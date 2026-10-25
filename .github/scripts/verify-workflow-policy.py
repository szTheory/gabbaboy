#!/usr/bin/env python3
"""Judge the privilege and trust wiring of the release workflows.

This is deliberately not a general YAML or shell parser. It reads the one block
shape these workflows use (mappings, sequences, literal and folded block scalars,
simple flow lists), refuses everything else (anchors, aliases, tags, tabs, flow
maps, duplicate keys, multi-line plain scalars) and then classifies every job by
role: unprivileged producer, trusted reader, minimal attacher, or a named
residual. Residual jobs still keep write authority (an owner decision) but are not
exempt from credential checks: every checkout is non-persisted, jobs that run tagged
code hold the token only on gh steps and overlay the trusted verifiers, and the
job-level token exemption is the named TOKEN_SCOPE_EXEMPT data with its reasons. Roles are enforced from jobs, permissions, needs, checkout inputs and
artifact steps, never from substrings of the file.

The judge never imports or executes anything from the tree it judges. Run it from
a trusted checkout and pass the subject tree as --root (data only).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path


class Reject(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"REJECT {code}: {message}")


# --------------------------------------------------------------------------- reader
_KEY = re.compile(r"""^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:\s+(.*))?$""")
_BLOCK = {"|", "|-", "|+", ">", ">-", ">+"}


def _unsupported(name: str, what: str) -> Reject:
    return Reject("workflow-unsupported-yaml", f"{name}: {what}")


def _scalar(raw: str, name: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "&*!@`%{" or value.startswith("<<"):
        raise _unsupported(name, f"unsupported value {value[:30]!r}")
    if value[0] in "'\"":
        end = value.find(value[0], 1)
        if end < 0 or value[end + 1 :].strip() not in ("",) and not value[end + 1 :].strip().startswith("#"):
            raise _unsupported(name, f"unsupported quoted value {value[:30]!r}")
        return value[1:end]
    cut = value.find(" #")
    return value[:cut].rstrip() if cut >= 0 else value


def _flow_list(raw: str, name: str) -> list[str]:
    inner = raw.strip()[1:-1]
    if any(ch in inner for ch in "[]{}"):
        raise _unsupported(name, f"unsupported flow list {raw[:40]!r}")
    return [_scalar(part, name) for part in inner.split(",") if part.strip()]


class _Reader:
    def __init__(self, text: str, name: str) -> None:
        if "\t" in text or "\r" in text:
            raise _unsupported(name, "tabs and carriage returns are unsupported")
        self.name = name
        self.lines = text.split("\n")
        self.i = 0

    def peek(self) -> tuple[int, str] | None:
        while self.i < len(self.lines):
            line = self.lines[self.i]
            body = line.strip()
            if not body or body.startswith("#"):
                self.i += 1
                continue
            return len(line) - len(line.lstrip(" ")), body
        return None

    def block_scalar(self, indent: int) -> str:
        collected: list[str] = []
        block_indent = None
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.strip():
                width = len(line) - len(line.lstrip(" "))
                if width <= indent:
                    break
                block_indent = width if block_indent is None else min(block_indent, width)
            collected.append(line)
            self.i += 1
        width = block_indent or 0
        return "\n".join(line[width:] if line.strip() else "" for line in collected).rstrip("\n")

    def mapping(self, indent: int) -> dict:
        result: dict = {}
        while True:
            head = self.peek()
            if head is None or head[0] < indent:
                return result
            if head[0] > indent:
                raise _unsupported(self.name, f"unexpected indentation near {head[1][:50]!r}")
            body = head[1]
            if body.startswith("- "):
                raise _unsupported(self.name, f"unexpected sequence item near {body[:50]!r}")
            match = _KEY.match(body)
            if not match:
                raise _unsupported(self.name, f"unsupported mapping row {body[:50]!r}")
            key, raw = match.group(1), match.group(2) or ""
            if key in result:
                raise Reject("workflow-duplicate-key", f"{self.name}: duplicate key {key}")
            self.i += 1
            stripped = raw.strip()
            if stripped in _BLOCK:
                result[key] = self.block_scalar(indent)
            elif stripped.startswith("["):
                if not stripped.endswith("]"):
                    raise _unsupported(self.name, f"unterminated flow list for {key}")
                result[key] = _flow_list(stripped, self.name)
            elif stripped == "" or stripped.startswith("#"):
                nxt = self.peek()
                if nxt is not None and (nxt[0] > indent or (nxt[0] == indent and nxt[1].startswith("- "))):
                    result[key] = self.sequence(nxt[0]) if nxt[1].startswith("- ") else self.mapping(nxt[0])
                else:
                    result[key] = ""
            else:
                result[key] = _scalar(raw, self.name)

    def sequence(self, indent: int) -> list:
        result: list = []
        while True:
            head = self.peek()
            if head is None or head[0] != indent or not head[1].startswith("- "):
                if head is not None and head[0] > indent:
                    raise _unsupported(self.name, f"unexpected indentation near {head[1][:50]!r}")
                return result
            rest = head[1][2:]
            if _KEY.match(rest):
                self.lines[self.i] = " " * (indent + 2) + rest
                result.append(self.mapping(indent + 2))
            else:
                if rest.strip()[:1] in "[{":
                    raise _unsupported(self.name, "nested flow collections are unsupported")
                result.append(_scalar(rest, self.name))
                self.i += 1


def read_workflow(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject("workflow-unavailable", f"cannot read {path.name}: {exc.strerror}") from exc
    reader = _Reader(text, path.name)
    tree = reader.mapping(0)
    if reader.peek() is not None:
        raise _unsupported(path.name, "content after the root mapping")
    jobs = tree.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        raise _unsupported(path.name, "missing jobs mapping")
    for job_id, job in jobs.items():
        if not isinstance(job, dict):
            raise _unsupported(path.name, f"job {job_id} is not a mapping")
        steps = job.get("steps", [])
        if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
            raise _unsupported(path.name, f"job {job_id} steps are not a list of mappings")
    return tree


# --------------------------------------------------------------------------- helpers
def _needs(job: dict) -> set[str]:
    needs = job.get("needs", [])
    return set(needs) if isinstance(needs, list) else ({needs} if needs else set())


def _permissions(job: dict, top: dict) -> dict[str, str]:
    """GitHub grants only what a job lists once it lists any; an omitted block inherits the top level."""
    declared = job["permissions"] if "permissions" in job else top.get("permissions", {})
    if isinstance(declared, str):
        # read-all/write-all or an empty block: treat the broad forms as writable, fail closed.
        return {"*": "write"} if declared == "write-all" else ({"*": "read"} if declared == "read-all" else {})
    return dict(declared)


def _writes(perms: dict[str, str]) -> bool:
    return any(value == "write" for value in perms.values())


def _checkouts(job: dict) -> list[dict]:
    return [step for step in job.get("steps", []) if str(step.get("uses", "")).startswith("actions/checkout@")]


def _artifact_steps(job: dict, kind: str) -> list[dict]:
    return [step for step in job.get("steps", []) if str(step.get("uses", "")).startswith(f"actions/{kind}-artifact@")]


_TOKEN = re.compile(r"github\.token|secrets\.|GH_TOKEN|GITHUB_TOKEN")
_WRITE_COMMAND = re.compile(r"(?m)(?:^|[\s;&|(])(?:gh\s+(?:release|api|pr|issue|run|workflow)|git\s+(?:push|remote|credential))\b")


def _strings(value) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    return [str(value)]


def _where(workflow: str, job_id: str) -> str:
    return f"{workflow}.{job_id}"


def _check_actions(workflow: str, tree: dict) -> None:
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            uses = str(step.get("uses", ""))
            if uses and not uses.startswith("./") and not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", uses):
                raise Reject("workflow-unpinned-action", f"{_where(workflow, job_id)} uses an action not pinned to a full commit: {uses}")
        if "uses" in job and not str(job["uses"]).startswith("./"):
            raise Reject("workflow-unpinned-action", f"{_where(workflow, job_id)} calls an unpinned reusable workflow")


# A run body is shell text; an expression spliced into it bypasses shell quoting (IN-07). These three are
# workflow-controlled, fixed-shape values and the only ones a run body may interpolate; every step output,
# input or event field has to arrive through step-level env instead.
RUN_EXPRESSION_ALLOWED = ("github.run_id", "github.run_attempt", "github.sha")
_EXPRESSION = re.compile(r"\$\{\{(.*?)\}\}", re.S)


def _check_run_expressions(workflow: str, tree: dict) -> None:
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            for expression in _EXPRESSION.findall(str(step.get("run", ""))):
                if expression.strip() not in RUN_EXPRESSION_ALLOWED:
                    raise Reject("run-expression", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} interpolates "
                                 f"${{{{ {expression.strip()} }}}} into a run body; pass it through step-level env")


def _substitutions(text: str) -> list[str]:
    """Bodies of the `$(...)` command substitutions in one shell word (arithmetic `$((...))` holds no command)."""
    bodies, i = [], 0
    while True:
        i = text.find("$(", i)
        if i < 0:
            return bodies
        if text.startswith("$((", i):
            i += 3
            continue
        k = _match(text, i + 1, "(", ")")
        bodies.append(text[i + 2 : k])
        i = k + 1


def _commands(script: str) -> list[list[str]]:
    """Every command the script runs, including those inside command substitutions, as word lists."""
    found = []
    for event in shell_events(script):
        found.append(event.words)
        for text in [*event.words, *event.assigns]:
            for body in _substitutions(text):
                found.extend(_commands(body))
    return found


def _head_operand(word: str) -> bool:
    return word == "HEAD" or word.startswith(("HEAD^", "HEAD~"))


def _check_fuzz_source_binding(workflow: str, tree: dict) -> None:
    """The fuzz reader's judge is the trusted checkout (HEAD) and its subject is the release commit. The subject is
    bound by the tag API check and the trusted hosted verifier; on a retry main has moved, so nothing may compare
    the subject with HEAD or ask for its ancestry against HEAD (WR-04)."""
    job = _require_job(workflow, tree, "candidate-fuzz")
    for step in job.get("steps", []):
        for words in _commands(str(step.get("run", ""))):
            if words[:2] == ["git", "rev-parse"] and any(_head_operand(word) for word in words[2:]):
                raise Reject("fuzz-source-binding", f"{_where(workflow, 'candidate-fuzz')} step {step.get('name', '?')!r} reads HEAD; "
                             "source identity comes from the tag API check and the trusted verifier, never the moving checkout")
            if words[:1] == ["git"] and ("merge-base" in words[1:3] or "--is-ancestor" in words[1:]):
                raise Reject("fuzz-source-binding", f"{_where(workflow, 'candidate-fuzz')} step {step.get('name', '?')!r} asserts ancestry "
                             "against the moving checkout; main membership is the API push-run record at the source SHA")


FUZZ_BUDGET_NAMES = ("CI_RUN_WAIT_ATTEMPTS", "CI_RUN_WAIT_SECONDS", "CI_RUN_WAIT_DEADLINE_SECONDS",
                     "CI_RUN_REQUEST_TIMEOUT_SECONDS", "HOSTED_POLL_SECONDS")
# Checkout with full history, run download, artifact upload, verifier startup and the verifier's final-iteration overshoot.
FUZZ_BUDGET_MARGIN_SECONDS = 900


def _budget_value(env: dict, name: str, where: str) -> int:
    """A positive integer literal; the workflow reader may hand scalars back as text."""
    value = env.get(name)
    if isinstance(value, bool) or not (isinstance(value, int) or (isinstance(value, str) and re.fullmatch(r"[0-9]+", value))) or int(value) <= 0:
        raise Reject("fuzz-wait-budget", f"{where} {name} must be a positive integer literal")
    return int(value)


def _check_fuzz_wait_budget(workflow: str, tree: dict) -> None:
    """The CI-run poll ends by an elapsed-time deadline plus one bounded request, and the whole job fits its timeout."""
    job = _require_job(workflow, tree, "candidate-fuzz")
    where = _where(workflow, "candidate-fuzz")
    env = job.get("env", {}) if isinstance(job.get("env"), dict) else {}
    attempts, interval, deadline, request, hosted = (_budget_value(env, name, where) for name in FUZZ_BUDGET_NAMES)
    minutes = _budget_value(job, "timeout-minutes", where)
    if deadline < attempts * interval:
        raise Reject("fuzz-wait-budget", f"{where} deadline {deadline}s is below attempts x interval {attempts * interval}s, which would silently shorten the poll")
    worst = deadline + request + interval + hosted + FUZZ_BUDGET_MARGIN_SECONDS
    if worst > minutes * 60:
        raise Reject("fuzz-wait-budget", f"{where} worst case {worst}s exceeds timeout-minutes {minutes} ({minutes * 60}s)")
    guarded = lookups = 0
    for step in job.get("steps", []):
        script = str(step.get("run", ""))
        events = shell_events(script)
        for at, event in enumerate(events):
            if (event.words[:1] in (["[["], ["["], ["test"]) and "-ge" in event.words
                    and any(re.search(r"\$\(\(.*\bSECONDS\b", word) for word in event.words)
                    and any(word in ("$CI_RUN_WAIT_DEADLINE_SECONDS", "${CI_RUN_WAIT_DEADLINE_SECONDS}") for word in event.words)
                    and any(frame[0] == "loop" for frame in event.frames)
                    and at + 1 < len(events) and events[at + 1].words == ["break"]):
                guarded += 1
        for words in _commands(script):
            for position in range(len(words) - 1):
                if words[position : position + 2] == ["gh", "api"] and any("actions/workflows/ci.yml/runs" in word for word in words):
                    lookups += 1
                    if not (position == 2 and words[0] == "timeout"
                            and words[1] in ("$CI_RUN_REQUEST_TIMEOUT_SECONDS", "${CI_RUN_REQUEST_TIMEOUT_SECONDS}")):
                        raise Reject("fuzz-wait-budget", f"{where} runs-lookup gh api call must run under timeout $CI_RUN_REQUEST_TIMEOUT_SECONDS")
    if not guarded:
        raise Reject("fuzz-wait-budget", f"{where} poll loop must break when elapsed SECONDS reaches CI_RUN_WAIT_DEADLINE_SECONDS")
    if not lookups:
        raise Reject("fuzz-wait-budget", f"{where} has no ci.yml runs lookup for the budget to bound")


def _check_checkout_credentials(workflow: str, tree: dict, job_ids) -> None:
    for job_id in job_ids:
        for step in _checkouts(tree["jobs"][job_id]):
            if str(step.get("with", {}).get("persist-credentials", "")).lower() != "false":
                raise Reject("checkout-credentials", f"{_where(workflow, job_id)} checkout must set persist-credentials: false")


def _upload(job: dict, workflow: str, job_id: str, name: str, must_contain: tuple[str, ...], retain_on_failure: bool = False) -> None:
    uploads = _artifact_steps(job, "upload")
    matching = [step for step in uploads if step.get("with", {}).get("name") == name]
    if len(matching) != 1:
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} must retain exactly one artifact named {name}")
    inputs = matching[0]["with"]
    if inputs.get("if-no-files-found") != "error" or any(item not in str(inputs.get("path", "")) for item in must_contain):
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} artifact {name} must fail on a missing file and carry {must_contain}")
    allowed = ("", "${{ success() }}") + (("always()", "${{ always() }}") if retain_on_failure else ())
    if str(matching[0].get("if", "")).strip() not in allowed:
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} artifact upload must not be conditional")


def _download(job: dict, workflow: str, job_id: str, name: str) -> None:
    if not any(step.get("with", {}).get("name") == name for step in _artifact_steps(job, "download")):
        raise Reject("artifact-flow", f"{_where(workflow, job_id)} must download retained artifact {name}")


def _check_unprivileged(workflow: str, tree: dict, job_id: str) -> None:
    """A producer runs subject code with a read-only job token and no token it could use or leak."""
    job = tree["jobs"][job_id]
    perms = _permissions(job, tree.get("permissions", {}))
    if _writes(perms):
        raise Reject("producer-write-authority", f"{_where(workflow, job_id)} runs producer work with write authority")
    if "permissions" in job and perms != {"contents": "read"}:
        raise Reject("producer-permissions", f"{_where(workflow, job_id)} must hold only contents: read")
    if any(_TOKEN.search(text) for text in _strings({k: v for k, v in job.items() if k != "name"})):
        raise Reject("producer-token", f"{_where(workflow, job_id)} references the job token or a secret")
    if any(_WRITE_COMMAND.search(step.get("run", "")) for step in job.get("steps", [])):
        raise Reject("producer-write-command", f"{_where(workflow, job_id)} runs a repository-write or API command")


def _check_trusted_checkout(workflow: str, job_id: str, job: dict, expected_ref: str, expected_path: str,
                            optional: bool = False) -> None:
    """A judge, reader or attacher checks out only the trusted workflow revision, never the subject ref."""
    steps = _checkouts(job)
    if optional and not steps:
        return
    if len(steps) != 1:
        raise Reject("judge-trust", f"{_where(workflow, job_id)} needs exactly one trusted checkout")
    inputs = steps[0].get("with", {})
    if inputs.get("ref") != expected_ref or inputs.get("path") != expected_path:
        raise Reject("judge-trust", f"{_where(workflow, job_id)} trusted checkout must be ref {expected_ref} at path {expected_path}")


def _require_needs(workflow: str, job_id: str, job: dict, needed: set[str], code: str) -> None:
    missing = needed - _needs(job)
    if missing:
        raise Reject(code, f"{_where(workflow, job_id)} must depend on {sorted(missing)}")


def _require_job(workflow: str, tree: dict, job_id: str) -> dict:
    job = tree["jobs"].get(job_id)
    if job is None:
        raise Reject("workflow-job-missing", f"{workflow} is missing job {job_id}")
    return job



# --------------------------------------------------------------------------- shell intent
# A bounded reader for the plain bash these workflows use. It recovers commands, their enclosing
# if/loop/function/group frames, list connectors and `|| ...` guards so that a required command can be
# proved reachable and fatal. Anything it cannot place (case, background jobs, unterminated quotes) is
# rejected as ambiguous rather than guessed.
_WORD_END = set(" \t\n;&|()<>")
_REDIRECTS = {">", ">>", "<", "<<", "<<-", "<<<", ">&", "<&", "&>"}


def _ambiguous(what: str) -> Reject:
    return Reject("shell-unsupported", what)


def _match(text: str, start: int, opener: str, closer: str) -> int:
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c in "'\"":
            end = text.find(c, i + 1)
            if end < 0:
                raise _ambiguous("unterminated quote")
            i = end
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise _ambiguous(f"unterminated {opener}{closer}")


def _tokens(script: str, *, extended: bool = False, heredoc_log: list | None = None) -> list[tuple[str, str]]:
    """Shell words and operators. `extended` is used only by the token-step judge: it also reads `(( ))` commands and
    `name=( ... )` arrays as single words and logs every heredoc as (delimiter, quoted, body) in `heredoc_log`."""
    out: list[tuple[str, str]] = []
    heredocs: list[tuple[str, bool, bool]] = []
    i, n = 0, len(script)
    while i < n:
        c = script[i]
        if c == "\\" and script[i + 1 : i + 2] == "\n":
            i += 2
        elif c in " \t":
            i += 1
        elif c == "\n":
            out.append(("op", "\n"))
            i += 1
            for delimiter, strip, quoted in heredocs:
                body: list[str] = []
                while i < n:
                    end = script.find("\n", i)
                    line = script[i : end if end >= 0 else n]
                    i = end + 1 if end >= 0 else n
                    if (line.strip() if strip else line) == delimiter:
                        break
                    body.append(line)
                if heredoc_log is not None:
                    heredoc_log.append((delimiter, quoted, "\n".join(body)))
            heredocs = []
        elif c == "#":
            while i < n and script[i] != "\n":
                i += 1
        elif extended and script.startswith("((", i):
            k = _match(script, i, "(", ")")
            if script[k - 1] != ")":
                raise _ambiguous("unreadable (( )) command")
            out.append(("w", script[i : k + 1]))
            i = k + 1
        elif c in ";&|<>()":
            op = next((cand for cand in ("<<<", "<<-", "&&", "||", ";;", ">>", "<<", ">&", "<&", "&>") if script.startswith(cand, i)), c)
            out.append(("op", op))
            i += len(op)
            if op in ("<<", "<<-"):
                j = i
                while j < n and script[j] in " \t":
                    j += 1
                k = j
                while k < n and script[k] not in " \t\n;&|()<>":
                    k += 1
                raw = script[j:k]
                heredocs.append((raw.strip("'\""), op == "<<-", any(ch in raw for ch in "'\"\\")))
        else:
            parts: list[str] = []
            while i < n:
                c = script[i]
                if c == "'":
                    end = script.find("'", i + 1)
                    if end < 0:
                        raise _ambiguous("unterminated quote")
                    parts.append(script[i + 1 : end])
                    i = end + 1
                elif c == '"':
                    j = i + 1
                    while j < n and script[j] != '"':
                        if script[j] == "\\" and j + 1 < n:
                            parts.append(script[j + 1] if script[j + 1] in '"\\$`' else script[j : j + 2])
                            j += 2
                        elif script[j] == "$" and script[j + 1 : j + 2] in ("(", "{"):
                            opener, closer = ("(", ")") if script[j + 1] == "(" else ("{", "}")
                            k = _match(script, j + 1, opener, closer)
                            parts.append(script[j : k + 1])
                            j = k + 1
                        else:
                            parts.append(script[j])
                            j += 1
                    if j >= n:
                        raise _ambiguous("unterminated quote")
                    i = j + 1
                elif c == "\\" and i + 1 < n:
                    parts.append(script[i + 1])
                    i += 2
                elif c == "$" and script[i + 1 : i + 2] in ("(", "{"):
                    opener, closer = ("(", ")") if script[i + 1] == "(" else ("{", "}")
                    k = _match(script, i + 1, opener, closer)
                    parts.append(script[i : k + 1])
                    i = k + 1
                elif c == "`":
                    end = script.find("`", i + 1)
                    if end < 0:
                        raise _ambiguous("unterminated backtick")
                    parts.append(script[i : end + 1])
                    i = end + 1
                elif extended and c == "(" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\+?=", "".join(parts)):
                    k = _match(script, i, "(", ")")
                    parts.append(script[i : k + 1])
                    i = k + 1
                elif c in _WORD_END:
                    break
                else:
                    parts.append(c)
                    i += 1
            word = "".join(parts)
            if word.isdigit() and i < n and script[i] in "<>":
                continue  # file-descriptor prefix of a redirection
            out.append(("w", word))
    return out


class Event:
    __slots__ = ("words", "assigns", "frames", "connector", "guard", "index", "line_end")

    def __init__(self, words, assigns, frames, connector, index):
        self.words, self.assigns, self.frames, self.connector, self.index = words, assigns, frames, connector, index
        self.guard: list[list[str]] = []  # commands on the right of `||` that decide what a failure does


def _const(words: list[str]):
    """True/False for a literal condition, None when it depends on runtime state."""
    if words in (["true"], [":"]):
        return True
    if words == ["false"]:
        return False
    body = words
    if body and body[0] in ("[[", "[", "test"):
        body = body[1:-1] if body[0] in ("[[", "[") else body[1:]
        if len(body) == 3 and not any("$" in w or "`" in w for w in body):
            left, op, right = body
            if op in ("==", "=", "-eq"):
                return left == right
            if op in ("!=", "-ne"):
                return left != right
    return None


def shell_events(script: str, *, extended: bool = False) -> list[Event]:
    tokens = _tokens(script, extended=extended)
    events: list[Event] = []
    frames: list[dict] = []
    state = {"cur": [], "connector": None, "last": None, "or_owner": None, "or_depth": 0, "func": None, "skip": False,
             "force_conn": None}

    def snapshot():
        return tuple((f["kind"], f["phase"], f["dead"], f.get("name", "")) for f in frames)

    def emit(words: list[str], connector):
        assigns = []
        while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\+?=.*" if extended else r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0], re.S if extended else 0):
            assigns.append(words.pop(0))
        if not words and not assigns:
            return
        if connector is None and state["force_conn"]:
            connector, state["force_conn"] = state["force_conn"], None
        event = Event(list(words), assigns, snapshot(), connector, len(events))
        events.append(event)
        state["last"] = event
        if connector == "||" and state["or_owner"] is None and state["prev"] is not None:
            state["or_owner"], state["or_depth"] = state["prev"], len(frames)
        if state["or_owner"] is not None and event is not state["or_owner"] and words:
            state["or_owner"].guard.append(list(words))
        if frames and frames[-1]["kind"] in ("if", "loop") and frames[-1]["phase"] in ("cond", "header") and words:
            frames[-1].setdefault("cond", []).append(list(words))

    state["prev"] = None

    def command(words: list[str], connector):
        if not words:
            return
        head = words[0]
        if head in ("case", "function", "select", "coproc"):
            raise _ambiguous(f"unsupported shell construct {head}")
        if head == "if":
            frames.append({"kind": "if", "phase": "cond", "dead": False, "const": None})
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "elif":
            frames[-1].update(phase="cond", dead=False, const=None, cond=[])
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "then":
            frame = frames[-1]
            conds = frame.get("cond", [])
            frame["const"] = _const(conds[0]) if len(conds) == 1 else None
            frame.update(phase="then", dead=frame["const"] is False)
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "else":
            frame = frames[-1]
            frame.update(phase="else", dead=frame["const"] is True)
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "fi":
            frames.pop()
            return
        if head in ("for", "while", "until"):
            frames.append({"kind": "loop", "phase": "header", "dead": False})
            if head != "for" and len(words) > 1:
                emit(list(words[1:]), connector)
            return
        if head == "do":
            frames[-1]["phase"] = "body"
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "done":
            frames.pop()
            return
        if head == "{":
            name = state["func"]
            frames.append({"kind": "func" if name else "group", "phase": "body", "dead": False, "name": name or ""})
            state["func"] = None
            if len(words) == 1 and connector == "||":
                state["force_conn"] = connector
            return command(words[1:], connector) if len(words) > 1 else None
        if head == "}":
            frames.pop()
            return
        emit(list(words), connector)

    def flush(next_connector):
        words, connector = state["cur"], state["connector"]
        state["cur"] = []
        command(words, connector)
        state["prev"] = state["last"]
        state["connector"] = next_connector

    i = 0
    while i < len(tokens):
        kind, value = tokens[i]
        if state["skip"]:
            state["skip"] = False
            i += 1
            continue
        if kind == "w":
            state["cur"].append(value)
        elif value in _REDIRECTS:
            state["skip"] = True
        elif value == "(":
            if len(state["cur"]) == 1 and tokens[i + 1 : i + 2] == [("op", ")")]:
                state["func"] = state["cur"][0]
                state["cur"] = []
                i += 1
            else:
                raise _ambiguous("subshells are unsupported")
        elif value in ("&&", "||", "|"):
            flush(value)
        elif value in ("\n", ";"):
            flush(None)
            state["last"] = None if value == "\n" or True else state["last"]
            state["prev"] = None
            if state["or_owner"] is not None and len(frames) <= state["or_depth"]:
                state["or_owner"] = None
        elif value in ("&", ";;", ")", "&>"):
            raise _ambiguous(f"unsupported shell operator {value}")
        i += 1
    flush(None)
    if frames:
        raise _ambiguous("unterminated shell block")
    return events


_ERREXIT_OFF = re.compile(r"^\+[a-zA-Z]*e[a-zA-Z]*$")


def _ignores_failure(event: Event) -> bool:
    if not event.guard:
        return False
    return not any(words[0] in ("exit", "return") and len(words) > 1 and words[1] != "0" for words in event.guard) \
        and not any(words == ["false"] for words in event.guard)


def _reachable(event: Event, events: list[Event], conditional: bool, errexit_off: bool, _seen=()) -> bool:
    for kind, phase, dead, name in event.frames:
        if dead:
            return False
        if kind == "func":
            if name in _seen or not any(
                other.words and other.words[0] == name and other is not event
                and _reachable(other, events, conditional, errexit_off, _seen + (name,)) for other in events
            ):
                return False
        elif kind in ("if", "loop"):
            if not conditional or phase in ("cond", "header"):
                return False
        elif kind == "group" and not conditional:
            return False
    if event.connector in ("&&", "||") or _ignores_failure(event):
        return False
    for earlier in events[: event.index]:
        if earlier.frames or earlier.connector:
            continue
        if earlier.words[:1] in (["exit"], ["return"]):
            return False
        if not errexit_off and earlier.words[:1] == ["set"] and any(_ERREXIT_OFF.match(w) or w == "+o" for w in earlier.words[1:]):
            return False
    return True


def expected_command(text: str) -> tuple[list[str], list[str]]:
    events = shell_events(text)
    return events[0].words, events[0].assigns


def _const_false(expression) -> bool:
    text = re.sub(r"^\$\{\{|\}\}$", "", str(expression).strip()).strip()
    return text in ("false", "0", "''", '""', "null") or bool(re.match(r"^false\s*&&", text))


def _check_disabled(workflow: str, tree: dict) -> None:
    for job_id, job in tree["jobs"].items():
        if _const_false(job["if"]) if "if" in job else False:
            raise Reject("disabled-gate", f"{_where(workflow, job_id)} is disabled by a constant-false condition")
        for step in job.get("steps", []):
            if "if" in step and _const_false(step["if"]):
                raise Reject("disabled-gate", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} is disabled by a constant-false condition")


_DOWNLOAD_TOOLS = {"curl", "wget"}


def _check_bounded_downloads(workflow: str, tree: dict) -> None:
    """Artifact downloads go through the bounded streaming helper; a bare curl or wget has no time or byte contract."""
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            for event in _step_events(step):
                if event.words and event.words[0].rsplit("/", 1)[-1] in _DOWNLOAD_TOOLS:
                    raise Reject("unbounded-download", f"{_where(workflow, job_id)} downloads with {event.words[0]!r}; use download-release-artifact.py")


def _runs_under_errexit(step: dict) -> bool:
    shell = str(step.get("shell", "bash")).strip()
    return shell in ("bash", "bash -e {0}", "bash --noprofile --norc -eo pipefail {0}") and str(step.get("continue-on-error", "false")).lower() in ("", "false")


def _step_events(step: dict) -> list[Event]:
    try:
        return shell_events(step.get("run", ""))
    except Reject:
        return []


def require_call(workflow: str, job_id: str, job: dict, command_text: str, *, conditional: bool = False,
                 errexit_off: bool = False, status_var: str = "", after_step: int = 0, allow_always: bool = False,
                 contains: tuple[str, ...] = ()) -> tuple[int, int]:
    """Prove the job runs `command_text` as a reachable, fatal statement; return its (step, statement) position."""
    words, assigns = expected_command(command_text)
    for number, step in enumerate(job.get("steps", [])):
        always = allow_always and str(step.get("if", "")).strip() in ("always()", "${{ always() }}")
        if number < after_step or ("if" in step and not always) or not _runs_under_errexit(step) or not step.get("run"):
            continue
        events = _step_events(step)
        for event in events:
            if event.words[: len(words)] != words or not set(assigns) <= set(event.assigns):
                continue
            if not set(contains) <= set(event.words):
                continue
            if not _reachable(event, events, conditional, errexit_off):
                continue
            if status_var:
                following = events[event.index + 1] if event.index + 1 < len(events) else None
                if not (following and not following.words and f"{status_var}=$?" in following.assigns):
                    continue
                if not any(e.words[:3] == ["test", f"${status_var}", "-eq"] and e.words[3:4] == ["0"]
                           and _reachable(e, events, False, True) for e in events[event.index + 1 :]):
                    continue
            return number, event.index
    raise Reject("required-command-not-executed", f"{_where(workflow, job_id)} does not run a reachable, fatal: {command_text}")


def _check_ignored_failures(workflow: str, tree: dict) -> None:
    for job_id, job in tree["jobs"].items():
        if str(job.get("continue-on-error", "false")).lower() not in ("", "false"):
            raise Reject("ignored-gate", f"{_where(workflow, job_id)} ignores job failure with continue-on-error")
        for number, step in enumerate(job.get("steps", [])):
            if str(step.get("continue-on-error", "false")).lower() in ("", "false"):
                continue
            step_id = step.get("id", "")
            gate_vars = [key for later in job["steps"][number + 1 :] for key, value in later.get("env", {}).items()
                         if step_id and value == "${{ steps." + step_id + ".outcome }}"]
            gated = False
            for var in gate_vars:
                try:
                    require_call(workflow, job_id, job, f'test "${var}" = success', after_step=number + 1, allow_always=True)
                    gated = True
                except Reject:
                    continue
            if not gated:
                raise Reject("ignored-gate", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} continues on error without a fatal outcome gate")



_TRUSTED_OPERANDS = ("trusted/", "$RUNNER_TEMP/", "build/verify-release-gates.sh")
_BUILD_TOOLS = {"cmake", "ctest", "make", "ninja", "cc", "gcc", "clang"}


def _check_no_subject_execution(workflow: str, job_id: str, job: dict) -> None:
    """A write-holding judge runs interpreters only on trusted-checkout files, inline stdin, or files cut from
    the trusted workflow revision; never on a script or build tool from the tagged workspace."""
    for step in job.get("steps", []):
        for event in shell_events(step.get("run", "")):
            if not event.words:
                continue
            head = event.words[0]
            if head in _BUILD_TOOLS or head.startswith((".", "tests/", ".github/", "build/")):
                raise Reject("subject-judge-execution", f"{_where(workflow, job_id)} executes {head!r} from the tagged workspace under write authority")
            if head in ("bash", "sh", "python3", "python"):
                if any(word in ("-c", "-m") for word in event.words[1:]):
                    continue
                operands = [word for word in event.words[1:] if word == "-" or not word.startswith("-")]
                script = operands[0] if operands else "-"
                if script != "-" and not script.startswith(_TRUSTED_OPERANDS):
                    raise Reject("subject-judge-execution", f"{_where(workflow, job_id)} runs {script!r}, which is not trusted judge code")


# A run body that builds or runs code from the tagged workspace: a build tool as a command, or a tests/scripts path.
SUBJECT_EXECUTION = re.compile(r"(?m)(?:^|[\s;&|(])(?:cmake|ctest|make|ninja)\s|(?:^|[\s\"'=])(?:\./)?tests/scripts/")
_TOKEN_NAMES = ("GH_TOKEN", "GITHUB_TOKEN")


def _names_token(env) -> bool:
    return isinstance(env, dict) and any(key in _TOKEN_NAMES or _TOKEN.search(str(value)) for key, value in env.items())


def _check_token_scope(workflow: str, job_id: str, job: dict) -> None:
    """A job that runs tagged-tree code must not hold the write token job-wide; only gh steps may carry it."""
    if _names_token(job.get("env", {})):
        raise Reject("token-scope", f"{_where(workflow, job_id)} declares GH_TOKEN or GITHUB_TOKEN at job level; scope it to the gh steps")


def _check_token_subject_execution(workflow: str, job_id: str, job: dict, job_wide: bool = False) -> None:
    """No step that holds the token (its own env, or every step when the job holds it) builds or runs tagged code."""
    for step in job.get("steps", []):
        if (job_wide or _names_token(step.get("env", {}))) and SUBJECT_EXECUTION.search(step.get("run", "")):
            raise Reject("token-subject-execution", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} holds the token and runs build or tagged-script commands")


# Plain command words a tokened residual step may run. Enumerated from the real release.yml with the extended parser
# (heads of every step that holds the token in the five residual-role jobs, plus the heads nested in $(...) and
# backtick bodies). None of them runs a program named by its own operands: that rules out bash, sh, python*, node,
# the build tools, eval, exec, source, env, xargs, command, builtin, timeout, nohup, find and any word that holds a
# slash, a dollar sign or a backtick. `gh`, `jq` and `sed` can still execute code through their own features; that
# is the residual GR-WR-03(a)-R, not judged here.
TOKEN_STEP_COMMANDS = frozenset({
    "gh", "jq", "cmp", "echo", "printf", "set", "exit", "mkdir", "cp", "cat", "read", "basename", "base64", "head", "sed",
})
# Operands a tokened residual step may hand to bash or python3: the trusted workflow checkout, and the one
# verifier cut from the workflow revision into the build directory. The build/ entry is equality, not a prefix.
TOKEN_STEP_TRUSTED_OPERANDS = ("trusted/", "build/verify-release-gates.sh")


def _backticks(word: str) -> list[str]:
    """Bodies of the backtick substitutions in one shell word; an unpaired backtick cannot be judged."""
    parts = word.split("`")
    if len(parts) % 2 == 0:
        raise Reject("token-subject-execution", f"unpaired backtick in word {word!r}")
    return parts[1::2]


def _token_trusted_operand(word: str) -> bool:
    if ".." in word.split("/"):
        return False
    return word == TOKEN_STEP_TRUSTED_OPERANDS[1] or word.startswith(TOKEN_STEP_TRUSTED_OPERANDS[0])


def _token_command_allowed(words: list[str]) -> bool:
    head = words[0]
    if head in TOKEN_STEP_COMMANDS:
        return True
    if head == "git":
        return (len(words) == 3 and words[1] == "show" and words[2].startswith("${GITHUB_SHA}:")) or words[1:2] in (["rev-parse"], ["status"])
    if head == "bash":
        return len(words) > 1 and _token_trusted_operand(words[1])
    if head == "python3":
        at = 1
        while at < len(words) and words[at] == "-I":
            at += 1
        return at < len(words) and (words[at] == "-" or _token_trusted_operand(words[at]))
    return False


def _token_step_commands(script: str) -> list[list[str]]:
    """Every command the script runs, including those nested in $(...) and backtick bodies of any word, as word lists.
    Anything the reader cannot place is rejected (fail closed): the default reader's empty answer must not read as safe."""
    heredocs: list[tuple[str, bool, str]] = []
    try:
        events = shell_events(script, extended=True)
        tokens = _tokens(script, extended=True, heredoc_log=heredocs)
    except Reject as exc:
        raise Reject("token-subject-execution", f"a tokened step cannot be read, so it cannot be judged: {exc}") from None
    found: list[list[str]] = []
    in_conditional = False
    for event in events:
        words = event.words
        if not words:
            continue  # bare assignment
        if in_conditional or words[0] == "[[":
            # `[[ a && b ]]` arrives split at && and ||; the operands are not commands.
            in_conditional = words[-1] != "]]"
        elif not words[0].startswith("(("):
            found.append(words)
    if in_conditional:
        raise Reject("token-subject-execution", "a tokened step opens [[ without closing it")
    for delimiter, quoted, body in heredocs:
        if not quoted and ("$(" in body or "`" in body):
            raise Reject("token-subject-execution", f"unquoted heredoc {delimiter!r} expands a command substitution")
    for kind, word in tokens:
        if kind == "w":
            for body in [*_substitutions(word), *_backticks(word)]:
                found.extend(_token_step_commands(body))
    return found


# Defense in depth for the command-execution channel only. It judges which command heads a token-holding step runs,
# not what an allowlisted program does with its own features (script sources read from data, writes into trusted
# paths, environment hijack, gh alias or extension, arithmetic evaluation, sed e); those stay the owner-decided
# residual LIM-RESIDUAL-WRITE-JOBS, whose structural fix is removing the token from jobs that read the tagged tree.
def _check_token_step_commands(workflow: str, job_id: str, job: dict, job_wide: bool = False) -> None:
    for step in job.get("steps", []):
        if not ((job_wide or _names_token(step.get("env", {}))) and step.get("run")):
            continue
        where = f"{_where(workflow, job_id)} step {step.get('name', '?')!r} holds the token"
        try:
            commands = _token_step_commands(str(step["run"]))
        except Reject as exc:
            raise Reject("token-subject-execution", f"{where}: {exc}") from None
        for words in commands:
            if not _token_command_allowed(words):
                raise Reject("token-subject-execution", f"{where} and runs {words[0]!r}, which is not an allowed tokened-step command")


def _check_trusted_overlay(workflow: str, job_id: str, job: dict, paths: tuple[str, ...]) -> None:
    """Each tagged-tree verifier in `paths` is replaced by the workflow commit's copy in an earlier, unconditional,
    fatal step than the first step that invokes any of them. verify-release-candidate.sh runs the others, so
    calling it counts as first use of every path."""
    overlay_at = {}
    for path in paths:
        try:
            overlay_at[path] = require_call(workflow, job_id, job, f'git show "${{GITHUB_SHA}}:{path}"')[0]
        except Reject:
            raise Reject("trusted-verifier-overlay", f"{_where(workflow, job_id)} must overlay {path} from GITHUB_SHA in an unconditional step") from None
    last_overlay = max(overlay_at.values())
    names = {path: path.rsplit("/", 1)[-1] for path in paths}
    for number, step in enumerate(job.get("steps", [])):
        if number <= last_overlay:
            # A step the default reader cannot place would hide a verifier call from it (it returns no events), so
            # every step up to the last overlay is read with the extended reader and an unreadable one is refused.
            try:
                events = shell_events(str(step.get("run", "")), extended=True)
            except Reject as exc:
                raise Reject("trusted-verifier-overlay", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} cannot be read, "
                             f"so it cannot be shown to precede the trusted overlay: {exc}") from None
        else:
            events = _step_events(step)
        # The overlay step's own `git show` operand names the verifier without running it.
        used = {path for event in events if event.words[:2] != ["git", "show"] for word in event.words for path in paths
                if word in (path, "./" + path) or _overlay_basename(word) == names[path]}
        if "tests/scripts/verify-release-candidate.sh" in used:
            used = set(paths)
        late = sorted(path for path in used if overlay_at[path] >= number)
        if late:
            raise Reject("trusted-verifier-overlay", f"{_where(workflow, job_id)} step {step.get('name', '?')!r} runs {late[0]} before the trusted overlay")


def _overlay_basename(word: str) -> str:
    """The file name a path word ends in, without quotes or a leading variable such as $DIR or ${DIR}."""
    base = word.strip("'\"").rsplit("/", 1)[-1]
    return re.sub(r"^(?:\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*)+", "", base)


# --------------------------------------------------------------------------- policy
REHEARSAL_PRODUCERS = ("corpus", "fuzz", "performance", "perf-gate", "package", "aggregate")
REHEARSAL_FUZZ_ARTIFACT = "rehearsal-fuzz-${{ github.run_id }}-${{ github.run_attempt }}"
DEFAULT_BRANCH_REF = "${{ github.event.repository.default_branch }}"
TRUSTED_SHA_REF = "${{ github.sha }}"

RELEASE_ROLES = {
    "release": "release-please",
    "candidate": "residual",
    "candidate-macos": "residual",
    "candidate-windows": "residual",
    "candidate-platform-manifest": "residual",
    "publish-qualified-release": "residual",
    "candidate-corpus": "producer",
    "candidate-performance": "producer",
    "candidate-fuzz": "trusted-reader",
    "attach-v02-evidence": "attacher",
}
# Residual jobs that build or run tagged-tree code while holding contents: write. The overlay paths are the
# tagged-tree verifiers each one must replace with the workflow commit's copy before first use.
_VERIFIER_PAIR = ("tests/scripts/verify-release-candidate.sh", "tests/scripts/verify-v02-consumers.py")
TRUSTED_OVERLAYS = {
    "candidate": ("tests/scripts/verify-release-candidate.sh", "tests/scripts/verify-v02-source-archive.py",
                  "tests/scripts/verify-v02-consumers.py", "cmake/VerifyReleaseReceipt.cmake"),
    # verify-release-candidate.sh --extract reaches verify-v02-consumers.py, so both are overlaid before either runs.
    "candidate-macos": _VERIFIER_PAIR,
    "candidate-windows": _VERIFIER_PAIR,
}
# Residual jobs that run tagged-tree code: no job-wide token, the token only on gh steps.
RESIDUAL_SUBJECT_JOBS = ("candidate", "candidate-macos", "candidate-windows")
# Residual jobs that keep a job-level token, with the reason. They are not exempt from the step rule: with the
# token job-wide, none of their steps may build or run tagged code.
TOKEN_SCOPE_EXEMPT = {
    "candidate-platform-manifest": "runs only trusted judge code (_check_no_subject_execution and the trusted-checkout rule) "
                                   "and needs the token across its gh-only steps",
    "publish-qualified-release": "runs only trusted judge code (_check_no_subject_execution and the trusted-checkout rule) "
                                 "and needs the token across its gh-only release steps",
}
RELEASE_ARTIFACTS = {
    "candidate-corpus": ("release-evidence-corpus", ("build/cgb-corpus-receipt.json", "build/support-ledger.json")),
    "candidate-performance": ("release-evidence-performance", ("build/v02-performance-receipt.json",)),
    "candidate-fuzz": ("release-evidence-fuzz", ("build/ci-fuzz/v02-fuzz-receipt.json",)),
}
SUBJECT_REF = "${{ env.SOURCE_SHA }}"
JUDGE_CALL_POLICY = "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject"
PRODUCER_SCRIPT = ".github/scripts/produce-release-evidence.sh"
PRODUCER_SCRIPT_REQUIRED = (
    'same_commit "$head" "$source_sha"',
    'same_commit "$tagged" "$source_sha"',
    'git -C "$subject" tag -f "$tag" "$source_sha"',
    "cmake --preset phase1",
    "cmake --build --preset phase1",
    "cmake --install build --prefix build/package-prefix",
    'bash "$gate" --check-v02-evidence "$evidence" "$tag" "$source_sha" "$archive"',
)
_SHARED = "bash " + PRODUCER_SCRIPT
_REHEARSAL_TAG = _SHARED + ' verify-subject --subject . --source-sha "$GITHUB_SHA" --tag "$REHEARSAL_TAG" --local-tag'
_RELEASE_SUBJECT = _SHARED + ' verify-subject --subject . --source-sha "$SOURCE_SHA" --tag "$RELEASE_TAG"'
_CORPUS_BUILD = _SHARED + " corpus-build --subject ."
_LEDGER_BASE = 'python3 -I tests/scripts/verify-support-ledger.py --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --receipt build/cgb-corpus-receipt.json'
# The hosted cumulative performance gate (Phase 16, D-14..D-16): the gate itself and both seeded controls.
PERF_GATE_COMMANDS = (
    "bash tests/scripts/run-perf-gate.sh --gate",
    "bash tests/scripts/run-perf-gate.sh --seeded-regression",
    "bash tests/scripts/run-perf-gate.sh --noop-twin",
)
REHEARSAL_REQUIRED = {
    "perf-gate": PERF_GATE_COMMANDS,
    "corpus": (
        _REHEARSAL_TAG,
        _CORPUS_BUILD,
        "python3 -I tests/scripts/verify-cgb-corpus-report.py --begin-run --build-dir build --receipt build/cgb-corpus-receipt.json",
        "python3 -I tests/scripts/verify-cgb-corpus-report.py --from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json",
        "python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json",
        "python3 -I tests/scripts/verify-support-ledger.py --check-current --receipt build/cgb-corpus-receipt.json",
        "bash .github/scripts/verify-test-inventory.sh",
        _LEDGER_BASE + " --output build/support-ledger.json",
        _LEDGER_BASE + " --verify-sidecar build/support-ledger.json",
    ),
    "fuzz": (
        "GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --explore --receipt build-asan/v02-fuzz-receipt.json",
        "python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan/v02-fuzz-receipt.json",
        "GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --self-test",
    ),
    "performance": (
        "bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json",
        "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json",
    ),
    "package": (
        _REHEARSAL_TAG,
        'bash tests/scripts/verify-release-candidate.sh --extract build/gabbaboy-core-linux-x64.tar.gz "$RUNNER_TEMP/v02-extracted"',
        'python3 -I tests/scripts/verify-v02-consumers.py --write-candidate-manifest "$RUNNER_TEMP/candidate-manifest.json" --archive build/gabbaboy-core-linux-x64.tar.gz --source-sha "$SOURCE_SHA" --build-receipt build/release/CMakeCache.txt',
        'python3 -I tests/scripts/verify-v02-consumers.py --prefix "$RUNNER_TEMP/v02-extracted" --archive build/gabbaboy-core-linux-x64.tar.gz --candidate-manifest "$RUNNER_TEMP/candidate-manifest.json" --output build/v02-consumer-receipt.json',
        'python3 -I tests/scripts/verify-v02-source-archive.py --archive "$archive" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo . --output build/source-archive-receipt.json',
        'python3 -I tests/scripts/verify-v02-source-archive.py --check-receipt build/source-archive-receipt.json --archive "$archive" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo .',
    ),
    "aggregate": (
        _REHEARSAL_TAG,
        _CORPUS_BUILD,
        _SHARED + " collect --subject . --output build/evidence",
        _SHARED + ' verify --judge . --subject . --source-sha "$SOURCE_SHA" --tag "$RELEASE_TAG" --evidence build/evidence --archive "$RUNNER_TEMP/source-archive.tar.gz"',
        "python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json",
        "GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --explore --receipt build-asan/v02-fuzz-receipt.json",
        "python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan/v02-fuzz-receipt.json",
        "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json",
    ),
    "judge": (
        JUDGE_CALL_POLICY,
        "python3 -I trusted-judge/tests/scripts/verify-v02-fuzz.py --verify rehearsal-evidence/v02-fuzz-receipt.json",
    ),
}
_PUBLISH_INVENTORY = 'python3 -I trusted/.github/scripts/verify-published-release-assets.py --inventory "$RUNNER_TEMP/expected-inventory.json" build/release-final'
_PUBLISH_RECOVERY = ('bash trusted/.github/scripts/verify-release-gates.sh --check-recovery "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA" '
                     '"$RUNNER_TEMP/expected-inventory.json" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" full')
_ATTACH_INVENTORY = ('python3 -I trusted/.github/scripts/verify-published-release-assets.py --inventory "$RUNNER_TEMP/expected-inventory.json" '
                     'build/evidence-corpus/support-ledger.json build/evidence-corpus/cgb-corpus-receipt.json '
                     'build/evidence-fuzz/v02-fuzz-receipt.json build/evidence-performance/v02-performance-receipt.json')
_ATTACH_RECOVERY = ('bash trusted/.github/scripts/verify-release-gates.sh --check-recovery "$release_id" "$RELEASE_TAG" "$SOURCE_SHA" '
                    '"$RUNNER_TEMP/expected-inventory.json" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" subset')
# The GitHub-generated source archive is streamed with a byte and time cap by the standard-library helper; the
# residual candidate job runs the copy cut from the workflow revision, the manifest job the trusted checkout.
_DOWNLOAD_BOUNDS = '--max-bytes 1073741824 --total-timeout 600'
_CANDIDATE_ARCHIVE_DOWNLOAD = ('python3 -I "$RUNNER_TEMP/download-release-artifact.py" "https://github.com/$GH_REPO/archive/refs/tags/$RELEASE_TAG.tar.gz" "$archive" '
                               + _DOWNLOAD_BOUNDS)
_MANIFEST_ARCHIVE_DOWNLOAD = ('python3 -I trusted/.github/scripts/download-release-artifact.py "https://github.com/$GH_REPO/archive/refs/tags/$RELEASE_TAG.tar.gz" '
                              '"$RUNNER_TEMP/source-archive.tar.gz" ' + _DOWNLOAD_BOUNDS)
RELEASE_REQUIRED = {
    "candidate-corpus": (_RELEASE_SUBJECT, _CORPUS_BUILD) + REHEARSAL_REQUIRED["corpus"][2:],
    "candidate-performance": (_RELEASE_SUBJECT,) + REHEARSAL_REQUIRED["performance"],
    "candidate-fuzz": (
        '[[ "$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq .sha)" == "$SOURCE_SHA" ]]',
        'gh run download "$run_id" --repo "$GH_REPO" --name "v02-fuzz-$run_id-$attempt" --dir build/ci-fuzz',
        'python3 -I tests/scripts/verify-v02-fuzz.py --verify-hosted --source-sha "$SOURCE_SHA" --run-id "$run_id" --attempt "$attempt" --receipt build/ci-fuzz/v02-fuzz-receipt.json --poll-seconds "$HOSTED_POLL_SECONDS"',
    ),
    "candidate-platform-manifest": (
        _MANIFEST_ARCHIVE_DOWNLOAD,
        'bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence build/evidence-validation "$RELEASE_TAG" "$SOURCE_SHA" "$RUNNER_TEMP/source-archive.tar.gz"',
    ),
    "publish-qualified-release": (
        'bash trusted/.github/scripts/verify-release-gates.sh --check-draft "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"',
        'bash trusted/.github/scripts/verify-release-gates.sh --check-merged-source "$SOURCE_SHA" "$RELEASE_TAG" "$RELEASE_ID" build/release-final/source-receipt.json "$RUNNER_TEMP/verify-release-source-proof.py"',
        'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"',
        "python3 -I trusted/.github/scripts/verify-published-release-assets.py",
        'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag',
        _PUBLISH_INVENTORY,
        _PUBLISH_RECOVERY,
    ),
    "attach-v02-evidence": (_ATTACH_INVENTORY, _ATTACH_RECOVERY),
    "candidate": (_CANDIDATE_ARCHIVE_DOWNLOAD,),
}
# Downloaded-byte platform smoke in the residual candidate jobs: (command prefix, words that must also appear).
RELEASE_SMOKE_REQUIRED = {
    "candidate": (
        ("bash tests/scripts/verify-release-candidate.sh --verify", ()),
        ("bash tests/scripts/verify-release-candidate.sh --verify-final", ()),
        ("cmake", ("-P", "cmake/VerifyInstalledPackage.cmake")),
    ),
    "candidate-macos": (
        ('bash "$RUNNER_TEMP/verify-release-gates.sh" --check-digest-sidecar build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz.sha256 build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz', ()),
        ("bash tests/scripts/verify-release-candidate.sh --extract build/downloaded-core/gabbaboy-core-macos-arm64.tar.gz build/extracted-core", ()),
        ("cmake", ("-P", "cmake/VerifyInstalledPackage.cmake")),
        ('GBB_VERIFIED_OUTPUT_DIR="$RUNNER_TEMP/release-player-downloaded" bash tests/scripts/verify-phase3-player.sh --verify-package build/downloaded-player', ()),
    ),
    "candidate-windows": (
        ("bash build/verify-release-gates.sh --check-digest-sidecar build/downloaded/gabbaboy-core-windows-x64.tar.gz.sha256 build/downloaded/gabbaboy-core-windows-x64.tar.gz", ()),
        ("bash tests/scripts/verify-release-candidate.sh --extract build/downloaded/gabbaboy-core-windows-x64.tar.gz build/extracted", ()),
        ("cmake", ("-P", "cmake/VerifyInstalledPackage.cmake")),
    ),
}
# Wiring facts of release.yml that no other table pins, judged from the parsed job: (kind, ...) items per job.
#   ("env", key)                   the job env defines key
#   ("if", fragment)               the job-level if: expression contains fragment
#   ("step-if", step name, frag)   the named step is guarded by an if: expression containing fragment
#   ("call", command, conditional) the job runs command as a reachable, fatal statement (conditional allows branches/loops)
#   ("step-lines", step name, lines) the unconditional, errexit step runs these consecutive non-comment script lines; used only
#                                  where the shell reader rejects the step (the candidate-selection steps use `(( ))`)
_REUSE_MACOS_GUARD = "env.REUSE_MACOS_CANDIDATE != 'true'"
_REUSE_WINDOWS_GUARD = "env.REUSE_WINDOWS_CANDIDATE != 'true'"
# The guard expressions that decide whether a release job or a reuse-sensitive step runs, pinned in normalised form
# (outer ${{ }} removed, whitespace collapsed) and compared for equality: a substring test accepts `|| true` or an
# `always() || ...` rewrite that keeps the old text as a fragment. Key: (job id,) or (job id, step name).
RELEASE_GUARD_EXPRESSIONS = {
    ("candidate",): "always() && ((inputs.retry == true) || (needs.release.result == 'success' && needs.release.outputs.release_created == 'true'))",
    ("candidate-macos",): "always() && needs.candidate.result == 'success' && ((inputs.retry == true) || (needs.release.result == 'success' && needs.release.outputs.release_created == 'true'))",
    ("candidate-windows",): "always() && needs.candidate-macos.result == 'success' && ((inputs.retry == true) || (needs.release.result == 'success' && needs.release.outputs.release_created == 'true'))",
    ("publish-qualified-release",): "always() && needs.candidate.result == 'success' && needs.candidate-macos.result == 'success' && needs.candidate-windows.result == 'success' && needs.candidate-platform-manifest.result == 'success' && ((inputs.retry == true) || (needs.release.result == 'success' && needs.release.outputs.release_created == 'true'))",
    ("candidate-macos", "Build and package macOS arm64 core once"): _REUSE_MACOS_GUARD,
    ("candidate-macos", "Build pinned SDL player and verify extracted package"): _REUSE_MACOS_GUARD,
    ("candidate-macos", "Attach macOS candidate bytes to the unpublished draft"): _REUSE_MACOS_GUARD,
    ("candidate-windows", "Build and package Windows x64 core once"): _REUSE_WINDOWS_GUARD,
    ("candidate-windows", "Attach Windows bytes to the unpublished draft"): _REUSE_WINDOWS_GUARD,
}


def _normalise_if(expression) -> str:
    text = str(expression).strip()
    wrapped = re.fullmatch(r"\$\{\{(.*)\}\}", text, re.S)
    return " ".join((wrapped.group(1) if wrapped else text).split())


RELEASE_PRESENCE = {
    "candidate": (
        ("if", "needs.release.outputs.release_created == 'true'"),
        ("env", "RETRY"),
        ("call", 'api_commit=$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq \'.sha\')', False),
        ("call", 'draft=$(jq --arg tag "$RELEASE_TAG" -r \'.[] | select(.tag_name == $tag) | .draft\' <<<"$release_json")', False),
        ("call", 'prs=$(gh api "repos/$GH_REPO/commits/$SOURCE_SHA/pulls")', False),
        ("call", 'required=$(gh pr checks "$pr_number" --required --json name,bucket)', False),
    ),
    "candidate-macos": (
        ("step-if", "Build and package macOS arm64 core once", _REUSE_MACOS_GUARD),
        ("step-if", "Build pinned SDL player and verify extracted package", _REUSE_MACOS_GUARD),
        ("step-if", "Attach macOS candidate bytes to the unpublished draft", _REUSE_MACOS_GUARD),
        ("step-lines", "Select a complete existing macOS candidate or a clean build",
         ('echo "Draft contains a partial macOS candidate asset set; refusing to rebuild or replace bytes." >&2', "exit 1")),
        ("call", 'gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern gabbaboy-preview-macos-arm64.tar.gz', False),
    ),
    "candidate-windows": (
        ("step-if", "Build and package Windows x64 core once", _REUSE_WINDOWS_GUARD),
        ("step-if", "Attach Windows bytes to the unpublished draft", _REUSE_WINDOWS_GUARD),
        ("step-lines", "Select an existing Windows archive or a clean build",
         ('echo "Draft contains a partial Windows candidate asset set; refusing to rebuild or replace bytes." >&2', "exit 1")),
        ("call", 'cmake -S "tests/consumers/$language" -B "build/consumer-work/$language" -G "Visual Studio 17 2022" -A x64', True),
    ),
    "candidate-platform-manifest": (
        ("call", 'gh release upload "$RELEASE_TAG" build/candidate-platform-manifest.json --repo "$GH_REPO"', True),
    ),
}
# Hosted runner images of the native downloaded-archive lanes; a silently different image changes what was qualified.
RELEASE_RUNNERS = {"candidate-macos": "macos-14", "candidate-windows": "windows-2022"}
# The only events that may start release.yml: it is a reusable workflow, so a privileged event of its own
# (pull_request_target, release, push) would run the draft-writing jobs outside the release-please entrypoint.
RELEASE_TRIGGERS = frozenset({"workflow_call"})
# The one caller of release.yml, so that release-please outputs and the candidate jobs run in a single workflow run.
RELEASE_ENTRYPOINT_WORKFLOW = "release-please.yml"
RELEASE_LOCAL_PATH = "./.github/workflows/release.yml"
CI_REQUIRED = (
    "cmake --preset phase1-asan -DGBB_TEST_INSTALL_PREFIX=",
    "cmake --build --preset phase1-asan",
    "GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --fast",
)
# The ASan inventory runs in two jobs apart from the fuzz campaign, which keeps its pinned 45-minute bound. Their
# exact filters are complementary, and each checks exactly its slice of the expected inventory (LESSONS GB-CI-010).
_ASAN_SHARD_BUILD = ("cmake --preset phase1-asan -DGBB_TEST_INSTALL_PREFIX=", "cmake --build --preset phase1-asan")
_ASAN_SHARD_INVENTORY = "bash .github/scripts/verify-test-inventory.sh build-asan/ctest.xml build-asan/expected-shard.txt"
CI_SANITIZER_SHARDS = {
    "linux-sanitizers-tests": _ASAN_SHARD_BUILD + (
        "ctest --preset phase1-asan --parallel 4 -E '^acceptance_' --output-on-failure --no-tests=error --output-junit ctest.xml",
        "grep -vE '^acceptance_' tests/expected-tests.txt > build-asan/expected-shard.txt",
        _ASAN_SHARD_INVENTORY),
    "linux-sanitizers-acceptance": _ASAN_SHARD_BUILD + (
        "ctest --preset phase1-asan --parallel 4 -R '^acceptance_' -E '^acceptance_stall_diagnosis(_replay_[12])?$' --output-on-failure --no-tests=error --output-junit ctest.xml",
        "grep -E '^acceptance_' tests/expected-tests.txt | grep -vE '^acceptance_stall_diagnosis(_replay_[12])?$' > build-asan/expected-shard.txt",
        _ASAN_SHARD_INVENTORY),
}
# (command, status variable, conditional by design): the sanitizer step runs under set +e so it can always retain
# evidence, then must assert every recorded status after errexit is restored.
CI_STATUS_CALLS = (
    ("GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --explore --receipt build-asan/v02-fuzz-receipt.json", "campaign_status", False),
    ("python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan/v02-fuzz-receipt.json", "verify_status", True),
    ("GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --self-test", "self_test_status", True),
)
# The per-test TIMEOUT ratchet (D-18): the native-linux job passes the PR base or push parent as --base so a change
# cannot judge its own allowlist against itself.
CI_BUDGET_COMMANDS = (
    'python3 -I tests/scripts/verify-test-budget.py --build-dir build --base "$BUDGET_BASE"',
)
# The budget base falls back to the merge base with origin/main when the push parent is all-zero or no longer a
# reachable commit (rebased and force-pushed branch), and still fails closed on an unresolvable final base.
CI_BUDGET_BASE_PINS = (
    '! git cat-file -e "${base}^{commit}"',
    'base=$(git merge-base HEAD origin/main)',
    'git cat-file -e "${base}^{commit}"\n',
)
CI_REQUIRED_NATIVE_NEEDS = {"native-linux", "native-macos", "native-windows", "linux-sanitizers", "linux-sanitizers-tests", "linux-sanitizers-acceptance", "cmake-floor-3-25-3", "perf-gate", "player-gate", "macos-player-package"}


_FORBIDDEN_PRODUCER_HEADS = {"gh", "curl", "wget", "ssh", "scp"}
_PRODUCER_GIT_WRITES = {"push", "remote", "credential", "config", "send-email"}


def check_producer_script(root: Path) -> None:
    """The shared producer runs under the same read-only authority as the jobs that call it: no token, no network
    publication, no remote or credential edits, fail-fast from its first statement."""
    path = root / PRODUCER_SCRIPT
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        raise Reject("producer-script-missing", f"{PRODUCER_SCRIPT} is missing") from None
    if _TOKEN.search(text):
        raise Reject("producer-token", f"{PRODUCER_SCRIPT} references a GitHub token or secret")
    events = shell_events(text)
    if not events or events[0].words != ["set", "-euo", "pipefail"]:
        raise Reject("producer-script-failfast", f"{PRODUCER_SCRIPT} must begin with set -euo pipefail")
    for event in events:
        words = event.words
        if words[:1] and (words[0] in _FORBIDDEN_PRODUCER_HEADS):
            raise Reject("producer-write-command", f"{PRODUCER_SCRIPT} runs {words[0]}, which can publish or change repository state")
        if words[:1] == ["git"]:
            subcommand = next((w for w in words[1:] if not w.startswith("-") and w != "-C" and not w.startswith(("$", '"'))), "")
            if any(w in _PRODUCER_GIT_WRITES for w in words[1:3]) or subcommand in _PRODUCER_GIT_WRITES:
                raise Reject("producer-write-command", f"{PRODUCER_SCRIPT} runs git {subcommand}, which can publish or change credentials")
    for command in PRODUCER_SCRIPT_REQUIRED:
        require_script_call(command, text)


def require_script_call(command_text: str, text: str) -> None:
    words, assigns = expected_command(command_text)
    events = shell_events(text)
    if not any(e.words[: len(words)] == words and set(assigns) <= set(e.assigns) and _reachable(e, events, True, False) for e in events):
        raise Reject("required-command-not-executed", f"{PRODUCER_SCRIPT} does not run a reachable, fatal: {command_text}")


def _check_no_duplicate_setup(workflow: str, tree: dict) -> None:
    """Rehearsal tag setup lives only in the shared producer; an inline copy would drift from it."""
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            for event in shell_events(step.get("run", "")):
                if event.words[:1] == ["git"] and "tag" in event.words[1:3]:
                    raise Reject("duplicate-rehearsal-setup", f"{_where(workflow, job_id)} sets up a tag inline; use {PRODUCER_SCRIPT} verify-subject")


def check_rehearsal(root: Path) -> None:
    name = "release-rehearsal"
    tree = read_workflow(root / ".github/workflows/release-rehearsal.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", f"{name} must declare only top-level contents: read")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_bounded_downloads(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    _check_no_duplicate_setup(name, tree)
    _check_checkout_credentials(name, tree, tree["jobs"])
    for job_id, job in tree["jobs"].items():
        if _writes(_permissions(job, tree["permissions"])):
            raise Reject("producer-write-authority", f"{_where(name, job_id)} holds write authority in a non-publishing rehearsal")
    for job_id in REHEARSAL_PRODUCERS:
        _require_job(name, tree, job_id)
        _check_unprivileged(name, tree, job_id)
    _upload(tree["jobs"]["fuzz"], name, "fuzz", REHEARSAL_FUZZ_ARTIFACT, ("build-asan/v02-fuzz-receipt.json",))

    judge = _require_job(name, tree, "judge")
    _require_needs(name, "judge", judge, set(REHEARSAL_PRODUCERS), "workflow-dependency")
    if "if" in judge:
        raise Reject("workflow-dependency", f"{_where(name, 'judge')} must run unconditionally after every producer")
    _check_unprivileged(name, tree, "judge")
    checkouts = {step.get("with", {}).get("path"): step.get("with", {}) for step in _checkouts(judge)}
    if set(checkouts) != {"trusted-judge", "subject"}:
        raise Reject("judge-trust", f"{_where(name, 'judge')} needs one trusted-judge checkout and one subject-data checkout")
    if checkouts["trusted-judge"].get("ref") != DEFAULT_BRANCH_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} judge code must come from the default branch, not the rehearsed subject")
    if checkouts["subject"].get("ref", TRUSTED_SHA_REF) != TRUSTED_SHA_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} subject data must be the rehearsed commit")
    _download(judge, name, "judge", REHEARSAL_FUZZ_ARTIFACT)
    for step in judge.get("steps", []):
        if re.search(r"(?:^|[\s=\"'])\.?/?subject/", step.get("run", "")):
            raise Reject("judge-subject-execution", f"{_where(name, 'judge')} names a path inside the subject tree; subject files are data only")
    for job_id, commands in REHEARSAL_REQUIRED.items():
        for command in commands:
            require_call(name, job_id, tree["jobs"][job_id], command)


# Read-only workflows must not leave the checkout token in .git/config for later steps (IN-08). A job that truly
# needs the persisted credential is listed here as (workflow file, job id) -> reason; none does today, because the
# jobs authenticate gh through an explicit step-level token and fetch only public sources.
READONLY_WORKFLOWS = ("ci.yml", "fixture-repro.yml", "preview.yml", "perf-attribution.yml")
CREDENTIAL_EXEMPT: dict[tuple[str, str], str] = {}


def check_readonly_workflows(root: Path, exempt=None) -> None:
    exempt = CREDENTIAL_EXEMPT if exempt is None else exempt
    trees = {item: read_workflow(root / ".github/workflows" / item) for item in READONLY_WORKFLOWS}
    for (workflow, job_id), reason in exempt.items():
        if workflow not in trees or job_id not in trees[workflow]["jobs"]:
            raise Reject("checkout-credentials", f"CREDENTIAL_EXEMPT names {workflow}.{job_id}, which does not exist")
        if not str(reason).strip():
            raise Reject("checkout-credentials", f"CREDENTIAL_EXEMPT entry {workflow}.{job_id} has no reason")
    for workflow, tree in trees.items():
        _check_checkout_credentials(workflow, tree, [job_id for job_id in tree["jobs"] if (workflow, job_id) not in exempt])


def check_ci(root: Path) -> None:
    name = "ci"
    tree = read_workflow(root / ".github/workflows/ci.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "ci must declare only top-level contents: read")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_bounded_downloads(name, tree)
    _check_ignored_failures(name, tree)
    job = _require_job(name, tree, "linux-sanitizers")
    perms = _permissions(job, tree["permissions"])
    if perms != {"actions": "read", "contents": "read"}:
        raise Reject("fuzz-producer-permissions", "ci.linux-sanitizers must hold only actions: read and contents: read")
    _check_checkout_credentials(name, tree, ("linux-sanitizers",))
    _upload(job, name, "linux-sanitizers", "v02-fuzz-${{ github.run_id }}-${{ github.run_attempt }}",
            ("build-asan/v02-fuzz-receipt.json", "build-asan/fuzz-artifacts/"), retain_on_failure=True)
    if any(_writes(_permissions(item, tree["permissions"])) for item in tree["jobs"].values()):
        raise Reject("producer-write-authority", "ci must not grant write authority to any job")
    gate = _require_job(name, tree, "required-native")
    _require_needs(name, "required-native", gate, CI_REQUIRED_NATIVE_NEEDS, "workflow-dependency")
    if str(gate.get("if", "")).strip() != "always()":
        raise Reject("workflow-dependency", "ci.required-native must run always() so skipped or failed lanes are rejected, not skipped")
    for var, lane in (("LINUX_SANITIZERS", "linux-sanitizers"), ("LINUX_SANITIZER_TESTS", "linux-sanitizers-tests"),
                       ("LINUX_SANITIZER_ACCEPTANCE", "linux-sanitizers-acceptance"),
                       ("NATIVE_LINUX", "native-linux"), ("CMAKE_FLOOR", "cmake-floor-3-25-3"),
                       ("PERF_GATE", "perf-gate")):
        mapped = [step.get("env", {}).get(var) for step in gate.get("steps", [])]
        if "${{ needs." + lane + ".result }}" not in mapped:
            raise Reject("workflow-dependency", f"ci.required-native must read the {lane} result")
    require_call(name, "required-native", gate, 'bash .github/scripts/check-player-result.sh "$PLAYER_GATE" "$PLAYER_REQUIRED" "$PLAYER_RESULT"')
    for command in CI_REQUIRED:
        require_call(name, "linux-sanitizers", job, command)
    native_linux = _require_job(name, tree, "native-linux")
    for command in CI_BUDGET_COMMANDS:
        require_call(name, "native-linux", native_linux, command)
    base_steps = [step for step in native_linux.get("steps", []) if step.get("id") == "budget_base"]
    base_run = str(base_steps[0].get("run", "")) if len(base_steps) == 1 else ""
    for needle in CI_BUDGET_BASE_PINS:
        if needle not in base_run:
            raise Reject("budget-base-fallback", f"ci.native-linux budget_base step must contain: {needle}")
    perf_job = _require_job(name, tree, "perf-gate")
    if perf_job.get("runs-on") != "ubuntu-24.04":
        raise Reject("runner-image", "ci.perf-gate must run on the pinned ubuntu-24.04 image")
    for command in PERF_GATE_COMMANDS:
        require_call(name, "perf-gate", perf_job, command)
    for shard, commands in CI_SANITIZER_SHARDS.items():
        shard_job = _require_job(name, tree, shard)
        for command in commands:
            require_call(name, shard, shard_job, command)
    for command, var, conditional in CI_STATUS_CALLS:
        require_call(name, "linux-sanitizers", job, command, conditional=conditional, errexit_off=True, status_var=var)


PERF_ATTRIBUTION_COMMANDS = (
    "bash tests/scripts/run-perf-gate.sh --attribution-dry-run",
    "bash tests/scripts/run-perf-gate.sh --attribution",
)


def check_perf_attribution(root: Path) -> None:
    """The dispatched D-17 measurement job: manual trigger only, read-only, never pushes (D-02a)."""
    name = "perf-attribution"
    tree = read_workflow(root / ".github/workflows/perf-attribution.yml")
    if _trigger_names(tree) != {"workflow_dispatch"}:
        raise Reject("workflow-trigger", "perf-attribution must trigger on workflow_dispatch only")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "perf-attribution must declare only top-level contents: read")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_bounded_downloads(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    _check_checkout_credentials(name, tree, tree["jobs"])
    if set(tree["jobs"]) != {"attribution"}:
        raise Reject("job-unclassified", "perf-attribution must hold exactly the attribution job")
    job = tree["jobs"]["attribution"]
    if _writes(_permissions(job, tree["permissions"])) or "permissions" in job:
        raise Reject("producer-write-authority", "perf-attribution.attribution must not hold or widen permissions")
    _check_unprivileged(name, tree, "attribution")
    if job.get("runs-on") != "ubuntu-24.04":
        raise Reject("runner-image", "perf-attribution must run on the pinned ubuntu-24.04 image")
    for command in PERF_ATTRIBUTION_COMMANDS:
        require_call(name, "attribution", job, command)


NIGHTLY_COMMANDS = (
    "cmake --preset phase1-asan -DGBB_TEST_INSTALL_PREFIX=",
    "cmake --build --preset phase1-asan",
    "ctest --preset phase1-asan --parallel 2 -R '^acceptance_stall_diagnosis(_replay_[12])?$' --output-on-failure --no-tests=error",
)


def check_nightly(root: Path) -> None:
    """The scheduled full ASan stall replay (D-19, D-108): two triggers, a read-only replay job that runs the repository
    code, and a separate report job that alone holds issues: write, has no checkout and runs no repository code (T-16-07)."""
    name = "nightly-asan"
    tree = read_workflow(root / ".github/workflows/nightly-asan.yml")
    if _trigger_names(tree) != {"schedule", "workflow_dispatch"}:
        raise Reject("workflow-trigger", "nightly-asan must trigger on schedule and workflow_dispatch only")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "nightly-asan must declare only top-level contents: read")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_bounded_downloads(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    if set(tree["jobs"]) != {"asan-full-replay", "report-red"}:
        raise Reject("job-unclassified", "nightly-asan must hold exactly the asan-full-replay and report-red jobs")
    replay = tree["jobs"]["asan-full-replay"]
    if "permissions" in replay or _writes(_permissions(replay, tree["permissions"])):
        raise Reject("producer-write-authority", "nightly-asan.asan-full-replay must not hold or widen permissions")
    _check_unprivileged(name, tree, "asan-full-replay")
    _check_checkout_credentials(name, tree, ("asan-full-replay",))
    if replay.get("runs-on") != "ubuntu-24.04":
        raise Reject("runner-image", "nightly-asan.asan-full-replay must run on the pinned ubuntu-24.04 image")
    if "timeout-minutes" not in replay:
        raise Reject("job-timeout", "nightly-asan.asan-full-replay must carry timeout-minutes")
    for command in NIGHTLY_COMMANDS:
        require_call(name, "asan-full-replay", replay, command)
    report = tree["jobs"]["report-red"]
    if _needs(report) != {"asan-full-replay"} or str(report.get("if", "")).strip() != "failure()":
        raise Reject("nightly-report-trigger", "nightly-asan.report-red must need asan-full-replay and run if: failure()")
    if report.get("permissions") != {"issues": "write"}:
        raise Reject("nightly-report-permissions", "nightly-asan.report-red must hold issues: write as its only permission")
    if _checkouts(report) or any("uses" in step for step in report.get("steps", [])):
        raise Reject("nightly-report-checkout", "nightly-asan.report-red must not check out source or use any action")


def _check_residual_classification(roles=None, subject=None, exempt=None, overlays=None) -> None:
    """Every residual job is named once: it runs tagged code (job token forbidden) or is a reasoned exemption."""
    roles = RELEASE_ROLES if roles is None else roles
    subject = RESIDUAL_SUBJECT_JOBS if subject is None else subject
    exempt = TOKEN_SCOPE_EXEMPT if exempt is None else exempt
    overlays = TRUSTED_OVERLAYS if overlays is None else overlays
    residual = {job_id for job_id, role in roles.items() if role == "residual"}
    if set(subject) & set(exempt) or residual != set(subject) | set(exempt) or len(set(subject)) != len(subject):
        raise Reject("residual-classification", "every residual job must be in exactly one of RESIDUAL_SUBJECT_JOBS or TOKEN_SCOPE_EXEMPT")
    if any(not isinstance(reason, str) or not reason.strip() for reason in exempt.values()):
        raise Reject("residual-classification", "every TOKEN_SCOPE_EXEMPT job needs a non-empty reason")
    if not set(overlays) <= set(subject):
        raise Reject("residual-classification", "TRUSTED_OVERLAYS may name only RESIDUAL_SUBJECT_JOBS")


def _check_release_presence(workflow: str, tree: dict) -> None:
    jobs = tree["jobs"]
    for job_id, items in RELEASE_PRESENCE.items():
        job = _require_job(workflow, tree, job_id)
        for item in items:
            kind = item[0]
            if kind == "env":
                if item[1] not in (job.get("env") or {}):
                    raise Reject("release-presence", f"{_where(workflow, job_id)} does not define env {item[1]}")
            elif kind == "if":
                if item[1] not in str(job.get("if", "")):
                    raise Reject("release-presence", f"{_where(workflow, job_id)} job if: lacks {item[1]}")
            elif kind == "step-if":
                guarded = [step for step in job.get("steps", []) if step.get("name") == item[1]]
                if len(guarded) != 1 or item[2] not in str(guarded[0].get("if", "")):
                    raise Reject("release-presence", f"{_where(workflow, job_id)} step {item[1]!r} is not guarded by {item[2]}")
            elif kind == "step-lines":
                named = [step for step in job.get("steps", []) if step.get("name") == item[1]]
                lines = []
                if len(named) == 1 and "if" not in named[0] and _runs_under_errexit(named[0]):
                    lines = [line.strip() for line in str(named[0].get("run", "")).splitlines()
                             if line.strip() and not line.strip().startswith("#")]
                wanted = list(item[2])
                if not any(lines[at:at + len(wanted)] == wanted for at in range(len(lines))):
                    raise Reject("release-presence", f"{_where(workflow, job_id)} step {item[1]!r} does not refuse a partial candidate set")
            else:
                try:
                    require_call(workflow, job_id, jobs[job_id], item[1], conditional=item[2])
                except Reject as exc:
                    raise Reject("release-presence", f"{_where(workflow, job_id)} lacks required wiring: {exc}") from exc
    for key, expected in RELEASE_GUARD_EXPRESSIONS.items():
        job = _require_job(workflow, tree, key[0])
        if len(key) == 1:
            actual, subject = job.get("if", ""), "job if:"
        else:
            named = [step for step in job.get("steps", []) if step.get("name") == key[1]]
            actual, subject = (named[0].get("if", "") if len(named) == 1 else ""), f"step {key[1]!r} if:"
        if _normalise_if(actual) != _normalise_if(expected):
            raise Reject("release-presence", f"{_where(workflow, key[0])} {subject} is not exactly the pinned guard {expected!r}")
    for job_id, runner in RELEASE_RUNNERS.items():
        actual = str(_require_job(workflow, tree, job_id).get("runs-on", "")).strip()
        if actual != runner:
            raise Reject("runner-image", f"{_where(workflow, job_id)} must run on {runner}, not {actual or 'an unset image'}")


def _trigger_names(tree: dict) -> set[str]:
    on = tree.get("on")
    if isinstance(on, dict):
        return set(on)
    if isinstance(on, list):
        return {str(item) for item in on}
    if isinstance(on, str) and on:
        return {on}
    return set()


def _check_release_triggers(workflow: str, tree: dict) -> None:
    extra = _trigger_names(tree) - RELEASE_TRIGGERS
    if extra:
        raise Reject("workflow-trigger", f"{workflow} may only be started by {sorted(RELEASE_TRIGGERS)}, not {sorted(extra)}")


def _check_release_entrypoint(root: Path) -> None:
    """release.yml is reusable, and the release-please workflow must call it as a job so that the release outputs and
    the candidate jobs live in one workflow run."""
    release = read_workflow(root / ".github/workflows/release.yml")
    if "workflow_call" not in _trigger_names(release):
        raise Reject("release-entrypoint", "release.yml must be a reusable workflow (workflow_call)")
    entry = read_workflow(root / ".github/workflows" / RELEASE_ENTRYPOINT_WORKFLOW)
    if not any(job.get("uses") == RELEASE_LOCAL_PATH for job in entry["jobs"].values()):
        raise Reject("release-entrypoint", f"{RELEASE_ENTRYPOINT_WORKFLOW} must call {RELEASE_LOCAL_PATH} from a job")


def check_release(root: Path) -> None:
    name = "release"
    _check_residual_classification()
    tree = read_workflow(root / ".github/workflows/release.yml")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("workflow-permissions", "release must declare only top-level contents: read")
    _check_release_triggers(name, tree)
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_bounded_downloads(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    jobs = tree["jobs"]
    for job_id in jobs:
        if job_id not in RELEASE_ROLES:
            raise Reject("job-unclassified", f"{_where(name, job_id)} has no declared trust role; classify it in the policy")
    for job_id, role in RELEASE_ROLES.items():
        job = _require_job(name, tree, job_id)
        perms = _permissions(job, tree["permissions"])
        if role in ("producer", "trusted-reader") and _writes(perms):
            raise Reject("producer-write-authority", f"{_where(name, job_id)} runs {role} work with write authority")
        if role == "producer":
            _check_unprivileged(name, tree, job_id)
            _check_checkout_credentials(name, tree, (job_id,))
            _require_needs(name, job_id, job, {"release", "candidate"}, "workflow-dependency")
            checkouts = _checkouts(job)
            if len(checkouts) != 1 or checkouts[0].get("with", {}).get("ref") != SUBJECT_REF:
                raise Reject("producer-checkout", f"{_where(name, job_id)} must check out exactly the tagged source")
            artifact, files = RELEASE_ARTIFACTS[job_id]
            _upload(job, name, job_id, artifact, files)
        elif role == "trusted-reader":
            if perms != {"actions": "read", "contents": "read"}:
                raise Reject("reader-permissions", f"{_where(name, job_id)} needs only actions: read and contents: read")
            _check_checkout_credentials(name, tree, (job_id,))
            _check_trusted_checkout(name, job_id, job, TRUSTED_SHA_REF, "trusted")
            _require_needs(name, job_id, job, {"release", "candidate"}, "workflow-dependency")
            artifact, files = RELEASE_ARTIFACTS[job_id]
            _upload(job, name, job_id, artifact, files)
        elif role == "residual":
            _check_checkout_credentials(name, tree, (job_id,))
            _check_token_subject_execution(name, job_id, job, job_wide=job_id in TOKEN_SCOPE_EXEMPT)
            if job_id in RESIDUAL_SUBJECT_JOBS:
                _check_token_scope(name, job_id, job)
            if job_id in TRUSTED_OVERLAYS:
                _check_trusted_overlay(name, job_id, job, TRUSTED_OVERLAYS[job_id])
        elif role == "attacher":
            if perms != {"contents": "write"}:
                raise Reject("attacher-permissions", f"{_where(name, job_id)} must hold exactly contents: write")
            _check_checkout_credentials(name, tree, (job_id,))
            _check_trusted_checkout(name, job_id, job, TRUSTED_SHA_REF, "trusted", optional=True)
            _require_needs(name, job_id, job, {"release", "candidate", "candidate-corpus", "candidate-fuzz", "candidate-performance"}, "attacher-dependencies")
            for producer in ("candidate-corpus", "candidate-fuzz", "candidate-performance"):
                _download(job, name, job_id, RELEASE_ARTIFACTS[producer][0])
                if f"needs.{producer}.result == 'success'" not in str(job.get("if", "")):
                    raise Reject("attacher-dependencies", f"{_where(name, job_id)} must run only after {producer} succeeded")
            if any(SUBJECT_EXECUTION.search(step.get("run", "")) for step in job.get("steps", [])):
                raise Reject("attacher-subject-execution", f"{_where(name, job_id)} must execute trusted code only")
    _require_needs(name, "candidate-platform-manifest", jobs["candidate-platform-manifest"], {"attach-v02-evidence"}, "workflow-dependency")
    _require_needs(name, "publish-qualified-release", jobs["publish-qualified-release"], {"candidate-platform-manifest"}, "workflow-dependency")
    for job_id in ("candidate-platform-manifest", "publish-qualified-release"):
        job = jobs[job_id]
        _check_checkout_credentials(name, tree, (job_id,))
        trusted = [step for step in _checkouts(job) if step.get("with", {}).get("path") == "trusted"]
        if len(trusted) != 1 or trusted[0]["with"].get("ref") != TRUSTED_SHA_REF:
            raise Reject("judge-trust", f"{_where(name, job_id)} needs one trusted checkout of ref {TRUSTED_SHA_REF} at path trusted")
        _check_no_subject_execution(name, job_id, job)
    for job_id, commands in RELEASE_REQUIRED.items():
        for command in commands:
            require_call(name, job_id, jobs[job_id], command)
    _check_fuzz_source_binding(name, tree)
    _check_fuzz_wait_budget(name, tree)
    publisher = jobs["publish-qualified-release"]
    gate_at = require_call(name, "publish-qualified-release", publisher, RELEASE_REQUIRED["publish-qualified-release"][2])
    publish_at = require_call(name, "publish-qualified-release", publisher, RELEASE_REQUIRED["publish-qualified-release"][4])
    if gate_at >= publish_at:
        raise Reject("publication-order", f"{_where(name, 'publish-qualified-release')} must run the final downloaded-byte gate before the one publication transition")
    # Recovery decides from independently read live state BEFORE any retry write (P15-09): inventory, then the decision,
    # then the upload; and the published-asset readback only after the one publication transition.
    upload = 'gh release upload "$RELEASE_TAG" "build/release-final/$name" --repo "$GH_REPO"'
    inventory_at = require_call(name, "publish-qualified-release", publisher, _PUBLISH_INVENTORY)
    recovery_at = require_call(name, "publish-qualified-release", publisher, _PUBLISH_RECOVERY)
    upload_at = require_call(name, "publish-qualified-release", publisher, upload, conditional=True)
    if not inventory_at < recovery_at < upload_at:
        raise Reject("recovery-order", f"{_where(name, 'publish-qualified-release')} must decide recovery from live state before any final-metadata upload")
    readback_at = require_call(name, "publish-qualified-release", publisher, RELEASE_REQUIRED["publish-qualified-release"][3] + ' "$assets" build/release-final/api-assets.json')
    if readback_at <= publish_at:
        raise Reject("publication-order", f"{_where(name, 'publish-qualified-release')} must read published assets back after the publication transition")
    for job_id, calls in RELEASE_SMOKE_REQUIRED.items():
        for command, extra in calls:
            require_call(name, job_id, jobs[job_id], command, contains=extra, conditional=True)
    _check_release_presence(name, tree)
    _require_needs(name, "candidate-windows", _require_job(name, tree, "candidate-windows"), {"release", "candidate-macos"}, "workflow-dependency")
    _check_release_entrypoint(root)
    attach = jobs["attach-v02-evidence"]
    require_call(name, "attach-v02-evidence", attach, 'gh release upload "$RELEASE_TAG" "$1/$2" --repo "$GH_REPO"', conditional=True)
    attach_call = require_call(name, "attach-v02-evidence", attach, 'attach "$dir" "$name"', conditional=True)
    attach_inventory_at = require_call(name, "attach-v02-evidence", attach, _ATTACH_INVENTORY)
    attach_recovery_at = require_call(name, "attach-v02-evidence", attach, _ATTACH_RECOVERY)
    if not attach_inventory_at < attach_recovery_at < attach_call:
        raise Reject("recovery-order", f"{_where(name, 'attach-v02-evidence')} must decide recovery from live state before any evidence upload")
    # Last, so every other rule's diagnostic keeps priority over this one.
    # Scope: only these five jobs check out and build the tagged tree while a step holds the token. The
    # trusted-reader (candidate-fuzz) and the attacher (attach-v02-evidence) check out only the trusted
    # workflow revision (ref github.sha, path trusted, persist-credentials false, _check_trusted_checkout),
    # never run the tagged tree, and read producer artifacts as data through trusted verifiers.
    for job_id, role in RELEASE_ROLES.items():
        if role == "residual":
            _check_token_step_commands(name, job_id, jobs[job_id], job_wide=job_id in TOKEN_SCOPE_EXEMPT)


def check_all(root: Path) -> dict[str, int]:
    check_producer_script(root)
    check_rehearsal(root)
    check_ci(root)
    check_perf_attribution(root)
    check_nightly(root)
    check_readonly_workflows(root)
    check_release(root)
    residual = sorted(job_id for job_id, role in RELEASE_ROLES.items() if role == "residual")
    return {"residual": len(residual)}


# --------------------------------------------------------------------------- self-test
WORKFLOWS = ("release-rehearsal.yml", "release.yml", "release-please.yml", "ci.yml", "fixture-repro.yml", "preview.yml", "perf-attribution.yml", "nightly-asan.yml")


def _copy_fixture(root: Path, target: Path) -> None:
    for item in WORKFLOWS:
        destination = target / ".github/workflows" / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / ".github/workflows" / item).read_bytes())
    script = target / PRODUCER_SCRIPT
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes((root / PRODUCER_SCRIPT).read_bytes()) if (root / PRODUCER_SCRIPT).is_file() else None


def _run_cli(fixture: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(Path(__file__).resolve()), "--check", "--root", str(fixture)],
        capture_output=True, text=True, check=False, cwd=cwd, timeout=60,
    )


def _m(label: str, workflow: str, after: str, old: str, new: str, expected: str):
    return (label, workflow, [(after, old, new)], expected)


JUDGE_CALL = "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject"
_REHEARSAL_TAG_LINE = "bash .github/scripts/produce-release-evidence.sh verify-subject --subject . --source-sha \"$GITHUB_SHA\" --tag \"$REHEARSAL_TAG\" --local-tag"
JUDGE_STEP = "      - name: Judge workflow privilege and trust wiring from the trusted checkout\n"
FUZZ_TAG_CHECK = '[[ "$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq .sha)" == "$SOURCE_SHA" ]] || {'


_TOKEN_STEP_ANCHOR = "mkdir -p build/downloaded build/consumer-work"


def _token_step_mutations():
    """Fifteen forms inserted into the tokened candidate step "Download the exact draft bytes", each expected to be
    refused as token-subject-execution. Only the command-head judge can reject them: none names a build tool or a
    tests/scripts path, and the step already holds the token."""
    cases = (
        ("bare python3 on a tagged script", "python3 -I .github/scripts/x.py"),
        ("bare bash on a tagged script", "bash build/consumer.sh"),
        ("bare tagged binary", "./build/gabbaboy-cli --version"),
        ("tagged binary inside an echo argument substitution", 'echo "$(./build/gabbaboy-cli --version)"'),
        ("tagged script inside an assignment substitution", "x=$(bash build/consumer.sh)"),
        ("tagged script inside a gh --jq substitution", 'gh api x --jq "$(python3 -I .github/scripts/x.py)"'),
        ("tagged binary inside an arithmetic command", "(( $(./build/gabbaboy-cli --version) > 0 ))"),
        ("tagged script inside a backtick substitution", "echo `bash build/consumer.sh`"),
        ("tagged binary inside a here-string", 'jq . <<<"$(./build/gabbaboy-cli --version)"'),
        ("tagged binary inside an unquoted heredoc body", "cat <<EOF\n{I}$(./build/gabbaboy-cli --version)\n{I}EOF"),
        ("tagged binary inside a for list", 'for v in "$(./build/gabbaboy-cli --version)"; do echo "$v"; done'),
        ("tagged binary inside an array element", 'names=( a "$(./build/gabbaboy-cli --version)" )'),
        ("trusted operand escaped with a dot-dot segment", "bash trusted/../build/consumer.sh"),
        ("variable command head", 'run=./build/gabbaboy-cli\n{I}"$run" --version'),
        ("bare subshell the reader cannot place", "( ./build/gabbaboy-cli --version )"),
    )
    return [_m(f"release candidate tokened download step runs {label}", "release.yml", "Download the exact draft bytes", _TOKEN_STEP_ANCHOR,
               f"{line}\n{{I}}{_TOKEN_STEP_ANCHOR}", "token-subject-execution") for label, line in cases]


def _mutations():
    """(label, workflow, [(after, old, new)], expected code). Each edit replaces the first `old` following `after`
    (or the file start); `{I}` in `new` stands for the indentation of the line that holds `old`."""
    reh = "release-rehearsal.yml"
    rel = "release.yml"
    return [
        _m("rehearsal fuzz producer gains contents: write", reh, "  fuzz:\n", "    runs-on: ubuntu-24.04\n",
         "    runs-on: ubuntu-24.04\n    permissions:\n      contents: write\n", "producer-write-authority"),
        _m("rehearsal top-level write", reh, "", "permissions:\n  contents: read\n", "permissions:\n  contents: write\n",
         "workflow-permissions"),
        _m("rehearsal judge reads judge code from the subject", reh, "  judge:\n", f"ref: {DEFAULT_BRANCH_REF}",
         f"ref: {TRUSTED_SHA_REF}", "judge-trust"),
        _m("rehearsal judge runs a path inside the subject tree", reh, "  judge:\n",
         "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject",
         "python3 -I subject/.github/scripts/verify-workflow-policy.py --check --root subject", "judge-subject-execution"),
        _m("rehearsal judge stops waiting for the fuzz producer", reh, "  judge:\n",
         "needs: [corpus, fuzz, performance, perf-gate, package, aggregate]", "needs: [corpus, fuzz, performance, package, aggregate]",
         "workflow-dependency"),
        _m("rehearsal judge stops waiting for the perf-gate producer", reh, "  judge:\n",
         "needs: [corpus, fuzz, performance, perf-gate, package, aggregate]", "needs: [corpus, fuzz, performance, package, aggregate]",
         "workflow-dependency"),
        _m("rehearsal perf-gate seeded-regression control removed", reh, "  perf-gate:\n",
         "bash tests/scripts/run-perf-gate.sh --seeded-regression", "true", "required-command-not-executed"),
        _m("required-native stops waiting for perf-gate", "ci.yml", "  required-native:\n", "      - perf-gate\n", "", "workflow-dependency"),
        _m("required-native ignores the perf-gate result", "ci.yml", "  required-native:\n",
           "          PERF_GATE: ${{ needs.perf-gate.result }}\n", "", "workflow-dependency"),
        _m("ci perf-gate gate command replaced by echo", "ci.yml", "  perf-gate:\n",
           "run: bash tests/scripts/run-perf-gate.sh --gate", "run: echo bash tests/scripts/run-perf-gate.sh --gate",
           "required-command-not-executed"),
        _m("ci budget ratchet drops --base", "ci.yml", "  native-linux:\n",
           'verify-test-budget.py --build-dir build --base "$BUDGET_BASE"', "verify-test-budget.py --build-dir build",
           "required-command-not-executed"),
        _m("ci budget base loses the unreachable-parent fallback", "ci.yml", "  native-linux:\n",
           ' || ! git cat-file -e "${base}^{commit}"; then', "; then", "budget-base-fallback"),
        _m("ci budget base stops failing closed", "ci.yml", "  native-linux:\n",
           '          git cat-file -e "${base}^{commit}"\n          echo', "          echo", "budget-base-fallback"),
        _m("nightly gains a pull_request trigger", "nightly-asan.yml", "", "  workflow_dispatch:\n",
           "  workflow_dispatch:\n  pull_request:\n", "workflow-trigger"),
        _m("nightly replay job gains issues: write", "nightly-asan.yml", "  asan-full-replay:\n", "    runs-on: ubuntu-24.04\n",
           "    runs-on: ubuntu-24.04\n    permissions:\n      issues: write\n", "producer-write-authority"),
        _m("nightly report job gains a checkout", "nightly-asan.yml", "  report-red:\n", "    steps:\n",
           "    steps:\n      - name: Check out source\n        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683\n"
           "        with:\n          persist-credentials: false\n", "nightly-report-checkout"),
        _m("nightly replay drops the full-replay ctest filter", "nightly-asan.yml", "  asan-full-replay:\n",
           "-R '^acceptance_stall_diagnosis(_replay_[12])?$'", "-R '^acceptance_'", "required-command-not-executed"),
        _m("ci perf-gate no-op twin control removed", "ci.yml", "  perf-gate:\n",
           "bash tests/scripts/run-perf-gate.sh --noop-twin", "true", "required-command-not-executed"),
        _m("ci perf-gate checkout persists credentials", "ci.yml", "  perf-gate:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("ci perf-gate gains contents: write", "ci.yml", "  perf-gate:\n", "    runs-on: ubuntu-24.04\n",
           "    runs-on: ubuntu-24.04\n    permissions:\n      contents: write\n", "producer-write-authority"),
        _m("perf-attribution gains a push trigger", "perf-attribution.yml", "", "on:\n  workflow_dispatch:\n",
           "on:\n  workflow_dispatch:\n  push:\n    branches: [main]\n", "workflow-trigger"),
        _m("perf-attribution top-level write", "perf-attribution.yml", "", "permissions:\n  contents: read\n",
           "permissions:\n  contents: write\n", "workflow-permissions"),
        _m("perf-attribution job gains contents: write", "perf-attribution.yml", "  attribution:\n", "    runs-on: ubuntu-24.04\n",
           "    runs-on: ubuntu-24.04\n    permissions:\n      contents: write\n", "producer-write-authority"),
        _m("perf-attribution checkout persists credentials", "perf-attribution.yml", "  attribution:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("perf-attribution dry run before cachegrind work removed", "perf-attribution.yml", "  attribution:\n",
           "run: bash tests/scripts/run-perf-gate.sh --attribution-dry-run", "run: true", "required-command-not-executed"),
        _m("rehearsal fuzz artifact no longer retained", reh, "  fuzz:\n", "name: " + REHEARSAL_FUZZ_ARTIFACT,
         "name: renamed-" + REHEARSAL_FUZZ_ARTIFACT, "artifact-flow"),
        _m("rehearsal checkout persists credentials", reh, "  corpus:\n", "persist-credentials: false",
         "persist-credentials: true", "checkout-credentials"),
        _m("unpinned action", reh, "", "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
         "actions/upload-artifact@v4", "workflow-unpinned-action"),
        _m("YAML anchor", reh, "", "REHEARSAL_TAG: v0.2.0\n", "REHEARSAL_TAG: &tag v0.2.0\n", "workflow-unsupported-yaml"),
        _m("release corpus producer gains contents: write", rel, "  candidate-corpus:\n", "      contents: read\n",
         "      contents: write\n", "producer-write-authority"),
        _m("release corpus producer receives the job token", rel, "  candidate-corpus:\n", "    env:\n",
         "    env:\n      GH_TOKEN: ${{ github.token }}\n", "producer-token"),
        _m("release performance checkout persists credentials", rel, "  candidate-performance:\n",
         "persist-credentials: false", "persist-credentials: true", "checkout-credentials"),
        _m("release fuzz reader checks out the tagged subject", rel, "  candidate-fuzz:\n", "ref: ${{ github.sha }}",
         "ref: ${{ env.SOURCE_SHA }}", "judge-trust"),
        _m("release attacher checks out the tagged subject", rel, "  attach-v02-evidence:\n", "    steps:\n",
         "    steps:\n      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2\n        with:\n          ref: ${{ env.SOURCE_SHA }}\n          persist-credentials: false\n",
         "judge-trust"),
        _m("release attacher stops waiting for the corpus producer", rel, "  attach-v02-evidence:\n",
         "needs: [release, candidate, candidate-corpus, candidate-fuzz, candidate-performance]",
         "needs: [release, candidate, candidate-fuzz, candidate-performance]", "attacher-dependencies"),
        _m("release attacher gains a second permission", rel, "  attach-v02-evidence:\n", "      contents: write\n",
         "      contents: write\n      actions: write\n", "attacher-permissions"),
        _m("release manifest no longer waits for the attacher", rel, "  candidate-platform-manifest:\n",
         "candidate-performance, attach-v02-evidence]", "candidate-performance]", "workflow-dependency"),
        _m("new unclassified release job", rel, "", "\njobs:\n",
         "\njobs:\n  surprise:\n    runs-on: ubuntu-22.04\n    steps:\n      - run: true\n", "job-unclassified"),
        # Textual decoys and disabled gates (P15-10): the required call is present as text but never runs.
        # Run 39634983581: the consumer verifier needs a candidate manifest, so the stale prefix-only call must not pass.
        _m("package consumer call without a candidate manifest", reh, "  package:\n", " --candidate-manifest \"$RUNNER_TEMP/candidate-manifest.json\"", "", "required-command-not-executed"),
        _m("package candidate manifest never written", reh, "  package:\n", "--write-candidate-manifest", "--no-manifest", "required-command-not-executed"),
        # Run 39641384657: --check-receipt refuses to qualify a receipt without an independent Git-tree repo.
        _m("source archive receipt check without a repo", reh, "  package:\n", " --source-sha \"$SOURCE_SHA\" --repo .\n", " --source-sha \"$SOURCE_SHA\"\n", "required-command-not-executed"),
        _m("comment instead of the judge call", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, "# " + JUDGE_CALL, "required-command-not-executed"),
        _m("echo instead of the judge call", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, "echo " + JUDGE_CALL, "required-command-not-executed"),
        ("dead if false branch", "release-rehearsal.yml", [("  judge:\n", JUDGE_CALL, "if false; then\n{I}  " + JUDGE_CALL + "\n{I}fi")], "required-command-not-executed"),
        ("dead constant comparison branch", "release-rehearsal.yml", [("  judge:\n", JUDGE_CALL, "if [[ 0 == 1 ]]; then\n{I}  " + JUDGE_CALL + "\n{I}fi")], "required-command-not-executed"),
        _m("failure swallowed with || true", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, JUDGE_CALL + " || true", "required-command-not-executed"),
        _m("guarded by a false && list", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, "false && " + JUDGE_CALL, "required-command-not-executed"),
        _m("errexit disabled before the call", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, "set +e\n{I}" + JUDGE_CALL, "required-command-not-executed"),
        _m("exit before the call", "release-rehearsal.yml", "  judge:\n", JUDGE_CALL, "exit 0\n{I}" + JUDGE_CALL, "required-command-not-executed"),
        _m("continue-on-error on the judge step", "release-rehearsal.yml", "  judge:\n", JUDGE_STEP, JUDGE_STEP + "        continue-on-error: true\n", "ignored-gate"),
        _m("step disabled with if false", "release-rehearsal.yml", "  judge:\n", JUDGE_STEP, JUDGE_STEP + "        if: ${{ false }}\n", "disabled-gate"),
        _m("judge job disabled with if false", "release-rehearsal.yml", "  judge:\n", "    runs-on: ubuntu-24.04\n", "    if: ${{ false }}\n    runs-on: ubuntu-24.04\n", "disabled-gate"),
        ("call moved to the wrong job", "release-rehearsal.yml", [
            ("  judge:\n", JUDGE_CALL, "true"),
            ("  package:\n", "# does not exist yet, so build the equivalent from the local-only tag and run the same checker.\n",
             "# does not exist yet, so build the equivalent from the local-only tag and run the same checker.\n{I}" + JUDGE_CALL + "\n")],
         "required-command-not-executed"),
        _m("fuzz verifier replaced by echo", "release-rehearsal.yml", "  fuzz:\n", "python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan",
           "echo python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan", "required-command-not-executed"),
        _m("release corpus claims verifier commented out", "release.yml", "  candidate-corpus:\n", "python3 -I tests/scripts/verify-cgb-corpus-claims.py",
           "# python3 -I tests/scripts/verify-cgb-corpus-claims.py", "required-command-not-executed"),
        _m("release corpus CTest failure no longer gated", "release.yml", "  candidate-corpus:\n", 'run: test "$FULL_CTEST_OUTCOME" = success',
           'run: echo "$FULL_CTEST_OUTCOME"', "ignored-gate"),
        _m("release hosted fuzz verifier loses its run identity", "release.yml", "  candidate-fuzz:\n", '--run-id "$run_id" --attempt "$attempt"',
           '--attempt "$attempt"', "required-command-not-executed"),
        # Fuzz reader binds the release commit without the moving checkout and bounds its wait (WR-04).
        _m("release fuzz reader compares HEAD with the source SHA", rel, "  candidate-fuzz:\n", FUZZ_TAG_CHECK,
           '[[ "$(git rev-parse HEAD)" == "$SOURCE_SHA" ]] || exit 1\n{I}' + FUZZ_TAG_CHECK, "fuzz-source-binding"),
        _m("release fuzz reader asserts ancestry of the source against HEAD", rel, "  candidate-fuzz:\n", FUZZ_TAG_CHECK,
           'git merge-base --is-ancestor "$SOURCE_SHA" HEAD || exit 1\n{I}' + FUZZ_TAG_CHECK, "fuzz-source-binding"),
        _m("release fuzz reader tag API check replaced by a no-op", rel, "  candidate-fuzz:\n", FUZZ_TAG_CHECK,
           "true || {", "required-command-not-executed"),
        _m("release fuzz reader job timeout below its worst-case wait", rel, "  candidate-fuzz:\n", "timeout-minutes: 112",
           "timeout-minutes: 95", "fuzz-wait-budget"),
        _m("release fuzz reader attempts budget deleted", rel, "  candidate-fuzz:\n", "      CI_RUN_WAIT_ATTEMPTS: 90\n", "", "fuzz-wait-budget"),
        _m("release fuzz reader elapsed-time deadline comparison deleted", rel, "  candidate-fuzz:\n",
           '            if [[ $((SECONDS - poll_start)) -ge "$CI_RUN_WAIT_DEADLINE_SECONDS" ]]; then break; fi\n', "", "fuzz-wait-budget"),
        _m("release fuzz reader deadline below attempts times interval", rel, "  candidate-fuzz:\n", "CI_RUN_WAIT_DEADLINE_SECONDS: 3000",
           "CI_RUN_WAIT_DEADLINE_SECONDS: 2400", "fuzz-wait-budget"),
        _m("release fuzz reader runs lookup loses its request timeout", rel, "  candidate-fuzz:\n",
           'runs=$(timeout "$CI_RUN_REQUEST_TIMEOUT_SECONDS" gh api', "runs=$(gh api", "fuzz-wait-budget"),
        _m("release fuzz reader hosted poll no longer takes the budget", rel, "  candidate-fuzz:\n",
           ' \\\n            --poll-seconds "$HOSTED_POLL_SECONDS"', "", "required-command-not-executed"),
        _m("rehearsal ctest step interpolates the run nonce into its run body", "release-rehearsal.yml",
           "Run the full CTest stream once", '${RUN_NONCE}.xml"', '${{ steps.corpus_run.outputs.run_nonce }}.xml"', "run-expression"),
        _m("release performance verifier skipped by if false", "release.yml", "  candidate-performance:\n",
           "      - name: Measure the clean paired v0.1.0 baseline and exact-tag candidate\n",
           "      - name: Measure the clean paired v0.1.0 baseline and exact-tag candidate\n        if: ${{ false }}\n", "disabled-gate"),
        _m("release attacher upload commented out", "release.yml", "  attach-v02-evidence:\n", 'gh release upload "$RELEASE_TAG" "$1/$2"',
           '# gh release upload "$RELEASE_TAG" "$1/$2"', "required-command-not-executed"),
        _m("release manifest judge call replaced by echo", "release.yml", "  candidate-platform-manifest:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence',
           'echo bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence', "required-command-not-executed"),
        _m("release manifest judge taken from the subject checkout", "release.yml", "  candidate-platform-manifest:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence',
           'bash .github/scripts/verify-release-gates.sh --check-v02-evidence', "subject-judge-execution"),
        _m("release manifest trusted checkout points at the tag", "release.yml", "  candidate-platform-manifest:\n", "          ref: ${{ github.sha }}\n          path: trusted",
           "          ref: ${{ env.SOURCE_SHA }}\n          path: trusted", "judge-trust"),
        _m("release publisher final gate taken from the subject checkout", "release.yml", "  publish-qualified-release:\n", 'run: bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final',
           'run: bash .github/scripts/verify-release-gates.sh --check-draft-final', "subject-judge-execution"),
        _m("release publisher published-asset verifier taken from the subject checkout", "release.yml", "  publish-qualified-release:\n", "python3 -I trusted/.github/scripts/verify-published-release-assets.py",
           "python3 .github/scripts/verify-published-release-assets.py", "subject-judge-execution"),
        ("release publication runs before the final downloaded-byte gate", "release.yml", [
            ("  publish-qualified-release:\n", 'run: bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"', "run: true"),
            ("  publish-qualified-release:\n", 'echo "Published the exact qualified release', 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"\n{I}echo "Published the exact qualified release')],
         "publication-order"),
        _m("release publisher does not wait for the manifest judge", "release.yml", "  publish-qualified-release:\n", "candidate-windows, candidate-platform-manifest]",
           "candidate-windows]", "workflow-dependency"),
        _m("required-native stops waiting for the sanitizer lane", "ci.yml", "  required-native:\n", "      - linux-sanitizers\n", "", "workflow-dependency"),
        _m("required-native stops waiting for the sanitizer test lane", "ci.yml", "  required-native:\n", "      - linux-sanitizers-tests\n", "",
           "workflow-dependency"),
        _m("required-native ignores the sanitizer test lane result", "ci.yml", "  required-native:\n",
           "          LINUX_SANITIZER_TESTS: ${{ needs.linux-sanitizers-tests.result }}\n", "", "workflow-dependency"),
        _m("sanitizer test lane drops its inventory check", "ci.yml", "  linux-sanitizers-tests:\n",
           "          bash .github/scripts/verify-test-inventory.sh build-asan/ctest.xml build-asan/expected-shard.txt\n", "", "required-command-not-executed"),
        _m("required-native stops waiting for the sanitizer acceptance shard", "ci.yml", "  required-native:\n",
           "      - linux-sanitizers-acceptance\n", "", "workflow-dependency"),
        _m("sanitizer shards stop being complementary", "ci.yml", "  linux-sanitizers-acceptance:\n",
           "-R '^acceptance_'", "-R '^acceptance_cgb'", "required-command-not-executed"),
        _m("sanitizer acceptance shard checks the whole inventory instead of its slice", "ci.yml", "  linux-sanitizers-acceptance:\n",
           "          grep -E '^acceptance_' tests/expected-tests.txt | grep -vE '^acceptance_stall_diagnosis(_replay_[12])?$' > build-asan/expected-shard.txt\n",
           "          cp tests/expected-tests.txt build-asan/expected-shard.txt\n",
           "required-command-not-executed"),
        _m("sanitizer acceptance shard keeps the full stall replay", "ci.yml", "  linux-sanitizers-acceptance:\n",
           " -E '^acceptance_stall_diagnosis(_replay_[12])?$'", "", "required-command-not-executed"),
        _m("sanitizer acceptance shard excludes the bounded stall replay", "ci.yml", "  linux-sanitizers-acceptance:\n",
           "'^acceptance_stall_diagnosis(_replay_[12])?$' --output-on-failure", "'^acceptance_stall_' --output-on-failure",
           "required-command-not-executed"),
        # Shared unprivileged producer contract (P15-15).
        _m("rehearsal corpus re-inlines the local tag setup", "release-rehearsal.yml", "  corpus:\n", _REHEARSAL_TAG_LINE,
           'git tag -f "$REHEARSAL_TAG" "$GITHUB_SHA"', "duplicate-rehearsal-setup"),
        _m("rehearsal tag setup receives a mismatched source", "release-rehearsal.yml", "  package:\n", '--source-sha "$GITHUB_SHA"',
           '--source-sha "$GITHUB_REF"', "required-command-not-executed"),
        _m("rehearsal tag setup loses its local-only flag", "release-rehearsal.yml", "  package:\n", '"$REHEARSAL_TAG" --local-tag', '"$REHEARSAL_TAG"',
           "required-command-not-executed"),
        _m("rehearsal aggregate judge root is not explicit", "release-rehearsal.yml", "  aggregate:\n", " --judge . --subject .", " --subject .",
           "required-command-not-executed"),
        _m("rehearsal aggregate evidence collection replaced by echo", "release-rehearsal.yml", "  aggregate:\n",
           "bash .github/scripts/produce-release-evidence.sh collect", "echo bash .github/scripts/produce-release-evidence.sh collect",
           "required-command-not-executed"),
        _m("release corpus drops the shared subject check", "release.yml", "  candidate-corpus:\n", "bash .github/scripts/produce-release-evidence.sh verify-subject",
           "true bash .github/scripts/produce-release-evidence.sh verify-subject", "required-command-not-executed"),
        _m("release performance subject check source mismatch", "release.yml", "  candidate-performance:\n", '--source-sha "$SOURCE_SHA"',
           '--source-sha "$RELEASE_TAG"', "required-command-not-executed"),
        ("producer script publishes with gh", "script", [("", "cmd_corpus_build() {\n", "cmd_corpus_build() {\n  gh release upload v0.0.0 x\n")],
         "producer-write-command"),
        ("producer script pushes the rehearsal tag", "script", [("", 'git -C "$subject" tag -f', 'git -C "$subject" push origin tag -f')],
         "producer-write-command"),
        ("producer script reads the job token", "script", [("", "set -euo pipefail\n", "set -euo pipefail\ntoken=$GH_TOKEN\n")],
         "producer-token"),
        ("producer script is not fail-fast", "script", [("", "set -euo pipefail\n", "set -u\n")], "producer-script-failfast"),
        ("producer script loses its source-binding check", "script", [("", 'same_commit "$head" "$source_sha"', 'true same_commit "$head" "$source_sha"')],
         "required-command-not-executed"),
        # Retry recovery is decided from live state before any retry write (P15-09).
        _m("release publisher recovery decision replaced by echo", "release.yml", "  publish-qualified-release:\n",
           "bash trusted/.github/scripts/verify-release-gates.sh --check-recovery", "echo bash trusted/.github/scripts/verify-release-gates.sh --check-recovery",
           "required-command-not-executed"),
        _m("release publisher recovery taken from the subject checkout", "release.yml", "  publish-qualified-release:\n",
           "bash trusted/.github/scripts/verify-release-gates.sh --check-recovery", "bash .github/scripts/verify-release-gates.sh --check-recovery",
           "subject-judge-execution"),
        _m("release publisher recovery loses the run attempt", "release.yml", "  publish-qualified-release:\n",
           ' "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" full >', ' "$GITHUB_RUN_ID" full >', "required-command-not-executed"),
        _m("release publisher recovery swallows its failure", "release.yml", "  publish-qualified-release:\n",
           '"$GITHUB_RUN_ATTEMPT" full > "$RUNNER_TEMP/recovery-decision.txt"', '"$GITHUB_RUN_ATTEMPT" full > "$RUNNER_TEMP/recovery-decision.txt" || true',
           "required-command-not-executed"),
        ("release publisher inventory is built after the recovery decision", "release.yml", [
            ("  publish-qualified-release:\n", _PUBLISH_INVENTORY, "true"),
            ("  publish-qualified-release:\n", '> "$RUNNER_TEMP/recovery-decision.txt"', '> "$RUNNER_TEMP/recovery-decision.txt"\n{I}' + _PUBLISH_INVENTORY)],
         "recovery-order"),
        _m("release publisher published-asset readback removed", "release.yml", "  publish-qualified-release:\n",
           'python3 -I trusted/.github/scripts/verify-published-release-assets.py "$assets" build/release-final/api-assets.json',
           'true "$assets" build/release-final/api-assets.json', "required-command-not-executed"),
        _m("release attacher recovery decision replaced by echo", "release.yml", "  attach-v02-evidence:\n",
           "bash trusted/.github/scripts/verify-release-gates.sh --check-recovery", "echo bash trusted/.github/scripts/verify-release-gates.sh --check-recovery",
           "required-command-not-executed"),
        _m("release attacher recovery loses the subset scope", "release.yml", "  attach-v02-evidence:\n",
           ' "$GITHUB_RUN_ATTEMPT" subset >', ' "$GITHUB_RUN_ATTEMPT" >', "required-command-not-executed"),
        ("release attacher uploads evidence before it decides recovery", "release.yml", [
            ("  attach-v02-evidence:\n", _ATTACH_INVENTORY, "true"),
            ("  attach-v02-evidence:\n", '> "$RUNNER_TEMP/recovery-decision.txt"', '> "$RUNNER_TEMP/recovery-decision.txt"\n{I}' + _ATTACH_INVENTORY)],
         "recovery-order"),
        _m("release attacher recovery judge checkout points at the tag", "release.yml", "  attach-v02-evidence:\n", "          ref: ${{ github.sha }}\n          path: trusted",
           "          ref: ${{ env.SOURCE_SHA }}\n          path: trusted", "judge-trust"),
        # Bounded artifact downloads (P15-13).
        _m("release candidate downloads the source archive with curl", "release.yml", "  candidate:\n", "python3 -I \"$RUNNER_TEMP/download-release-artifact.py\"",
           "curl --fail --output \"$archive\" # ", "unbounded-download"),
        _m("release candidate download loses its byte cap", "release.yml", "  candidate:\n", " --max-bytes 1073741824 --total-timeout 600", " --total-timeout 600",
           "required-command-not-executed"),
        _m("release candidate download helper replaced by echo", "release.yml", "  candidate:\n", 'python3 -I "$RUNNER_TEMP/download-release-artifact.py"',
           'echo python3 -I "$RUNNER_TEMP/download-release-artifact.py"', "required-command-not-executed"),
        _m("release manifest download loses its time bound", "release.yml", "  candidate-platform-manifest:\n", " --max-bytes 1073741824 --total-timeout 600",
           " --max-bytes 1073741824", "required-command-not-executed"),
        _m("release manifest download helper taken from the subject checkout", "release.yml", "  candidate-platform-manifest:\n",
           "python3 -I trusted/.github/scripts/download-release-artifact.py", "python3 -I .github/scripts/download-release-artifact.py", "subject-judge-execution"),
        _m("release manifest downloads with wget", "release.yml", "  candidate-platform-manifest:\n",
           'python3 -I trusted/.github/scripts/download-release-artifact.py "https://github.com/$GH_REPO/archive/refs/tags/$RELEASE_TAG.tar.gz" "$RUNNER_TEMP/source-archive.tar.gz" --max-bytes 1073741824 --total-timeout 600',
           'wget -O "$RUNNER_TEMP/source-archive.tar.gz" "https://github.com/$GH_REPO/archive/refs/tags/$RELEASE_TAG.tar.gz"', "unbounded-download"),
        _m("windows downloaded consumer behavior no longer verified", "release.yml", "  candidate-windows:\n", "-P cmake/VerifyInstalledPackage.cmake",
           "-P cmake/Renamed.cmake", "required-command-not-executed"),
        _m("macos downloaded player smoke commented out", "release.yml", "  candidate-macos:\n",
           'GBB_VERIFIED_OUTPUT_DIR="$RUNNER_TEMP/release-player-downloaded" bash',
           '# GBB_VERIFIED_OUTPUT_DIR="$RUNNER_TEMP/release-player-downloaded" bash', "required-command-not-executed"),
        # Residual write jobs: no persisted credential, no job-wide token, trusted verifier overlay (WR-01).
        _m("windows residual checkout persists credentials", rel, "  candidate-windows:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("windows residual job env holds the write token", rel, "  candidate-windows:\n", "    env:\n",
           "    env:\n      GH_TOKEN: ${{ github.token }}\n", "token-scope"),
        _m("windows residual build step holds the write token", rel, "  candidate-windows:\n",
           "      - name: Build and package Windows x64 core once\n        if: env.REUSE_WINDOWS_CANDIDATE != 'true'\n",
           "      - name: Build and package Windows x64 core once\n        if: env.REUSE_WINDOWS_CANDIDATE != 'true'\n        env:\n          GH_TOKEN: ${{ github.token }}\n",
           "token-subject-execution"),
        _m("windows residual trusted verifier overlay removed", rel, "  candidate-windows:\n",
           'git show "${GITHUB_SHA}:tests/scripts/verify-release-candidate.sh" > tests/scripts/verify-release-candidate.sh',
           "true", "trusted-verifier-overlay"),
        ("windows residual overlay runs only in the step that first uses the verifier", rel, [
            ("  candidate-windows:\n", 'git show "${GITHUB_SHA}:tests/scripts/verify-release-candidate.sh" > tests/scripts/verify-release-candidate.sh', "true"),
            ("  candidate-windows:\n", 'git show "${GITHUB_SHA}:tests/scripts/verify-v02-consumers.py" > tests/scripts/verify-v02-consumers.py', "true"),
            ("  candidate-windows:\n", "bash tests/scripts/verify-release-candidate.sh --extract",
             'git show "${GITHUB_SHA}:tests/scripts/verify-release-candidate.sh" > tests/scripts/verify-release-candidate.sh\n{I}git show "${GITHUB_SHA}:tests/scripts/verify-v02-consumers.py" > tests/scripts/verify-v02-consumers.py\n{I}bash tests/scripts/verify-release-candidate.sh --extract')],
         "trusted-verifier-overlay"),
        _m("candidate residual checkout persists credentials", rel, "  candidate:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("candidate residual job env holds the write token", rel, "  candidate:\n", "    env:\n",
           "    env:\n      GH_TOKEN: ${{ github.token }}\n", "token-scope"),
        _m("candidate residual cache-free build step holds the write token", rel, "  candidate:\n",
           "      - name: Configure and build cache-free release core\n        if: env.CANDIDATE_REUSED != 'true'\n        env:\n",
           "      - name: Configure and build cache-free release core\n        if: env.CANDIDATE_REUSED != 'true'\n        env:\n          GH_TOKEN: ${{ github.token }}\n",
           "token-subject-execution"),
        _m("candidate residual tokened step runs the consumer verifier", rel, "  candidate:\n",
           "      - name: Prove downloaded relocated C and C++ consumer behavior\n        env:\n",
           "      - name: Prove downloaded relocated C and C++ consumer behavior\n        env:\n          GH_TOKEN: ${{ github.token }}\n",
           "token-subject-execution"),
        _m("candidate residual trusted verifier overlay removed", rel, "  candidate:\n",
           'git show "${GITHUB_SHA}:tests/scripts/verify-v02-source-archive.py" > tests/scripts/verify-v02-source-archive.py',
           "true", "trusted-verifier-overlay"),
        _m("candidate residual overlay omits the consumer verifier", rel, "  candidate:\n",
           'git show "${GITHUB_SHA}:tests/scripts/verify-v02-consumers.py" > tests/scripts/verify-v02-consumers.py',
           "true", "trusted-verifier-overlay"),
        _m("macos residual checkout persists credentials", rel, "  candidate-macos:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("macos residual job env holds the write token", rel, "  candidate-macos:\n", "    env:\n",
           "    env:\n      GH_TOKEN: ${{ github.token }}\n", "token-scope"),
        _m("macos residual smoke step holds the write token", rel, "  candidate-macos:\n",
           "      - name: Smoke the downloaded player archive and relocated C/C++ consumers\n",
           "      - name: Smoke the downloaded player archive and relocated C/C++ consumers\n        env:\n          GH_TOKEN: ${{ github.token }}\n",
           "token-subject-execution"),
        _m("macos residual trusted verifier overlay removed", rel, "  candidate-macos:\n",
           'git show "${GITHUB_SHA}:tests/scripts/verify-release-candidate.sh" > tests/scripts/verify-release-candidate.sh',
           "true", "trusted-verifier-overlay"),
        _m("macos residual overlay omits only the consumer verifier", rel, "  candidate-macos:\n",
           'git show "${GITHUB_SHA}:tests/scripts/verify-v02-consumers.py" > tests/scripts/verify-v02-consumers.py',
           "true", "trusted-verifier-overlay"),
        _m("platform manifest exempt job gains a token step running tagged scripts", rel, "  candidate-platform-manifest:\n",
           "    steps:\n", "    steps:\n      - name: Run a tagged script\n        run: python3 -I tests/scripts/verify-v02-consumers.py\n",
           "token-subject-execution"),
        # The tokened-step command judge (GR-WR-03a): every head, nested ones included, in the five residual-role jobs.
        *_token_step_mutations(),
        # Overlay first use is matched by basename and read fail-closed up to the last overlay step (GR-WR-03b); the
        # inserted lines sit in untokened steps, so only the overlay rule can refuse them.
        _m("candidate verifier called through cd and a bare file name before the overlay", rel, "Load trusted control-plane receipt verifier",
           "set -euo pipefail", "set -euo pipefail\n{I}cd tests/scripts && bash verify-release-candidate.sh", "trusted-verifier-overlay"),
        _m("candidate verifier called through a variable directory before the overlay", rel, "Load trusted control-plane receipt verifier",
           "set -euo pipefail", 'set -euo pipefail\n{I}bash "$SCRIPTS/verify-release-candidate.sh"', "trusted-verifier-overlay"),
        _m("windows verifier hidden behind an unreadable (( )) line before the overlay", rel, "Verify checked out source version",
           "set -euo pipefail", "set -euo pipefail\n{I}(( 1 ))\n{I}bash tests/scripts/verify-release-candidate.sh --extract build/x build/y", "trusted-verifier-overlay"),
        _m("windows verifier hidden in a bare subshell before the overlay", rel, "Verify checked out source version",
           "set -euo pipefail", "set -euo pipefail\n{I}( bash tests/scripts/verify-release-candidate.sh --extract build/x build/y )", "trusted-verifier-overlay"),
        # Guard expressions are compared exactly after normalisation (GR-WR-03c).
        _m("macOS build reuse guard weakened with || true", rel, "Build and package macOS arm64 core once",
           "if: env.REUSE_MACOS_CANDIDATE != 'true'\n", "if: env.REUSE_MACOS_CANDIDATE != 'true' || true\n", "release-presence"),
        _m("candidate job guard rewritten as always() || ...", rel, "  candidate:\n",
           "if: ${{ always() && ((inputs.retry == true) || (needs.release.result == 'success' && needs.release.outputs.release_created == 'true')) }}",
           "if: ${{ always() || needs.release.outputs.release_created == 'true' }}", "release-presence"),
        _m("platform manifest checkout persists credentials", rel, "  candidate-platform-manifest:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("release source-version comparison interpolates a step output into its run body", "release.yml",
           "Configure and build cache-free release core", '"$RELEASE_VERSION_OUT" ]]', '"${{ steps.identity.outputs.version }}" ]]', "run-expression"),
        _m("release ctest step interpolates the run nonce into its run body", "release.yml",
           "Run the full CTest stream once", '${RUN_NONCE}.xml"', '${{ steps.corpus_run.outputs.run_nonce }}.xml"', "run-expression"),
        _m("ci native-linux checkout persists credentials", "ci.yml", "  native-linux:\n",
           "          persist-credentials: false\n", "", "checkout-credentials"),
        _m("preview installed-package-smoke checkout persists credentials", "preview.yml", "  installed-package-smoke-linux-x64:\n",
           "          persist-credentials: false\n", "", "checkout-credentials"),
        _m("ci campaign status no longer asserted", "ci.yml", "  linux-sanitizers:\n", 'test "$verify_status" -eq 0', 'echo test "$verify_status" -eq 0', "required-command-not-executed"),
        _m("ci campaign verifier removed", "ci.yml", "  linux-sanitizers:\n", "python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan/v02-fuzz-receipt.json\n            verify_status=$?",
           "true\n            verify_status=$?", "required-command-not-executed"),
        # Release-candidate wiring formerly pinned as text in verify-release-candidate.sh (WR-06, W6-03..W6-11).
        _m("W6-03 release-please action unpinned", rel, "", "googleapis/release-please-action@45996ed1f6d02564a971a2fa1b5860e934307cf7",
           "googleapis/release-please-action@v5", "workflow-unpinned-action"),
        _m("W6-04 candidate drops gh pr checks", rel, "  candidate:\n", 'required=$(gh pr checks "$pr_number" --required --json name,bucket)',
           "required='[]'", "release-presence"),
        _m("W6-04b candidate drops the tag-to-source comparison input", rel, "  candidate:\n", 'api_commit=$(gh api "repos/$GH_REPO/commits/$RELEASE_TAG" --jq \'.sha\')',
           "api_commit=$SOURCE_SHA", "release-presence"),
        _m("W6-04c candidate drops the merged-PR lookup", rel, "  candidate:\n", 'prs=$(gh api "repos/$GH_REPO/commits/$SOURCE_SHA/pulls")',
           "prs='[]'", "release-presence"),
        _m("W6-04d candidate stops requiring release_created", rel, "  candidate:\n", " && needs.release.outputs.release_created == 'true'",
           "", "release-presence"),
        _m("W6-04e candidate loses its retry input", rel, "  candidate:\n", "      RETRY: ${{ inputs.retry }}\n", "", "release-presence"),
        _m("W6-05a candidate-macos runner changed", rel, "  candidate-macos:\n", "runs-on: macos-14", "runs-on: macos-latest", "runner-image"),
        _m("W6-05b candidate-windows runner changed", rel, "  candidate-windows:\n", "runs-on: windows-2022", "runs-on: windows-latest", "runner-image"),
        _m("W6-06 windows archive name changed in the extract call", rel, "  candidate-windows:\n",
           "bash tests/scripts/verify-release-candidate.sh --extract build/downloaded/gabbaboy-core-windows-x64.tar.gz",
           "bash tests/scripts/verify-release-candidate.sh --extract build/downloaded/gabbaboy-core-windows-arm64.tar.gz", "required-command-not-executed"),
        _m("W6-07 platform manifest name changed", rel, "  candidate-platform-manifest:\n",
           'gh release upload "$RELEASE_TAG" build/candidate-platform-manifest.json', 'gh release upload "$RELEASE_TAG" build/candidate-renamed-manifest.json',
           "release-presence"),
        _m("W6-07b macOS preview archive name changed in the player download", rel, "  candidate-macos:\n",
           'gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern gabbaboy-preview-macos-arm64.tar.gz',
           'gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern gabbaboy-preview-renamed.tar.gz', "release-presence"),
        _m("W6-08 verify-package call neutered", rel, "  candidate-macos:\n",
           "bash tests/scripts/verify-phase3-player.sh --verify-package build/downloaded-player",
           "bash tests/scripts/verify-phase3-player.sh --help build/downloaded-player", "required-command-not-executed"),
        _m("W6-09 windows generator changed", rel, "  candidate-windows:\n", '-G "Visual Studio 17 2022"', '-G "Ninja"', "release-presence"),
        _m("W6-11a macOS build step loses its reuse guard", rel, "  candidate-macos:\n",
           "      - name: Build and package macOS arm64 core once\n        if: env.REUSE_MACOS_CANDIDATE != 'true'\n",
           "      - name: Build and package macOS arm64 core once\n", "release-presence"),
        _m("W6-11b windows refusal message removed", rel, "  candidate-windows:\n",
           'echo "Draft contains a partial Windows candidate asset set; refusing to rebuild or replace bytes." >&2',
           'echo "Draft contains a partial Windows candidate asset set; continuing." >&2', "release-presence"),
        # Release-candidate wiring formerly pinned as text in verify-release-candidate.sh (WR-06, W6-12..W6-19).
        _m("W6-12 windows no longer needs macOS", rel, "  candidate-windows:\n", "needs: [release, candidate-macos]", "needs: [release]", "workflow-dependency"),
        _m("W6-14 release gains pull_request_target", rel, "", "  workflow_call:\n", "  pull_request_target:\n    branches: [main]\n  workflow_call:\n", "workflow-trigger"),
        ("W6-15 final gate moved after publish", rel, [
            ("  publish-qualified-release:\n", 'run: bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"', "run: true"),
            ("  publish-qualified-release:\n", 'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag',
             'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag\n{I}bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"')],
         "publication-order"),
        _m("W6-16 published asset verifier neutered", rel, "  publish-qualified-release:\n",
           'python3 -I trusted/.github/scripts/verify-published-release-assets.py "$assets" build/release-final/api-assets.json',
           'python3 -I trusted/.github/scripts/verify-published-release-assets.py --help "$assets" build/release-final/api-assets.json',
           "required-command-not-executed"),
        _m("W6-19 entrypoint stops calling release.yml", "release-please.yml", "", "uses: ./.github/workflows/release.yml",
           "uses: ./.github/workflows/release-renamed.yml", "release-entrypoint"),
    ]


def self_test(root: Path) -> None:
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="gbb-workflow-policy.") as directory:
        fixture = Path(directory) / "subject"
        work = Path(directory) / "work"
        work.mkdir()
        _copy_fixture(root, fixture)
        positive = _run_cli(fixture, work)
        if positive.returncode != 0 or "PASS: workflow privilege and trust wiring" not in positive.stdout:
            raise SystemExit(f"self-test positive control failed: exit={positive.returncode} stderr={positive.stderr.strip()!r}")
        baselines = {item: (fixture / ".github/workflows" / item).read_text(encoding="utf-8") for item in WORKFLOWS}
        baselines["script"] = (fixture / PRODUCER_SCRIPT).read_text(encoding="utf-8")

        def target(workflow: str) -> Path:
            return fixture / (PRODUCER_SCRIPT if workflow == "script" else f".github/workflows/{workflow}")

        for label, workflow, edits, expected in _mutations():
            text = baselines[workflow]
            for after, old, replacement in edits:
                split = text.find(after) if after else 0
                position = text.find(old, split) if split >= 0 else -1
                if position < 0:
                    raise SystemExit(f"self-test anchor missing for {label!r} in {workflow}: {old[:60]!r}")
                line_start = text.rfind("\n", 0, position) + 1
                indent = text[line_start:len(text[line_start:]) - len(text[line_start:].lstrip(" ")) + line_start]
                text = text[:position] + replacement.replace("{I}", indent) + text[position + len(old):]
            path = target(workflow)
            path.write_text(text, encoding="utf-8")
            result = _run_cli(fixture, work)
            diagnostic = result.stderr.strip()
            if result.returncode != 1 or f"REJECT {expected}:" not in diagnostic or "PASS:" in result.stdout:
                raise SystemExit(f"self-test negative {label!r} failed: want REJECT {expected}, exit={result.returncode}, "
                                 f"stdout={result.stdout!r}, stderr={diagnostic!r}")
            rejected += 1
            print(f"rejected: {label}: {diagnostic}")
            path.write_text(baselines[workflow], encoding="utf-8")
        # Equivalent shell formatting of a required call stays valid: continuation, quoting, extra spaces,
        # interleaved comments and blank lines do not change what runs.
        path = fixture / ".github/workflows/release-rehearsal.yml"
        accepted = 0
        for variant in (
            "python3  -I \\\n{I}  trusted-judge/.github/scripts/verify-workflow-policy.py \\\n{I}  --check --root subject",
            'python3 -I "trusted-judge/.github/scripts/verify-workflow-policy.py" --check --root \'subject\'',
            "# the judge\n{I}\n{I}python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject  # trailing",
        ):
            text = baselines["release-rehearsal.yml"]
            position = text.find(JUDGE_CALL, text.find("  judge:\n"))
            line_start = text.rfind("\n", 0, position) + 1
            indent = " " * (position - line_start)
            path.write_text(text[:position] + variant.replace("{I}", indent) + text[position + len(JUDGE_CALL):], encoding="utf-8")
            result = _run_cli(fixture, work)
            if result.returncode != 0 or "PASS:" not in result.stdout:
                raise SystemExit(f"self-test equivalent formatting {variant!r} was rejected: {result.stderr.strip()!r}")
            accepted += 1
        path.write_text(baselines["release-rehearsal.yml"], encoding="utf-8")
        # A subject that ships its own judge, and shadows standard-library modules, cannot change the verdict:
        # the trusted script ignores the subject tree except as workflow text.
        bad = baselines["release-rehearsal.yml"].replace("permissions:\n  contents: read\n", "permissions:\n  contents: write\n", 1)
        (fixture / ".github/workflows/release-rehearsal.yml").write_text(bad, encoding="utf-8")
        hostile = fixture / ".github/scripts/verify-workflow-policy.py"
        hostile.parent.mkdir(parents=True, exist_ok=True)
        hostile.write_text("print('PASS: workflow privilege and trust wiring')\nraise SystemExit(0)\n", encoding="utf-8")
        (fixture / "re.py").write_text("raise SystemExit('subject re.py executed')\n", encoding="utf-8")
        (fixture / "pathlib.py").write_text("raise SystemExit('subject pathlib.py executed')\n", encoding="utf-8")
        result = _run_cli(fixture, fixture)
        if result.returncode != 1 or "REJECT workflow-permissions:" not in result.stderr or "PASS:" in result.stdout:
            raise SystemExit(f"self-test hostile subject judge was not ignored: exit={result.returncode} stderr={result.stderr.strip()!r}")
        rejected += 1
        print("rejected: subject-supplied judge and shadowed modules cannot approve a mutated workflow")
        # Residual classification is data, so it is attacked in-process: a job in both sets, then a job in neither.
        for label, kwargs in (
            ("residual job listed in both the subject set and the exemption map", {"exempt": {**TOKEN_SCOPE_EXEMPT, "candidate": "claimed exempt"}}),
            ("residual job missing from both sets", {"subject": tuple(job for job in RESIDUAL_SUBJECT_JOBS if job != "candidate")}),
            ("exempt job without a reason", {"exempt": {**TOKEN_SCOPE_EXEMPT, "publish-qualified-release": " "}}),
        ):
            try:
                _check_residual_classification(**kwargs)
            except Reject as exc:
                if exc.code != "residual-classification":
                    raise SystemExit(f"self-test negative {label!r} failed: wrong code {exc.code}")
                rejected += 1
                print(f"rejected: {label}: {exc}")
            else:
                raise SystemExit(f"self-test negative {label!r} failed: accepted")
        # The credential exemption is data too: a stale job name and a reasonless entry are both rejected.
        for label, exempt in (
            ("credential exemption names a job that does not exist", {("ci.yml", "no-such-job"): "claimed"}),
            ("credential exemption without a reason", {("ci.yml", "native-linux"): " "}),
        ):
            try:
                check_readonly_workflows(root, exempt)
            except Reject as exc:
                if exc.code != "checkout-credentials":
                    raise SystemExit(f"self-test negative {label!r} failed: wrong code {exc.code}")
                rejected += 1
                print(f"rejected: {label}: {exc}")
            else:
                raise SystemExit(f"self-test negative {label!r} failed: accepted")
    print(f"PASS: workflow policy self-test negative_controls={rejected} positive_controls={1 + accepted}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="judge the workflow files under --root")
    modes.add_argument("--self-test", action="store_true", help="run positive and intended-defect controls through the CLI")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="tree whose .github/workflows files are judged as data")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.self_test:
            self_test(root)
            return 0
        facts = check_all(root)
        print(f"PASS: workflow privilege and trust wiring residual_write_jobs={facts['residual']}")
        return 0
    except Reject as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
