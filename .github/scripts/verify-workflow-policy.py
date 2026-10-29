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
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
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


# Release reuses a successful rehearsal receipt for the exact tag tree. Paired wall-clock timing itself is advisory,
# so rehearsal producer jobs have no decision input or tokened measurement-fetch step.
PERFORMANCE_TOKEN_STEPS = {
    ("release", "candidate-performance"): "Fetch the newest successful rehearsal run's performance receipt for this tag",
}
_GH_READ = re.compile(r"gh\s+run\s+(?:view|download|list)\b")
# The two read-only listings the rehearsal-reuse selection judges (WR-01): the rehearsal workflow's successful runs on this tag's
# branch, and one run's artifacts. Any other `gh api` form, method flag or path stays a repository-write/API command.
_GH_API_READ = re.compile(r'gh\s+api\s+"repos/\$GITHUB_REPOSITORY/actions/(?:workflows/release-rehearsal\.yml/runs\?[A-Za-z0-9_=&/$]+'
                          r'|runs/\$run_id/artifacts\?per_page=100)"')


def _gh_reads(text: str, replacement: str) -> str:
    return _GH_API_READ.sub(replacement, _GH_READ.sub(replacement, text))


def _check_unprivileged(workflow: str, tree: dict, job_id: str) -> None:
    """A producer runs subject code with a read-only job token and no token it could use or leak."""
    job = tree["jobs"][job_id]
    token_step = PERFORMANCE_TOKEN_STEPS.get((workflow, job_id))
    perms = _permissions(job, tree.get("permissions", {}))
    if _writes(perms):
        raise Reject("producer-write-authority", f"{_where(workflow, job_id)} runs producer work with write authority")
    allowed = {"contents": "read", "actions": "read"} if token_step else {"contents": "read"}
    if token_step and perms != allowed:
        raise Reject("producer-permissions", f"{_where(workflow, job_id)} must hold exactly contents: read and actions: read")
    if "permissions" in job and perms != allowed:
        raise Reject("producer-permissions", f"{_where(workflow, job_id)} must hold only contents: read")
    scanned = {k: v for k, v in job.items() if k != "name"}
    steps = [dict(step) for step in job.get("steps", [])]
    if token_step:
        holders = [step for step in steps if step.get("name") == token_step]
        if len(holders) != 1 or holders[0].get("env", {}).get("GH_TOKEN") != "${{ github.token }}":
            raise Reject("producer-token", f"{_where(workflow, job_id)} step {token_step!r} must be the one step holding GH_TOKEN: ${{{{ github.token }}}}")
        holder = holders[0]
        holder["env"] = {key: value for key, value in holder["env"].items() if key != "GH_TOKEN"}
        if _TOKEN.search(str(holder.get("run", ""))) or SUBJECT_EXECUTION.search(_gh_reads(str(holder.get("run", "")), "")):
            raise Reject("producer-token", f"{_where(workflow, job_id)} step {token_step!r} runs tagged-tree code while holding the token")
        holder["run"] = _gh_reads(str(holder.get("run", "")), "gh-read")
        scanned = {k: (steps if k == "steps" else v) for k, v in scanned.items()}
    if any(_TOKEN.search(text) for text in _strings(scanned)):
        raise Reject("producer-token", f"{_where(workflow, job_id)} references the job token or a secret")
    if any(_WRITE_COMMAND.search(step.get("run", "")) for step in steps):
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
    "candidate-fuzz": ("release-evidence-fuzz", ("build/ci-fuzz/v02-fuzz-receipt.json",
                                                   "build/ci-fuzz/perf-gate/perf-gate-receipt.json",
                                                   "build/ci-fuzz/perf-gate-run.json")),
}
SUBJECT_REF = "${{ env.SOURCE_SHA }}"
JUDGE_CALL_POLICY = "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject --release-head --git-root trusted-judge"
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
# The rehearsal tag is derived from the rehearsal/vX.Y.Z ref and the tree's own version, never a fixed default (D-28).
_DERIVE_TAG = 'python3 -I tests/scripts/verify-support-ledger.py --derive-rehearsal-tag "$GITHUB_REF_NAME"'
_REHEARSAL_TAG = _SHARED + ' verify-subject --subject . --source-sha "$GITHUB_SHA" --tag "$REHEARSAL_TAG" --local-tag'
_RELEASE_SUBJECT = _SHARED + ' verify-subject --subject . --source-sha "$SOURCE_SHA" --tag "$RELEASE_TAG"'
_CORPUS_BUILD = _SHARED + " corpus-build --subject ."
_LEDGER_BASE = 'python3 -I tests/scripts/verify-support-ledger.py --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --receipt build/cgb-corpus-receipt.json'
# The hosted cumulative performance gate (Phase 16, D-14..D-16): the gate itself and both seeded controls.
PERF_GATE_COMMANDS = (
    "bash tests/scripts/run-perf-gate.sh --gate",
    "bash tests/scripts/run-perf-gate.sh --seeded-regression",
    "bash tests/scripts/run-perf-gate.sh --noop-twin",
    # RM-030: the release gate controls (eight owner-approval and six nightly mutants plus the extras) run beside the gate.
    'python3 -I tests/scripts/verify-release-gates.py --self-test --rev "$GITHUB_SHA"',
)
PERFORMANCE_MEASURE = "bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json"
PERFORMANCE_UPLOAD = "rehearsal-performance-${{ github.run_id }}-${{ github.run_attempt }}"
REHEARSAL_REQUIRED = {
    "perf-gate": PERF_GATE_COMMANDS,
    "corpus": (
        _DERIVE_TAG,
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
        _DERIVE_TAG,
        _REHEARSAL_TAG,
        'bash tests/scripts/verify-release-candidate.sh --extract build/gabbaboy-core-linux-x64.tar.gz "$RUNNER_TEMP/v02-extracted"',
        'python3 -I tests/scripts/verify-v02-consumers.py --write-candidate-manifest "$RUNNER_TEMP/candidate-manifest.json" --archive build/gabbaboy-core-linux-x64.tar.gz --source-sha "$SOURCE_SHA" --build-receipt build/release/CMakeCache.txt',
        'python3 -I tests/scripts/verify-v02-consumers.py --prefix "$RUNNER_TEMP/v02-extracted" --archive build/gabbaboy-core-linux-x64.tar.gz --candidate-manifest "$RUNNER_TEMP/candidate-manifest.json" --output build/v02-consumer-receipt.json',
        'python3 -I tests/scripts/verify-v02-source-archive.py --archive "$archive" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo . --output build/source-archive-receipt.json',
        'python3 -I tests/scripts/verify-v02-source-archive.py --check-receipt build/source-archive-receipt.json --archive "$archive" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo .',
    ),
    "aggregate": (
        _DERIVE_TAG,
        _REHEARSAL_TAG,
        _CORPUS_BUILD,
        _SHARED + " collect --subject . --output build/evidence",
        _SHARED + ' verify --judge . --subject . --source-sha "$SOURCE_SHA" --tag "$RELEASE_TAG" --evidence build/evidence --archive "$RUNNER_TEMP/source-archive.tar.gz" --rehearsal',
        "python3 -I tests/scripts/verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json",
        "GBB_BUILD_DIR=build-asan bash tests/scripts/run-bounded-fuzz.sh --explore --receipt build-asan/v02-fuzz-receipt.json",
        "python3 -I tests/scripts/verify-v02-fuzz.py --verify build-asan/v02-fuzz-receipt.json",
        "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json",
    ),
    "judge": (
        JUDGE_CALL_POLICY,
        'python3 -I trusted-judge/tests/scripts/verify-v02-fuzz.py --verify-source rehearsal-evidence/v02-fuzz-receipt.json --source-sha "$GITHUB_SHA"',
        'python3 -I trusted-judge/tests/scripts/verify-support-ledger.py --derive-rehearsal-tag "$GITHUB_REF_NAME" --root subject',
    ),
}
# RM-030 (D-22): the exact-tree nightly ASan replay gate runs from the trusted revision, bound to the tagged source, after the
# final downloaded-byte gate and before the one publication transition.
NIGHTLY_GATE_CALL = ('python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate --runs-json "$RUNNER_TEMP/nightly-runs.json" '
                     '--run-json "$RUNNER_TEMP/nightly-run.json" --head "$head" --rev "$SOURCE_SHA" --branch "rehearsal/$RELEASE_TAG" '
                     '--output "$RUNNER_TEMP/nightly-gate-receipt.json"')
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
        'gh api "repos/$GH_REPO/actions/runs/$run_id" > build/ci-fuzz/perf-gate-run.json',
        'gh run download "$run_id" --repo "$GH_REPO" --name "perf-gate-$run_id-$attempt" --dir build/ci-fuzz/perf-gate',
        'python3 -I tests/scripts/verify-perf-gate.py --verify-receipt build/ci-fuzz/perf-gate/perf-gate-receipt.json --source-sha "$SOURCE_SHA" --run-json build/ci-fuzz/perf-gate-run.json --run-id "$run_id" --attempt "$attempt" --repo .',
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
STATE_PIN_NATIVE_JOBS = {
    "native-linux": ("linux-x64", "state-pins-linux"),
    "native-macos": ("macos-arm64", "state-pins-macos"),
    "native-windows": ("windows-x64", "state-pins-windows"),
}
STATE_PIN_TEST_COMMAND = "ctest --test-dir build -R '^state_portable_pins$' --output-on-failure --no-tests=error"
# The state pin base step body, pinned byte for byte (17-REVIEW WR-C02): a substring check let an inserted
# `base=$(git rev-parse HEAD)` keep every token while the ratchet compared HEAD with itself. A push parent that is all
# zeros or no longer reachable (a rebase or force-push, WR-C05) falls back to the merge base with origin/main, as the
# budget base step does; anything else that does not resolve fails the step.
STATE_PIN_BASE_RUN = (
    'if [ "$EVENT_NAME" = "pull_request" ]; then\n'
    '  base="$PR_BASE"\n'
    '  test -n "$base"\n'
    'elif [ "$EVENT_NAME" = "push" ]; then\n'
    '  base="$PUSH_BEFORE"\n'
    '  test -n "$base"\n'
    '  if [ -z "${base//0/}" ] || ! git cat-file -e "${base}^{commit}"; then\n'
    '    base=$(git merge-base HEAD origin/main)\n'
    '  fi\n'
    'else\n'
    '  echo "Unsupported CI event for immutable state pin base: $EVENT_NAME" >&2\n'
    '  exit 1\n'
    'fi\n'
    'git cat-file -e "${base}^{commit}"\n'
    'echo "base=$base" >> "$GITHUB_OUTPUT"'
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
    'git show "$BUDGET_BASE:tests/scripts/verify-test-budget.py" > "$RUNNER_TEMP/verify-test-budget.py"',
    'python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --base "$BUDGET_BASE" --repo "$GITHUB_WORKSPACE"',
    'python3 -I tests/scripts/verify-test-budget.py --self-test',
)
# The budget base falls back to the merge base with origin/main when the push parent is all-zero or no longer a
# reachable commit (rebased and force-pushed branch), and still fails closed on an unresolvable final base.
CI_BUDGET_BASE_PINS = (
    '! git cat-file -e "${base}^{commit}"',
    'base=$(git merge-base HEAD origin/main)',
    'git cat-file -e "${base}^{commit}"\n',
)
# Every job the planning-only classification may skip (D-21): each needs `changes` and runs only for kind == 'full'.
CI_HEAVY_JOBS = ("native-linux", "native-macos", "native-windows", "linux-sanitizers", "linux-sanitizers-tests",
                 "linux-sanitizers-acceptance", "cmake-floor-3-25-3", "perf-gate", "player-gate", "macos-player-package")
CI_FULL_CONDITION = "needs.changes.outputs.kind == 'full'"
CI_REQUIRED_NATIVE_NEEDS = set(CI_HEAVY_JOBS) | {"changes", "planning-checks"}
# The classifier is the copy stored at the base commit, so a change cannot loosen the rule that judges it. A base
# that has no copy, cannot be resolved or has an all-zero parent classifies as full (D-21).
CI_CLASSIFIER_PINS = (
    'if [ -z "${base//0/}" ] || ! git cat-file -e "${base}^{commit}"; then',
    'elif git show "$base:.github/scripts/classify-changes.py" > "$RUNNER_TEMP/classify-changes.py"; then',
    'python3 -I "$RUNNER_TEMP/classify-changes.py" --base "$base" --head "$GITHUB_SHA" --ref "$GITHUB_REF"',
    'if [ "$verdict" = "kind=planning" ]; then',
)
CI_PLANNING_COMMANDS = (
    "cmake --preset phase1 -DGBB_TEST_INSTALL_PREFIX=",
    "ctest --test-dir build -L planning --no-tests=error --output-on-failure",
)
CI_AGGREGATOR_ENV = {
    "KIND": "${{ needs.changes.outputs.kind }}",
    "CHANGES": "${{ needs.changes.result }}",
    "PLANNING_CHECKS": "${{ needs.planning-checks.result }}",
}


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


def _flat(step: dict) -> str:
    return " ".join(str(step.get("run", "")).split())


def _check_performance_qualification(workflow: str, job: dict, job_id: str) -> None:
    if workflow != "release-rehearsal" or job_id not in ("performance", "aggregate"):
        raise Reject("performance-advisory-path", f"unexpected advisory performance job {workflow}.{job_id}")
    steps = job.get("steps", [])
    flattened = " ".join(_flat(step) for step in steps)
    if any(token in flattened for token in ("--apply-decision", "performance_decision", "measurement_run_id",
                                           "pending-investigation")):
        raise Reject("performance-advisory-path", f"{_where(workflow, job_id)} routes ordinary timing through review approval")
    measures = [step for step in steps if PERFORMANCE_MEASURE in _flat(step)]
    verify_command = "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json"
    verifies = [step for step in steps if verify_command in _flat(step)]
    valid_order = len(measures) == 1 and len(verifies) == 1
    if valid_order:
        measure_step, verify_step = measures[0], verifies[0]
        valid_order = steps.index(measure_step) <= steps.index(verify_step)
        if valid_order and measure_step is verify_step:
            valid_order = _flat(measure_step).index(PERFORMANCE_MEASURE) < _flat(verify_step).index(verify_command)
    if not valid_order:
        raise Reject("performance-advisory-path", f"{_where(workflow, job_id)} must measure and verify one advisory receipt unconditionally")
    if job_id == "performance":
        uploads = [step for step in _artifact_steps(job, "upload") if step.get("with", {}).get("name") == PERFORMANCE_UPLOAD]
        if len(uploads) != 1 or str(uploads[0].get("if", "")).strip() not in ("always()", "${{ always() }}") \
                or uploads[0]["with"].get("path") != "build/v02-performance-receipt.json":
            raise Reject("artifact-flow", f"{_where(workflow, job_id)} must retain the advisory receipt with if: always()")


def _check_release_performance_consumer(job: dict) -> None:
    steps = job.get("steps", [])
    flattened = " ".join(_flat(step) for step in steps)
    if "--apply-decision" in flattened or "performance_decision" in flattened or "pending-investigation" in flattened:
        raise Reject("performance-advisory-path", "release candidate-performance routes ordinary timing through review approval")
    consumer = [step for step in steps if "--verify build/v02-performance-receipt.json" in _flat(step)]
    if len(consumer) != 1:
        raise Reject("performance-advisory-consumer", "release candidate-performance must verify the final advisory receipt")
    producer = [step for step in steps if PERFORMANCE_MEASURE in _flat(step)]
    reuse = [step for step in steps if "--verify-reuse" in _flat(step)]
    if len(producer) != 1 or len(reuse) != 1 or producer[0] is not reuse[0] or \
            steps.index(consumer[0]) < steps.index(reuse[0]):
        raise Reject("performance-advisory-consumer", "release candidate-performance must verify either the exact-tree reused receipt or a measured advisory receipt")


def _check_performance_reuse(workflow: str, job: dict) -> None:
    """release.yml reuses a rehearsal receipt only through --verify-reuse with the tag's tree, from a successful rehearsal run of this tag."""
    steps = job.get("steps", [])
    fetch = [step for step in steps if step.get("name") == PERFORMANCE_TOKEN_STEPS[(workflow, "candidate-performance")]]
    run = _flat(fetch[0]) if len(fetch) == 1 else ""
    judge = '"$RUNNER_TEMP/verify-release-source-proof.py"'
    for pin in ('git show "${GITHUB_SHA}:.github/scripts/verify-release-source-proof.py" > ' + judge,
                "release-rehearsal.yml/runs?branch=rehearsal/$RELEASE_TAG&status=success",
                f"if run_id=$(python3 -I {judge} --select-performance-run ",
                '--tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo "$GITHUB_REPOSITORY" --selected-run ',
                "actions/runs/$run_id/artifacts?per_page=100",
                f"if artifact=$(python3 -I {judge} --select-performance-artifact ",
                'gh run download "$run_id"', '--name "$artifact"'):
        if pin not in run:
            raise Reject("performance-reuse-unbound", f"{_where(workflow, 'candidate-performance')} must fetch only the validated artifact of a successful rehearsal run of this tag, judged by the trusted revision: {pin}")
    if re.search(r"python3?\s+(?:-\w+\s+)*\.?/?\.github/scripts/verify-release-source-proof\.py|\|\|\s*true", run):
        raise Reject("performance-reuse-unbound", f"{_where(workflow, 'candidate-performance')} must not judge reuse with the tagged tree's copy or swallow a refusal")
    reuse = [step for step in steps if "--verify-reuse" in _flat(step)]
    if len(reuse) != 1 or '--tag-tree "$tag_tree"' not in _flat(reuse[0]) or 'tag_tree=$(git rev-parse "$SOURCE_SHA^{tree}")' not in _flat(reuse[0]) \
            or reuse[0].get("env", {}).get("GH_TOKEN"):
        raise Reject("performance-reuse-unbound", f"{_where(workflow, 'candidate-performance')} must reuse a rehearsal receipt only through --verify-reuse with the tag's tree")


REHEARSAL_FETCH_STEP_NAME = "Fetch the rehearsal run and its attempt jobs for binding"
REHEARSAL_BIND_STEP_NAME = "Bind the exact-tag rehearsal to the version PR head"
REHEARSAL_BIND_COMMAND = ('python3 -I "$RUNNER_TEMP/verify-release-source-proof.py" --bind-rehearsal-run '
                          '"$RUNNER_TEMP/rehearsal-runs.json" --tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" '
                          '--repo "$GH_REPO" --selected-run "$RUNNER_TEMP/rehearsal-run.json" '
                          '--pr-head "$PR_HEAD_SHA" --merged-at "$PR_MERGED_AT" '
                          '--attempt-jobs "$RUNNER_TEMP/rehearsal-attempt-jobs.json"')


def _check_candidate_rehearsal_binding(workflow: str, job: dict) -> None:
    steps = job.get("steps", [])
    proofs = [step for step in steps if step.get("name") == "Verify merged PR exact-head required evidence"]
    fetches = [step for step in steps if step.get("name") == REHEARSAL_FETCH_STEP_NAME]
    bindings = [step for step in steps if step.get("name") == REHEARSAL_BIND_STEP_NAME]
    if (len(proofs) != 1 or len(fetches) != 1 or len(bindings) != 1
            or steps.index(fetches[0]) != steps.index(proofs[0]) + 1
            or steps.index(bindings[0]) != steps.index(fetches[0]) + 1):
        raise Reject("rehearsal-binding-order", "release candidate must bind rehearsal immediately after the merged PR proof")
    proof_text = proofs[0].get("run", "")
    if ("merged_at=$(jq -r '.merged_at' <<<\"$pr\")" not in proof_text
            or "merged_at=%s\\n" not in proof_text):
        raise Reject("rehearsal-binding-unbound", "release candidate must output the server-recorded merged_at of its exact PR")
    fetch = fetches[0]
    fetch_text = fetch.get("run", "")
    fetch_pins = (
        "actions/workflows/release-rehearsal.yml/runs?branch=rehearsal/$RELEASE_TAG&status=success&per_page=100",
        'actions/runs/$run_id/attempts/$attempt/jobs?per_page=100',
        'max_by(.id)',
    )
    if fetch.get("env", {}).get("GH_TOKEN") != "${{ github.token }}" or any(pin not in fetch_text for pin in fetch_pins):
        raise Reject("rehearsal-binding-unbound", "release candidate must fetch the newest rehearsal and its selected attempt jobs")
    bind = bindings[0]
    if bind.get("env", {}).get("PR_HEAD_SHA") != "${{ steps.proof.outputs.head_sha }}" \
            or bind.get("env", {}).get("PR_MERGED_AT") != "${{ steps.proof.outputs.merged_at }}" \
            or bind.get("env", {}).get("GH_TOKEN"):
        raise Reject("rehearsal-binding-unbound", "release candidate must bind the proof step's PR head and merged_at outputs")
    text = bind.get("run", "")
    pins = (
        'git show "${GITHUB_SHA}:.github/scripts/verify-release-source-proof.py" > "$RUNNER_TEMP/verify-release-source-proof.py"',
    )
    if any(pin not in text for pin in pins) or "set -euo pipefail" not in text or "|| true" in text:
        raise Reject("rehearsal-binding-unbound", "release candidate must fetch and judge the newest rehearsal and its attempt jobs without a fallback")
    require_call(workflow, "candidate", {"steps": [bind]}, REHEARSAL_BIND_COMMAND)


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
    dispatch = tree.get("on", {}).get("workflow_dispatch", {})
    inputs = dispatch.get("inputs", {}) if isinstance(dispatch, dict) else {}
    if isinstance(inputs, dict) and {"performance_decision", "measurement_run_id"} & set(inputs):
        raise Reject("performance-advisory-path", "release rehearsal must not expose ordinary timing decision inputs")
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
    judge_steps = judge.get("steps", [])
    tag_guard = judge_steps[0] if judge_steps else {}
    tag_guard_run = tag_guard.get("run", "")
    required_tag_guard = (
        'TAG="${GITHUB_REF_NAME#rehearsal/}"',
        'if [[ "$TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]; then',
        'git ls-remote --tags "https://github.com/$GITHUB_REPOSITORY" "refs/tags/$TAG"',
        'Tag $TAG already exists; a rehearsal after the tag cannot bind a release.',
        'if [[ -n "$tag_ref" ]]; then',
        "exit 1",
    )
    if tag_guard.get("name") != "Refuse rehearsal after its release tag exists" \
            or any(pin not in tag_guard_run for pin in required_tag_guard) or not _runs_under_errexit(tag_guard):
        raise Reject("rehearsal-tag-exists", "the rehearsal judge must first refuse a release-shaped branch whose tag already exists")
    checkouts = {step.get("with", {}).get("path"): step.get("with", {}) for step in _checkouts(judge)}
    if set(checkouts) != {"trusted-judge", "subject"}:
        raise Reject("judge-trust", f"{_where(name, 'judge')} needs one trusted-judge checkout and one subject-data checkout")
    if checkouts["trusted-judge"].get("ref") != DEFAULT_BRANCH_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} judge code must come from the default branch, not the rehearsed subject")
    if checkouts["trusted-judge"].get("fetch-depth") not in (0, "0"):
        raise Reject("judge-history-shallow", f"{_where(name, 'judge')} trusted-judge checkout must use fetch-depth: 0 for release-head object checks")
    if checkouts["subject"].get("ref", TRUSTED_SHA_REF) != TRUSTED_SHA_REF:
        raise Reject("judge-trust", f"{_where(name, 'judge')} subject data must be the rehearsed commit")
    _download(judge, name, "judge", REHEARSAL_FUZZ_ARTIFACT)
    for step in judge.get("steps", []):
        if re.search(r"(?:^|[\s=\"'])\.?/?subject/", step.get("run", "")):
            raise Reject("judge-subject-execution", f"{_where(name, 'judge')} names a path inside the subject tree; subject files are data only")
    for job_id, commands in REHEARSAL_REQUIRED.items():
        for command in commands:
            require_call(name, job_id, tree["jobs"][job_id], command)
    for job_id in ("performance", "aggregate"):
        _check_performance_qualification(name, tree["jobs"][job_id], job_id)


# Read-only workflows must not leave the checkout token in .git/config for later steps (IN-08). A job that truly
# needs the persisted credential is listed here as (workflow file, job id) -> reason; none does today, because the
# jobs authenticate gh through an explicit step-level token and fetch only public sources.
READONLY_WORKFLOWS = ("ci.yml", "fixture-repro.yml", "preview.yml", "perf-attribution.yml", "libbet-repro.yml")
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


# preview.yml player smoke vs the planning-only lane (D-21): a kind=planning exact-head CI run skips
# macos-player-package, so the wait excuses exactly that skip (and only for a planning run, which the wait reads from the
# run's own job results) and the three download/verify/upload steps are skipped when the wait reports kind=planning.
# `!= 'planning'` keeps the steps running (and failing on the missing run id) whenever the kind output is absent.
PREVIEW_PLAYER_JOB = "player-package-smoke-macos"
PREVIEW_PLAYER_WAIT_PINS = (
    "--require required-native --require macos-player-package",
    "--planning-skippable macos-player-package --deadline-seconds",
)
PREVIEW_PLAYER_GUARD = "steps.candidate.outputs.kind != 'planning'"
PREVIEW_PLAYER_GUARDED_STEPS = (
    "Download run-scoped candidate package",
    "Verify downloaded package bytes and create consumer receipt",
    "Upload qualified macOS player preview and receipt",
)


def check_preview_player_lane(root: Path) -> None:
    workflow = "preview.yml"
    tree = read_workflow(root / ".github/workflows" / workflow)
    job = _require_job(workflow, tree, PREVIEW_PLAYER_JOB)
    steps = job.get("steps", [])
    waits = [step for step in steps if step.get("id") == "candidate"]
    run = " ".join(str(waits[0].get("run", "")).split()) if len(waits) == 1 else ""
    for pin in PREVIEW_PLAYER_WAIT_PINS:
        if pin not in run:
            raise Reject("preview-player-lane", f"{_where(workflow, PREVIEW_PLAYER_JOB)} wait step must contain: {pin}")
    if run.count("--planning-skippable") != 1 or run.count("--require") != 2:
        raise Reject("preview-player-lane", f"{_where(workflow, PREVIEW_PLAYER_JOB)} may excuse only macos-player-package, with both jobs required")
    for name in PREVIEW_PLAYER_GUARDED_STEPS:
        named = [step for step in steps if step.get("name") == name]
        if len(named) != 1 or _normalise_if(named[0].get("if", "")) != PREVIEW_PLAYER_GUARD:
            raise Reject("preview-player-lane", f"{_where(workflow, PREVIEW_PLAYER_JOB)} step {name!r} must run only when {PREVIEW_PLAYER_GUARD}")


def _check_ci_planning_lane(workflow: str, tree: dict) -> None:
    """The planning-only lane (D-21): a read-only classifier on the base commit's copy, a real planning-checks job, and
    the full-matrix condition on every heavy job. required-native itself is judged by check_ci."""
    if "pull_request_target" in _trigger_names(tree):
        raise Reject("workflow-trigger", f"{workflow} must not use pull_request_target")
    changes = _require_job(workflow, tree, "changes")
    if _permissions(changes, tree["permissions"]) != {"contents": "read"}:
        raise Reject("producer-write-authority", "ci.changes must hold only contents: read")
    if changes.get("outputs", {}).get("kind") != "${{ steps.classify.outputs.kind }}":
        raise Reject("planning-lane", "ci.changes must publish kind from its classify step")
    classify = [step for step in changes.get("steps", []) if step.get("id") == "classify"]
    run = str(classify[0].get("run", "")) if len(classify) == 1 else ""
    for pin in CI_CLASSIFIER_PINS:
        if pin not in run:
            raise Reject("classifier-source", f"ci.changes classify step must contain: {pin}")
    checkout = _checkouts(changes)
    if len(checkout) != 1 or str(checkout[0].get("with", {}).get("fetch-depth")) != "0":
        raise Reject("planning-lane", "ci.changes must check out the full history so the base commit can be read")
    lane = _require_job(workflow, tree, "planning-checks")
    if _needs(lane) != {"changes"} or _normalise_if(lane.get("if", "")) != "needs.changes.outputs.kind == 'planning'":
        raise Reject("planning-lane", "ci.planning-checks must need changes and run only for kind == 'planning'")
    if _permissions(lane, tree["permissions"]) != {"contents": "read"}:
        raise Reject("producer-write-authority", "ci.planning-checks must hold only contents: read")
    for command in CI_PLANNING_COMMANDS:
        require_call(workflow, "planning-checks", lane, command)
    for job_id in CI_HEAVY_JOBS:
        job = _require_job(workflow, tree, job_id)
        clauses = [clause.strip() for clause in _normalise_if(job.get("if", "")).split("&&")]
        if "changes" not in _needs(job) or CI_FULL_CONDITION not in clauses:
            raise Reject("planning-lane-condition", f"ci.{job_id} must need changes and run only if {CI_FULL_CONDITION}")


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
    for var, expression in CI_AGGREGATOR_ENV.items():
        if expression not in [step.get("env", {}).get(var) for step in gate.get("steps", [])]:
            raise Reject("workflow-dependency", f"ci.required-native must pass {var}: {expression}")
    require_call(name, "required-native", gate, "python3 -I .github/scripts/check-required-native.py")
    require_call(name, "required-native", gate, 'bash .github/scripts/check-player-result.sh "$PLAYER_GATE" "$PLAYER_REQUIRED" "$PLAYER_RESULT"',
                 conditional=True)
    _check_ci_planning_lane(name, tree)
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
    require_call(name, "perf-gate", perf_job, "python3 -I tests/scripts/verify-perf-gate.py --self-test-receipt")
    _upload(perf_job, name, "perf-gate", "perf-gate-${{ github.run_id }}-${{ github.run_attempt }}",
            ("build/perf-gate-receipt.json",), retain_on_failure=True)
    gate_at = require_call(name, "perf-gate", perf_job, PERF_GATE_COMMANDS[0])
    seeded_at = require_call(name, "perf-gate", perf_job, "bash tests/scripts/run-perf-gate.sh --seeded-regression")
    receipt_uploads = [step for step in _artifact_steps(perf_job, "upload")
                       if step.get("with", {}).get("name") == "perf-gate-${{ github.run_id }}-${{ github.run_attempt }}"]
    if len(receipt_uploads) != 1 or receipt_uploads[0].get("if") != "always()":
        raise Reject("artifact-flow", "ci.perf-gate must retain its same-run receipt on pass or failure")
    upload_at = perf_job["steps"].index(receipt_uploads[0])
    if not gate_at[0] < upload_at < seeded_at[0]:
        raise Reject("artifact-flow", "ci.perf-gate must retain its receipt after the deciding gate and before seeded controls")
    for shard, commands in CI_SANITIZER_SHARDS.items():
        shard_job = _require_job(name, tree, shard)
        for command in commands:
            require_call(name, shard, shard_job, command)
    for command, var, conditional in CI_STATUS_CALLS:
        require_call(name, "linux-sanitizers", job, command, conditional=conditional, errexit_off=True, status_var=var)
    _check_state_pin_native_jobs(root, tree)


def _check_state_pin_native_jobs(root: Path, tree: dict) -> None:
    """Require immutable-base state pins and installed package consumers on each existing native OS lane."""
    workflow = "ci"
    expected_path = root / "tests/expected-tests.txt"
    try:
        expected_tests = set(expected_path.read_text(encoding="utf-8").splitlines())
    except OSError as error:
        raise Reject("state-pin-inventory", "tests/expected-tests.txt is unavailable") from error
    required_inventory = {"state_portable_pins", "state_pin_controls", "installed_consumer_c",
                          "installed_consumer_cpp", "preview_package_smoke"}
    if not required_inventory <= expected_tests:
        raise Reject("state-pin-inventory", "expected test inventory omits a state pin control or installed consumer")

    for job_id, (platform, artifact_prefix) in STATE_PIN_NATIVE_JOBS.items():
        job = _require_job(workflow, tree, job_id)
        checkout = _checkouts(job)
        if len(checkout) != 1 or str(checkout[0].get("with", {}).get("fetch-depth")) != "0":
            raise Reject("state-pin-base", f"ci.{job_id} must fetch full history for an immutable PR/push base")
        base_steps = [step for step in job.get("steps", []) if step.get("id") == "state_pin_base"]
        if len(base_steps) != 1:
            raise Reject("state-pin-base", f"ci.{job_id} must resolve exactly one immutable state pin base")
        base_step = base_steps[0]
        base_env = base_step.get("env", {})
        base_run = str(base_step.get("run", ""))
        for key, expression in (("EVENT_NAME", "${{ github.event_name }}"),
                                ("PR_BASE", "${{ github.event.pull_request.base.sha }}"),
                                ("PUSH_BEFORE", "${{ github.event.before }}")):
            if base_env.get(key) != expression:
                raise Reject("state-pin-base", f"ci.{job_id} state pin base must read the immutable PR/push event SHA")
        if base_run.strip("\n") != STATE_PIN_BASE_RUN or set(base_env) != {"EVENT_NAME", "PR_BASE", "PUSH_BEFORE"} or \
                set(base_step) - {"name", "id", "shell", "env", "run"} or base_step.get("shell", "bash") != "bash":
            raise Reject("state-pin-base", f"ci.{job_id} state pin base must be exactly the pinned event-base resolution")
        configure = [step for step in job.get("steps", []) if step.get("name") == "Configure"]
        if len(configure) != 1 or configure[0].get("env", {}).get("STATE_PIN_BASE") != \
                "${{ steps.state_pin_base.outputs.base }}":
            raise Reject("state-pin-base", f"ci.{job_id} Configure must consume the resolved immutable base")
        configure_run = str(configure[0].get("run", ""))
        if job_id == "native-windows":
            base_arg = '-DGBB_STATE_PIN_BASE_REV="$env:STATE_PIN_BASE"'
        else:
            base_arg = '-DGBB_STATE_PIN_BASE_REV="$STATE_PIN_BASE"'
        if base_arg not in configure_run:
            raise Reject("state-pin-base", f"ci.{job_id} Configure must pass the event base into the pin ratchet")

        pin_steps = [step for step in job.get("steps", [])
                     if step.get("name") == "Run state pins against the immutable event base"]
        if len(pin_steps) != 1 or STATE_PIN_TEST_COMMAND not in str(pin_steps[0].get("run", "")):
            raise Reject("state-pin-target", f"ci.{job_id} must execute the compiled state_portable_pins target")
        pin_env = pin_steps[0].get("env", {})
        if pin_env.get("GBB_STATE_PIN_RECEIPT") != "${{ github.workspace }}/build/state-pin-receipt.json" or \
                pin_env.get("GBB_STATE_PLATFORM") != platform:
            raise Reject("state-pin-receipt", f"ci.{job_id} must write a path-free, platform-labelled pin receipt")
        require_call(workflow, job_id, job, STATE_PIN_TEST_COMMAND)

        uploads = [step for step in _artifact_steps(job, "upload")
                   if str(step.get("with", {}).get("name", "")).startswith(artifact_prefix + "-")]
        if len(uploads) != 1:
            raise Reject("state-pin-receipt", f"ci.{job_id} must retain exactly one platform pin receipt")
        upload = uploads[0]
        details = upload.get("with", {})
        if upload.get("if") != "always()" or details.get("path") != "build/state-pin-receipt.json" or \
                details.get("if-no-files-found") != "error" or str(details.get("retention-days")) != "7" or \
                "${{ github.run_id }}" not in details.get("name", "") or \
                "${{ github.run_attempt }}" not in details.get("name", ""):
            raise Reject("state-pin-receipt", f"ci.{job_id} pin receipt artifact must be run-scoped and retained")

        require_call(workflow, job_id, job, "cmake --install build --prefix build/package-prefix")
        require_call(workflow, job_id, job, "ctest --test-dir build")
        require_call(workflow, job_id, job, "bash .github/scripts/verify-test-inventory.sh",
                     contains=("tests/expected-tests.txt", "--installed"),
                     allow_always=(job_id == "native-linux"))


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


# The red report (IN-03). The replay is skipped by the dry run, which runs the same reporting body with every write replaced by a
# recorded line; the open issue is reused only on an exact title AND the label, never on a title phrase.
NIGHTLY_REPLAY_IF = "${{ !inputs.report_red_dry_run }}"
NIGHTLY_REPORT_IF = "${{ failure() || (always() && inputs.report_red_dry_run) }}"
NIGHTLY_ISSUE_TITLE = "nightly-red: asan-full-replay"
NIGHTLY_ISSUE_LABEL = "nightly-red"
NIGHTLY_DRY_RUN_ENV = "${{ inputs.report_red_dry_run && 'true' || 'false' }}"
NIGHTLY_DEDUPE_FILTER = "[.[] | select(.title == env.ISSUE_TITLE and any(.labels[]; .name == env.ISSUE_LABEL))]"
NIGHTLY_REPORT_STEP_TIMEOUT_MAX = 5
_NIGHTLY_BARE_WRITE = re.compile(r"(?m)^\s*(?:gh\s+(?:issue\s+(?:create|comment|edit|close|reopen)|label\s+(?:create|edit|delete))\b)")


def _check_nightly_report(job: dict) -> None:
    where = "nightly-asan.report-red"
    if _needs(job) != {"asan-full-replay"} or str(job.get("if", "")).strip() != NIGHTLY_REPORT_IF:
        raise Reject("nightly-report-trigger", f"{where} must need asan-full-replay and run only if: {NIGHTLY_REPORT_IF}")
    if job.get("permissions") != {"issues": "write"}:
        raise Reject("nightly-report-permissions", f"{where} must hold issues: write as its only permission")
    if _checkouts(job) or any("uses" in step for step in job.get("steps", [])):
        raise Reject("nightly-report-checkout", f"{where} must not check out source or use any action")
    # The job's own timeout needs a ledger row citing a completed report-red run, and none exists until the dry run has been
    # dispatched on a pushed head (the job has only ever been skipped). Until then the bound is the reporting step's; once the
    # row is cited, the job-level timeout-minutes and its ledger row are judged by check_timeout_ledger like any other job.
    steps = job.get("steps", [])
    if len(steps) != 1:
        raise Reject("nightly-report-body", f"{where} must hold exactly the one reporting step")
    step = steps[0]
    minutes = str(step.get("timeout-minutes", ""))
    if not minutes.isdigit() or not 1 <= int(minutes) <= NIGHTLY_REPORT_STEP_TIMEOUT_MAX:
        raise Reject("nightly-report-timeout", f"{where} reporting step needs a timeout-minutes of at most {NIGHTLY_REPORT_STEP_TIMEOUT_MAX}")
    env = step.get("env", {})
    if env.get("ISSUE_TITLE") != NIGHTLY_ISSUE_TITLE or env.get("ISSUE_LABEL") != NIGHTLY_ISSUE_LABEL \
            or env.get("DRY_RUN") != NIGHTLY_DRY_RUN_ENV:
        raise Reject("nightly-report-body", f"{where} must pass the exact title, the label and the dry-run flag through env")
    run = str(step.get("run", ""))
    flat = _flat(step)
    if NIGHTLY_DEDUPE_FILTER not in run or 'gh issue list --state open --label "$ISSUE_LABEL" --limit 100 ' not in run \
            or "--search" in run or "in:title" in run:
        raise Reject("nightly-report-dedupe", f"{where} must find the open issue by exact title and label, not by a title phrase search")
    if 'issue_write issue create --title "$ISSUE_TITLE" --label "$ISSUE_LABEL"' not in run \
            or 'issue_write issue comment "$number"' not in run or "issue_write label create" not in run:
        raise Reject("nightly-report-dedupe", f"{where} must create the issue with the label, comment on a match and create the label when it is missing")
    if 'if [ "$DRY_RUN" = true ]; then' not in run or "DRY-RUN not sent" not in run or 'gh "$@"' not in run:
        raise Reject("nightly-report-dry-run", f"{where} must route every write through issue_write, which only records it in a dry run")
    if _NIGHTLY_BARE_WRITE.search(run.replace('gh "$@"', "")) or re.search(r"\|\|\s*true", flat) \
            or str(step.get("continue-on-error", "false")).lower() not in ("", "false"):
        raise Reject("nightly-report-dry-run", f"{where} writes to GitHub outside issue_write or ignores a failure")


def check_nightly(root: Path) -> None:
    """The scheduled full ASan stall replay (D-19, D-108): two triggers, a read-only replay job that runs the repository
    code, and a separate report job that alone holds issues: write, has no checkout and runs no repository code (T-16-07)."""
    name = "nightly-asan"
    tree = read_workflow(root / ".github/workflows/nightly-asan.yml")
    if _trigger_names(tree) != {"schedule", "workflow_dispatch"}:
        raise Reject("workflow-trigger", "nightly-asan must trigger on schedule and workflow_dispatch only")
    dispatch = tree["on"].get("workflow_dispatch") if isinstance(tree.get("on"), dict) else None
    inputs = dispatch.get("inputs") if isinstance(dispatch, dict) else None
    if not isinstance(inputs, dict) or set(inputs) != {"report_red_dry_run"} or not isinstance(inputs["report_red_dry_run"], dict) \
            or inputs["report_red_dry_run"].get("type") != "boolean" or str(inputs["report_red_dry_run"].get("default")) != "false":
        raise Reject("workflow-trigger", "nightly-asan workflow_dispatch may take only the boolean report_red_dry_run input, default false")
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
    if str(replay.get("if", "")).strip() != NIGHTLY_REPLAY_IF:
        raise Reject("nightly-replay-trigger", f"nightly-asan.asan-full-replay may be skipped only by the dry run: if: {NIGHTLY_REPLAY_IF}")
    for command in NIGHTLY_COMMANDS:
        require_call(name, "asan-full-replay", replay, command)
    _check_nightly_report(tree["jobs"]["report-red"])


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


# --------------------------------------------------------------------------- release lifecycle script (RM-028, D-20)
# The attach, manifest, final-gate and publication steps of release.yml are bodies of .github/scripts/release-evidence-lifecycle.sh,
# so the production workflow and the local replay run the same commands. The judge therefore reads each step that calls the
# script as if its body were inline: every rule below (command reachability, order, trusted-judge paths, token scope) keeps
# judging the exact text that runs. A mode that is not called, called from the wrong job, called with a path outside the trusted
# checkout, or defined twice is rejected, so extracted code can never be unused or substituted.
LIFECYCLE_SCRIPT = ".github/scripts/release-evidence-lifecycle.sh"
LIFECYCLE_MODES = {
    "attach-evidence": "attach-v02-evidence",
    "validate-evidence": "candidate-platform-manifest",
    "build-manifest": "candidate-platform-manifest",
    "validate-draft": "publish-qualified-release",
    "final-gate": "publish-qualified-release",
    "nightly-gate": "publish-qualified-release",
    "publish-draft": "publish-qualified-release",
}
_LIFECYCLE_CALL = re.compile(r"^bash trusted/\.github/scripts/release-evidence-lifecycle\.sh ([a-z-]+)$")


def lifecycle_regions(text: str) -> dict[str, str]:
    """The verbatim body of every mode: the lines between its BEGIN and END markers, each defined exactly once."""
    regions: dict[str, str] = {}
    for mode in LIFECYCLE_MODES:
        begin, end = f"\n# BEGIN {mode}\n", f"\n# END {mode}\n"
        if text.count(begin) != 1 or text.count(end) != 1 or text.find(begin) > text.find(end):
            raise Reject("lifecycle-wiring", f"{LIFECYCLE_SCRIPT} must define the mode {mode} exactly once between its BEGIN and END markers")
        function = f"\nlifecycle_{mode.replace('-', '_')}() {{{begin}"
        if text.count(function) != 1:
            raise Reject("lifecycle-wiring", f"{LIFECYCLE_SCRIPT} mode {mode} must be the body of its own function")
        if f"\n  {mode}) lifecycle_{mode.replace('-', '_')} ;;\n" not in text:
            raise Reject("lifecycle-wiring", f"{LIFECYCLE_SCRIPT} does not dispatch the mode {mode} to its function")
        regions[mode] = text[text.find(begin) + len(begin):text.find(end)]
    _check_lifecycle_skeleton(text)
    return regions


# WR-C02: the script outside the regions is a pinned skeleton. Without it a function override (`python3() { return 0; }`),
# a `trap 'exit 0' ERR`, or an extra first `case` arm (`nightly-gate) exit 0 ;;`, which bash takes before the real one)
# kept every region and dispatch line intact while the gates never ran. Comment and blank lines are free.
LIFECYCLE_USAGE_ARM = ("  *) printf 'usage: release-evidence-lifecycle.sh " + "|".join(LIFECYCLE_MODES) +
                       "\\n' >&2; exit 2 ;;")


def _check_lifecycle_skeleton(text: str) -> None:
    outside = text
    for mode in LIFECYCLE_MODES:
        begin, end = f"\n# BEGIN {mode}\n", f"\n# END {mode}\n"
        start, stop = outside.find(begin), outside.find(end)
        outside = outside[:start + 1] + outside[stop + len(end):]
    lines = [line.rstrip() for line in outside.split("\n") if line.strip() and not line.lstrip().startswith("#")]
    functions = [f"lifecycle_{mode.replace('-', '_')}" for mode in LIFECYCLE_MODES]
    expected = ["set -euo pipefail"]
    for function in functions:
        expected += [f"{function}() {{", "}"]
    expected.append('case "${1:-}" in')
    expected += [f"  {mode}) {function} ;;" for mode, function in zip(LIFECYCLE_MODES, functions)]
    expected += [LIFECYCLE_USAGE_ARM, "esac"]
    if lines != expected:
        first = next((index for index, (got, want) in enumerate(zip(lines, expected)) if got != want), min(len(lines), len(expected)))
        got = lines[first] if first < len(lines) else "<end of script>"
        want = expected[first] if first < len(expected) else "<end of script>"
        raise Reject("lifecycle-wiring", f"{LIFECYCLE_SCRIPT} outside its mode regions must be the pinned skeleton: "
                     f"found {got[:80]!r} where {want[:80]!r} belongs")


def expand_lifecycle(workflow: str, tree: dict, root: Path) -> None:
    path = root / LIFECYCLE_SCRIPT
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject("lifecycle-wiring", f"{workflow} calls {LIFECYCLE_SCRIPT}, which cannot be read: {exc.strerror}") from exc
    regions = lifecycle_regions(text)
    called: dict[str, str] = {}
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            run = str(step.get("run", "")).strip()
            if "release-evidence-lifecycle.sh" not in run:
                continue
            match = _LIFECYCLE_CALL.fullmatch(run)
            if not match or match.group(1) not in LIFECYCLE_MODES:
                raise Reject("lifecycle-wiring", f"{_where(workflow, job_id)} must call the lifecycle script exactly as "
                             "'bash trusted/.github/scripts/release-evidence-lifecycle.sh MODE' with a known mode")
            mode = match.group(1)
            if LIFECYCLE_MODES[mode] != job_id or mode in called:
                raise Reject("lifecycle-wiring", f"{_where(workflow, job_id)} must not call the lifecycle mode {mode}: "
                             f"it belongs to {LIFECYCLE_MODES[mode]} and runs once")
            called[mode] = job_id
            step["run"] = regions[mode]
    missing = sorted(set(LIFECYCLE_MODES) - set(called))
    if missing:
        raise Reject("lifecycle-wiring", f"{workflow} never calls the extracted lifecycle mode(s) {', '.join(missing)}: extracted code must be executed by the workflow")


ATTACH_REUSE_GUARD = 'if [[ "${RETRY:-}" == true ]]; then'
ATTACH_REUSE_DOWNLOAD = 'gh release download "$RELEASE_TAG" --repo "$GH_REPO" --pattern "$name" --dir "$RUNNER_TEMP/attached-$name"'


# IN-01: the attached bytes are judged on their own BEFORE any regenerated copy is replaced. The check reads the attachments
# (downloaded first) and the live asset list; a refusal must leave the regenerated evidence untouched, so it precedes the
# copy that reuses the attachments and the recovery decision.
ATTACH_TAMPER_CHECK = ('bash trusted/.github/scripts/verify-release-gates.sh --check-attached-evidence "$RELEASE_TAG" "$SOURCE_SHA" '
                       '"$RUNNER_TEMP/attached-assets.json" "$RUNNER_TEMP"')
ATTACH_REUSE_COPY = 'cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"'


def _check_attach_reuse(workflow: str, job: dict) -> None:
    """Evidence already attached to the draft replaces regenerated bytes only on a retry, after an independent tamper check
    of the attached bytes and before the recovery decision, and without any write; the downstream owner validators then
    judge those bytes against the tag source."""
    if job.get("env", {}).get("RETRY") != "${{ inputs.retry }}":
        raise Reject("attach-reuse-env", f"{_where(workflow, 'attach-v02-evidence')} RETRY must be the workflow's inputs.retry")
    runs = [step.get("run", "") for step in job.get("steps", []) if "attach evidence without replacing any asset" in step.get("name", "")]
    if len(runs) != 1:
        raise Reject("attach-reuse-unguarded", f"{_where(workflow, 'attach-v02-evidence')} needs exactly one attach step")
    text = runs[0]
    guard, download, decision = text.find(ATTACH_REUSE_GUARD), text.find(ATTACH_REUSE_DOWNLOAD), text.find("--check-recovery")
    if guard < 0 or download < guard or not (guard < decision):
        raise Reject("attach-reuse-unguarded", f"{_where(workflow, 'attach-v02-evidence')} must take attached evidence only inside the retry guard and before the recovery decision")
    block = text[guard:decision]
    if re.search(r"gh release (upload|edit|delete)|gh api[^\n]*(-X|--method)", block):
        raise Reject("attach-reuse-write", f"{_where(workflow, 'attach-v02-evidence')} reuse of attached evidence must not write to the release")
    check, copy = text.find(ATTACH_TAMPER_CHECK), text.find(ATTACH_REUSE_COPY)
    if check < 0 or copy < 0 or text.count(ATTACH_TAMPER_CHECK) != 1 or text.count(ATTACH_REUSE_COPY) != 1:
        raise Reject("attach-tamper-order", f"{_where(workflow, 'attach-v02-evidence')} must judge the attached evidence with --check-attached-evidence "
                     "once and reuse it with one copy")
    if not (guard < download < check < copy < decision):
        raise Reject("attach-tamper-order", f"{_where(workflow, 'attach-v02-evidence')} must download the attached evidence, run the independent "
                     "tamper check, and only then replace the regenerated copies, all before the recovery decision")


def check_release(root: Path) -> None:
    name = "release"
    _check_residual_classification()
    tree = read_workflow(root / ".github/workflows/release.yml")
    expand_lifecycle(name, tree, root)
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
            require_call(name, job_id, jobs[job_id], command, conditional=command == PERFORMANCE_MEASURE and job_id == "candidate-performance")
    _check_performance_reuse(name, jobs["candidate-performance"])
    _check_release_performance_consumer(jobs["candidate-performance"])
    _check_candidate_rehearsal_binding(name, jobs["candidate"])
    window_copy_at = require_call(name, "candidate", jobs["candidate"], VERSION_WINDOW_SOURCE_COPY)
    window_check_at = require_call(name, "candidate", jobs["candidate"], VERSION_WINDOW_SOURCE_CALL)
    if window_copy_at >= window_check_at:
        raise Reject("judge-trust", "release candidate must copy the trusted version-window checker before requiring the active record")
    _check_attach_reuse(name, jobs["attach-v02-evidence"])
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
    nightly_at = require_call(name, "publish-qualified-release", publisher, NIGHTLY_GATE_CALL)
    if not gate_at < nightly_at < publish_at:
        raise Reject("nightly-gate-order", f"{_where(name, 'publish-qualified-release')} must run the nightly ASan replay gate after the final "
                     "downloaded-byte gate and before the one publication transition")
    if _permissions(publisher, tree["permissions"]).get("actions") != "read":
        raise Reject("nightly-gate-permissions", f"{_where(name, 'publish-qualified-release')} needs exactly actions: read to list the nightly runs")
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
    require_call(name, "attach-v02-evidence", attach, ATTACH_TAMPER_CHECK, conditional=True)
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


# --------------------------------------------------------------------------- timeout ledger (D-20)
LEDGER_PATH = ".github/ci-timeouts.json"
LEDGER_WHOLE_RUN_MINUTES = Fraction(30)
LEDGER_NORMAL_FIELDS = frozenset({"timeout_minutes", "cited_run_id", "cited_sha", "p50_minutes", "samples", "provisional"})
LEDGER_NORMAL_OPTIONAL = frozenset({"tree_equal_sha", "cited_tree", "cited_job_name", "disclosure"})
LEDGER_BOUND_FIELDS = frozenset({"timeout_minutes", "release_bound", "provisional", "sizing_basis"})
# D-20 'release-bound ledger row (Phase 16)': no release_bound row remains after RM-027. Keep the narrow legacy whitelist and
# expiry rule so any row reintroduced at VERSION > 0.2.1 is refused; a generic skip is never allowed.
LEDGER_RELEASE_BOUND_KEYS = ("release.yml:attach-v02-evidence", "release.yml:candidate-fuzz", "release-rehearsal.yml:judge",
                             # D-111: the rehearsal producers that cannot pass until the version-bound ledger and the owner-recorded
                             # performance review exist; a provisional row would make the rehearsal judge's own --release-head check circular.
                             "release-rehearsal.yml:corpus", "release-rehearsal.yml:aggregate")
LEDGER_BOUND_LAST_VERSION = (0, 2, 1)
_P50 = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_LEDGER_JOB_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()/-]{0,99}$")
_LEDGER_DISCLOSURE = re.compile(r"^[\x20-\x7e]{1,400}$")


def _ledger_pairs(pairs):
    seen: dict = {}
    for key, value in pairs:
        if key in seen:
            raise Reject("timeout-ledger-schema", f"{LEDGER_PATH} repeats the key {key!r}")
        seen[key] = value
    return seen


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _project_version(root: Path) -> tuple[int, int, int]:
    try:
        text = (root / "CMakeLists.txt").read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject("timeout-ledger-release-bound", f"cannot read CMakeLists.txt to check the release-bound expiry: {exc.strerror}") from exc
    match = re.search(r"project\(\s*\w+\s+VERSION\s+(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        raise Reject("timeout-ledger-release-bound", "CMakeLists.txt has no project VERSION to check the release-bound expiry against")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _run_git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one bounded git query against the explicitly selected object database."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False, timeout=30)


def _workflow_job_block(text: str | None, job_id: str) -> str | None:
    """Return one top-level workflow job block, or None when the workflow/job is absent."""
    if text is None:
        return None
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == f"  {job_id}:"), None)
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip()) <= 2:
            end = index
            break
    return "\n".join(lines[start:end])


def check_ledger_git_objects(ledger, git_root: Path, main_ref: str, release_head: bool,
                             git=_run_git, disclosure_base: str | None = None,
                             workflow_root: Path | None = None) -> None:
    """Prove tree-equal citations against a fixed git object database; optional disclosure checks compare job blocks."""
    anchors = [(key, row) for key, row in ledger.items() if isinstance(row, dict) and "tree_equal_sha" in row]
    if not anchors and not (release_head and any(isinstance(row, dict) and "tree_equal_sha" in row for row in ledger.values())) \
            and disclosure_base is None:
        return

    def run(*args: str, code: str = "timeout-ledger-git-unavailable", key: str | None = None):
        try:
            result = git(*args, cwd=git_root)
        except (OSError, subprocess.SubprocessError) as exc:
            subject = f"{key}: " if key else ""
            raise Reject(code, f"{subject}git {' '.join(args)} failed: {exc}") from exc
        if result.returncode != 0:
            subject = f"{key}: " if key else ""
            detail = result.stderr.strip()[:200] if result.stderr else f"exit {result.returncode}"
            raise Reject(code, f"{subject}git {' '.join(args)} failed: {detail}")
        return result

    resolved_main = None
    if anchors:
        resolved_main = run("rev-parse", "--verify", "--end-of-options", f"{main_ref}^{{commit}}").stdout.strip()
        if not _SHA40.fullmatch(resolved_main):
            raise Reject("timeout-ledger-git-unavailable", f"git did not resolve {main_ref!r} to a commit id")
        for key, row in anchors:
            anchor = row["tree_equal_sha"]
            tree = run("rev-parse", "--verify", "--end-of-options", f"{anchor}^{{tree}}", key=key).stdout.strip()
            if not _SHA40.fullmatch(tree):
                raise Reject("timeout-ledger-git-unavailable", f"{key}: git did not resolve the tree-equal anchor to a tree id")
            if tree != row["cited_tree"]:
                raise Reject("timeout-ledger-tree-mismatch", f"{key}: cited_tree {row['cited_tree']} differs from anchor tree {tree}")
            try:
                ancestor = git("merge-base", "--is-ancestor", anchor, resolved_main, cwd=git_root)
            except (OSError, subprocess.SubprocessError) as exc:
                raise Reject("timeout-ledger-git-unavailable", f"{key}: git merge-base failed: {exc}") from exc
            if ancestor.returncode == 1:
                raise Reject("timeout-ledger-anchor-not-on-main", f"{key}: tree-equal anchor is not an ancestor of {main_ref}")
            if ancestor.returncode != 0:
                detail = ancestor.stderr.strip()[:200] if ancestor.stderr else f"exit {ancestor.returncode}"
                raise Reject("timeout-ledger-git-unavailable", f"{key}: git merge-base --is-ancestor failed: {detail}")

    if release_head:
        for key, row in anchors:
            cited_sha = row["cited_sha"]
            try:
                readable = git("cat-file", "-e", f"{cited_sha}^{{commit}}", cwd=git_root)
                if readable.returncode != 0:
                    detail = readable.stderr.strip()[:200] if readable.stderr else f"exit {readable.returncode}"
                    raise Reject("timeout-ledger-cited-object-missing", f"{key}: cited run head {cited_sha} is unreadable: {detail}")
                cited_tree = git("rev-parse", "--verify", "--end-of-options", f"{cited_sha}^{{tree}}", cwd=git_root)
            except (OSError, subprocess.SubprocessError) as exc:
                raise Reject("timeout-ledger-cited-object-missing", f"{key}: cited run head is unreadable: {exc}") from exc
            if cited_tree.returncode != 0 or not _SHA40.fullmatch(cited_tree.stdout.strip()) \
                    or cited_tree.stdout.strip() != row["cited_tree"]:
                detail = cited_tree.stderr.strip()[:200] if cited_tree.stderr else "cited tree is unreadable or differs"
                raise Reject("timeout-ledger-cited-object-missing", f"{key}: cited run head {cited_sha} is unreadable or has the wrong tree: {detail}")

    if disclosure_base is not None:
        if workflow_root is None:
            workflow_root = git_root
        base_commit = run("rev-parse", "--verify", "--end-of-options", f"{disclosure_base}^{{commit}}").stdout.strip()
        if not _SHA40.fullmatch(base_commit):
            raise Reject("timeout-ledger-git-unavailable", f"git did not resolve disclosure base {disclosure_base!r} to a commit id")

        def workflow_at_commit(path: str) -> str | None:
            listed = run("ls-tree", "-z", "--name-only", base_commit, "--", path)
            if not listed.stdout:
                return None
            shown = run("show", f"{base_commit}:{path}")
            return shown.stdout

        for key, row in ledger.items():
            workflow, separator, job_id = key.partition(":")
            if not separator:
                continue
            relative = f".github/workflows/{workflow}"
            base_text = workflow_at_commit(relative)
            try:
                current_text = (workflow_root / relative).read_text(encoding="utf-8")
            except FileNotFoundError:
                current_text = None
            except OSError as exc:
                raise Reject("timeout-ledger-git-unavailable", f"{key}: cannot read current workflow: {exc.strerror}") from exc
            if _workflow_job_block(base_text, job_id) != _workflow_job_block(current_text, job_id):
                disclosure = row.get("disclosure") if isinstance(row, dict) else None
                if not isinstance(disclosure, str) or "changed this job's body after the cited run" not in disclosure:
                    raise Reject("timeout-ledger-body-undisclosed", f"{key}: changed this job's body after the cited run; add the required disclosure")


def judge_timeout_ledger(ledger, yaml_timeouts: dict[str, int], gating: set[str], version: tuple[int, int, int],
                         release_head: bool) -> None:
    """Judge parsed ledger data against {workflow:job -> YAML timeout}; gating names the jobs behind required-native."""
    if not isinstance(ledger, dict) or not ledger:
        raise Reject("timeout-ledger-schema", f"{LEDGER_PATH} must be a non-empty object of workflow:job rows")
    for key in yaml_timeouts:
        if key not in ledger:
            raise Reject("timeout-ledger-missing-row", f"{key} has timeout-minutes but no row in {LEDGER_PATH}")
    for key in ledger:
        if key not in yaml_timeouts:
            raise Reject("timeout-ledger-stale", f"{LEDGER_PATH} row {key} names a job with no timeout-minutes")
    longest = Fraction(0)
    for key, row in ledger.items():
        if not isinstance(row, dict):
            raise Reject("timeout-ledger-schema", f"{key}: a row must be an object")
        if "release_bound" in row:
            if key not in LEDGER_RELEASE_BOUND_KEYS:
                raise Reject("timeout-ledger-release-bound", f"{key}: release_bound is legal only under {', '.join(LEDGER_RELEASE_BOUND_KEYS)}")
            if version > LEDGER_BOUND_LAST_VERSION:
                raise Reject("timeout-ledger-release-bound",
                             f"{key}: release_bound expired when the project VERSION passed {'.'.join(map(str, LEDGER_BOUND_LAST_VERSION))}; re-cite it from the release run")
            if set(row) != LEDGER_BOUND_FIELDS or row["release_bound"] is not True or row["provisional"] is not False \
                    or not isinstance(row["sizing_basis"], str) or not row["sizing_basis"].strip() or not _is_int(row["timeout_minutes"]):
                raise Reject("timeout-ledger-schema", f"{key}: a release_bound row holds exactly timeout_minutes, release_bound true, "
                             "provisional false and a non-empty sizing_basis, and none of cited_run_id, cited_sha, p50_minutes or samples")
            if row["timeout_minutes"] != yaml_timeouts[key]:
                raise Reject("timeout-ledger-stale", f"{key}: ledger timeout {row['timeout_minutes']} differs from the workflow's {yaml_timeouts[key]}")
            continue
        if not LEDGER_NORMAL_FIELDS.issubset(row) or set(row) - (LEDGER_NORMAL_FIELDS | LEDGER_NORMAL_OPTIONAL):
            raise Reject("timeout-ledger-schema", f"{key}: a row holds required {sorted(LEDGER_NORMAL_FIELDS)} and only optional {sorted(LEDGER_NORMAL_OPTIONAL)}")
        if ("tree_equal_sha" in row) != ("cited_tree" in row):
            raise Reject("timeout-ledger-schema", f"{key}: tree_equal_sha and cited_tree must appear together")
        if not _is_int(row["timeout_minutes"]) or not _is_int(row["cited_run_id"]) or row["cited_run_id"] <= 0 \
                or not _is_int(row["samples"]) or row["samples"] < 1 or not isinstance(row["provisional"], bool) \
                or not isinstance(row["cited_sha"], str) or not _SHA40.match(row["cited_sha"]) \
                or not isinstance(row["p50_minutes"], str) or not _P50.match(row["p50_minutes"]) \
                or ("tree_equal_sha" in row and (not isinstance(row["tree_equal_sha"], str) or not _SHA40.fullmatch(row["tree_equal_sha"]))) \
                or ("cited_tree" in row and (not isinstance(row["cited_tree"], str) or not _SHA40.fullmatch(row["cited_tree"]))) \
                or ("cited_job_name" in row and (not isinstance(row["cited_job_name"], str) or not _LEDGER_JOB_NAME.fullmatch(row["cited_job_name"]))) \
                or ("disclosure" in row and (not isinstance(row["disclosure"], str) or not _LEDGER_DISCLOSURE.fullmatch(row["disclosure"]))):
            raise Reject("timeout-ledger-schema", f"{key}: malformed field (timeout and samples integers, cited_sha 40 hex, p50 a decimal string)")
        if row["timeout_minutes"] != yaml_timeouts[key]:
            raise Reject("timeout-ledger-stale", f"{key}: ledger timeout {row['timeout_minutes']} differs from the workflow's {yaml_timeouts[key]}")
        p50 = Fraction(row["p50_minutes"])
        if row["timeout_minutes"] < math.ceil(2 * p50):
            raise Reject("timeout-ledger-ratio", f"{key}: timeout {row['timeout_minutes']} is below ceil(2 x p50 {row['p50_minutes']}) = {math.ceil(2 * p50)}")
        if release_head and row["provisional"]:
            raise Reject("timeout-ledger-provisional", f"{key}: a provisional row cannot stand at the release head; re-cite it from a main run")
        if key in gating and p50 > longest:
            longest = p50
    if longest > LEDGER_WHOLE_RUN_MINUTES:
        raise Reject("timeout-ledger-whole-run", f"the longest p50 behind required-native is {float(longest):g} min, over {LEDGER_WHOLE_RUN_MINUTES}")


def check_timeout_ledger(root: Path, release_head: bool = False, git_root: Path | None = None,
                         main_ref: str = "HEAD", disclosure_base: str | None = None) -> None:
    try:
        text = (root / LEDGER_PATH).read_text(encoding="utf-8")
        ledger = json.loads(text, object_pairs_hook=_ledger_pairs)
    except OSError as exc:
        raise Reject("timeout-ledger-schema", f"cannot read {LEDGER_PATH}: {exc.strerror}") from exc
    except ValueError as exc:
        raise Reject("timeout-ledger-schema", f"{LEDGER_PATH} is not valid JSON: {exc}") from exc
    yaml_timeouts: dict[str, int] = {}
    trees = {}
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        tree = read_workflow(path)
        trees[path.name] = tree
        for job_id, job in tree["jobs"].items():
            if "timeout-minutes" in job:
                raw = str(job["timeout-minutes"])
                if not raw.isdigit():
                    raise Reject("timeout-ledger-schema", f"{path.name}:{job_id} timeout-minutes must be an integer literal")
                yaml_timeouts[f"{path.name}:{job_id}"] = int(raw)
    gating = {f"ci.yml:{need}" for need in _needs(trees["ci.yml"]["jobs"]["required-native"])} if "ci.yml" in trees else set()
    judge_timeout_ledger(ledger, yaml_timeouts, gating, _project_version(root), release_head)
    check_ledger_git_objects(ledger, git_root or root, main_ref, release_head,
                             disclosure_base=disclosure_base, workflow_root=root)



def verify_cited(root: Path) -> int:
    """Online, advisory (D-20): confirm each ledger citation through gh. Never runs in CTest."""
    def gh(*args: str):
        result = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False, timeout=120)
        if result.returncode != 0:
            raise Reject("timeout-ledger-cited", f"gh api {' '.join(args)} failed: {result.stderr.strip()[:200]}")
        return json.loads(result.stdout)

    ledger = json.loads((root / LEDGER_PATH).read_text(encoding="utf-8"), object_pairs_hook=_ledger_pairs)
    display: dict[str, str] = {}
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        for job_id, job in read_workflow(path)["jobs"].items():
            name = str(job.get("name", job_id))
            display[f"{path.name}:{job_id}"] = f"release-candidate / {name}" if path.name == "release.yml" else name
    failures = 0
    for key, row in ledger.items():
        if "release_bound" in row:
            print(f"skip {key}: release_bound ({row['sizing_basis'][:60]})")
            continue
        try:
            run = gh("repos/{owner}/{repo}/actions/runs/%d" % row["cited_run_id"])
            jobs = gh("repos/{owner}/{repo}/actions/runs/%d/jobs?per_page=100" % row["cited_run_id"], "--paginate")
            cited_job_name = row.get("cited_job_name")
            expected_job = (f"release-candidate / {cited_job_name}" if key.startswith("release.yml:") else cited_job_name) \
                if cited_job_name is not None else display[key]
            found = [j for page in ([jobs] if isinstance(jobs, dict) else jobs) for j in page.get("jobs", []) if j["name"] == expected_job]
            problems = []
            if run["head_sha"] != row["cited_sha"]:
                problems.append(f"run head {run['head_sha'][:8]} is not the cited sha")
            if not found or found[0]["conclusion"] != "success":
                problems.append("job missing or not successful")
            else:
                started = found[0]["started_at"], found[0]["completed_at"]
                from datetime import datetime
                seconds = (datetime.strptime(started[1], "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(started[0], "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
                if Fraction(math.ceil(Fraction(seconds) / 60 * 100), 100) != Fraction(row["p50_minutes"]):
                    problems.append(f"cited job lasted {seconds / 60:.2f} min, not p50 {row['p50_minutes']}")
            if "tree_equal_sha" in row:
                commit = gh("repos/{owner}/{repo}/git/commits/%s" % run["head_sha"])
                api_tree = commit.get("tree", {}).get("sha")
                if api_tree != row["cited_tree"]:
                    problems.append(f"run head tree {api_tree!r} does not match cited_tree {row['cited_tree']}")
                provisional = False
            elif run["event"] == "pull_request":
                pulls = gh("repos/{owner}/{repo}/commits/%s/pulls" % row["cited_sha"])
                provisional = not any(item.get("merged_at") for item in pulls)
            else:
                ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", row["cited_sha"], "origin/main"], cwd=root, check=False).returncode == 0
                provisional = not ancestor
            if provisional != row["provisional"]:
                problems.append(f"provisional should be {str(provisional).lower()} for a {run['event']} run")
        except Reject as exc:
            problems = [str(exc)]
        for problem in problems:
            print(f"FAIL {key}: {problem}")
        failures += bool(problems)
        if not problems:
            print(f"ok {key}")
    print(f"verify-cited rows={len(ledger)} failures={failures}")
    return 1 if failures else 0


REHEARSAL_FLAG = re.compile(r"(?<![\w-])--rehearsal(?![\w-])")


def check_rehearsal_flag_scope(root: Path) -> None:
    """--rehearsal turns the fuzz receipt check into a source-bound one, because no hosted ci.yml run on main exists
    for a rehearsed branch commit. It is allowed in exactly one place, the rehearsal aggregate's verify call; the release
    and every other workflow keep the strict hosted binding."""
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        if path.name != "release-rehearsal.yml":
            if REHEARSAL_FLAG.search(path.read_text(encoding="utf-8")):
                raise Reject("rehearsal-flag-scope", f"{path.name} must not pass --rehearsal; only the rehearsal aggregate may")
    # The release steps now live in the lifecycle script, so the same rule covers it.
    lifecycle = root / LIFECYCLE_SCRIPT
    if lifecycle.is_file() and REHEARSAL_FLAG.search(lifecycle.read_text(encoding="utf-8")):
        raise Reject("rehearsal-flag-scope", f"{LIFECYCLE_SCRIPT} must not pass --rehearsal; only the rehearsal aggregate may")
    tree = read_workflow(root / ".github/workflows/release-rehearsal.yml")
    for job_id, job in tree["jobs"].items():
        for step in job.get("steps", []):
            if job_id != "aggregate" and REHEARSAL_FLAG.search(step.get("run", "")):
                raise Reject("rehearsal-flag-scope", f"release-rehearsal.{job_id} must not pass --rehearsal; only the aggregate may")


# --------------------------------------------------------------------------- version-PR content window (RM-028, D-19)
# release-please regenerates the version PR (body, changelog, version files) and the ledger is rendered from managed
# inputs, so a reviewed window is judged AFTER regeneration by the trusted checker, with the version-PR head read as
# Git objects and never executed. The gate is fatal, runs even when the release job fails, keeps the push trigger
# unfiltered and the release-note paths in release-please's own change set. It does not open or merge a version PR.
WINDOW_WORKFLOW = "release-please.yml"
WINDOW_JOB = "version-window"
WINDOW_IF = "${{ !cancelled() && inputs.retry != true }}"
WINDOW_CHECKER = "tests/scripts/verify-version-window.py"
WINDOW_RECORD = "tests/data/version-window.json"
WINDOW_CONFIG = "release-please-config.json"
WINDOW_CALL = ('python3 -I trusted/tests/scripts/verify-version-window.py --repo version-pr --rev "$PR_HEAD" '
               '--base "$MAIN_SHA" --check tests/data/version-window.json --body "$RUNNER_TEMP/version-pr-body.md"')
WINDOW_PERMISSIONS = {"contents": "read", "pull-requests": "read"}
WINDOW_STEP_TIMEOUT_MAX = 10
VERSION_PR_WORKFLOW = "version-pr-gate.yml"
VERSION_PR_JOB = "pre-tag-gate"
VERSION_PR_IF = ("${{ github.event.pull_request.head.ref == 'release-please--branches--main--components--GabbaBoy' "
                 "&& github.event.pull_request.head.repo.full_name == github.repository }}")
VERSION_PR_WINDOW_CALL = ('python3 -I trusted/tests/scripts/verify-version-window.py --repo version-pr --rev "$PR_HEAD" '
                          '--base "$BASE_SHA" --check tests/data/version-window.json --body "$RUNNER_TEMP/version-pr-body.md"')
VERSION_PR_BODY_WRITE = "printf '%s' \"$PR_BODY\" > \"$RUNNER_TEMP/version-pr-body.md\""
VERSION_PR_RUNS_API = ('gh api "repos/$GH_REPO/actions/workflows/release-rehearsal.yml/runs?'
                       'branch=rehearsal/$RELEASE_TAG&per_page=100"')
VERSION_PR_BIND_CALL = ('python3 -I .github/scripts/verify-release-source-proof.py --bind-rehearsal-run '
                        '"$RUNNER_TEMP/rehearsal-runs.json" --tag "$RELEASE_TAG" --source-sha "$PR_HEAD" '
                        '--repo "$GH_REPO" --selected-run "$RUNNER_TEMP/rehearsal-run.json" --pr-head "$PR_HEAD"')
VERSION_WINDOW_SOURCE_COPY = ('git show "${GITHUB_SHA}:tests/scripts/verify-version-window.py" > '
                              '"$RUNNER_TEMP/verify-version-window.py"')
VERSION_WINDOW_SOURCE_CALL = ('python3 -I "$RUNNER_TEMP/verify-version-window.py" --check-tracked '
                              '--rev "$SOURCE_SHA" --require-active --repo .')
VERSION_PR_STEP_NAMES = {
    "trusted": "Check out the trusted PR base",
    "head": "Check out the version PR head as data",
    "body": "Write the event's reviewed PR body",
    "window": "Judge the version window on the exact PR base",
    "state": "Select rehearsal only for an active window",
    "fetch": "Fetch rehearsal runs for the active version window",
    "bind": "Bind the rehearsal to the reviewed version PR head",
}
# release-please already ignores its own workflow and script paths when attributing commits; anything wider would hide
# a source, release-note or generator-input change from the version PR the window freezes.
WINDOW_EXCLUDED_PATHS_ALLOWED = (".github/workflows", ".github/scripts")


def _check_window_config(root: Path) -> None:
    try:
        config = json.loads((root / WINDOW_CONFIG).read_text(encoding="utf-8"), object_pairs_hook=_ledger_pairs)
    except OSError as exc:
        raise Reject("window-config", f"cannot read {WINDOW_CONFIG}: {exc.strerror}") from exc
    except (ValueError, Reject) as exc:
        raise Reject("window-config", f"{WINDOW_CONFIG} is not strict JSON: {exc}") from exc
    package = config.get("packages", {}).get(".") if isinstance(config, dict) else None
    if not isinstance(package, dict):
        raise Reject("window-config", f"{WINDOW_CONFIG} must configure the root package")
    for scope, holder in (("top level", config), ("root package", package)):
        excluded = holder.get("exclude-paths", [])
        if not isinstance(excluded, list) or any(path not in WINDOW_EXCLUDED_PATHS_ALLOWED for path in excluded):
            raise Reject("window-path-excluded",
                         f"{WINDOW_CONFIG} {scope} exclude-paths may only be {list(WINDOW_EXCLUDED_PATHS_ALLOWED)}, not {excluded!r}: "
                         "excluding source, release-note or generator-input paths hides changes from the version PR")
        if holder.get("skip-changelog") not in (None, False) or holder.get("skip-github-release") not in (None, False):
            raise Reject("window-config", f"{WINDOW_CONFIG} {scope} may not skip the changelog or the GitHub release")
    if package.get("changelog-path") != "CHANGELOG.md" or "CMakeLists.txt" not in package.get("extra-files", []):
        raise Reject("window-config", f"{WINDOW_CONFIG} must keep CHANGELOG.md and the CMakeLists.txt version file under release-please")


def check_version_window(root: Path) -> None:
    name = WINDOW_WORKFLOW
    tree = read_workflow(root / ".github/workflows" / WINDOW_WORKFLOW)
    for path in (WINDOW_CHECKER, WINDOW_RECORD):
        if not (root / path).is_file():
            raise Reject("window-gate-missing", f"{path} is required by the {WINDOW_JOB} gate and is not in the tree")
    push = tree.get("on", {}).get("push") if isinstance(tree.get("on"), dict) else None
    if not isinstance(push, dict) or push.get("branches") != ["main"] or {"paths", "paths-ignore"} & set(push):
        raise Reject("window-trigger-filtered", f"{name} must start on every push to main; a paths filter would let a relevant change skip regeneration")
    job = tree["jobs"].get(WINDOW_JOB)
    if job is None:
        raise Reject("window-gate-missing", f"{name} has no {WINDOW_JOB} job, so a regenerated version PR is never judged against its window")
    if _needs(job) != {"release"}:
        raise Reject("window-gate-order", f"{_where(name, WINDOW_JOB)} must depend on exactly the release job so it judges the PR after regeneration")
    if str(job.get("if", "")).strip() != WINDOW_IF:
        raise Reject("window-gate-skipped", f"{_where(name, WINDOW_JOB)} must run with {WINDOW_IF}, so a failed release job cannot skip it")
    if _permissions(job, tree.get("permissions", {})) != WINDOW_PERMISSIONS:
        raise Reject("window-gate-permissions", f"{_where(name, WINDOW_JOB)} needs exactly {WINDOW_PERMISSIONS}")
    _check_checkout_credentials(name, tree, (WINDOW_JOB,))
    checkouts = _checkouts(job)
    by_path = {step.get("with", {}).get("path"): step.get("with", {}) for step in checkouts}
    if len(checkouts) != 2 or set(by_path) != {"trusted", "version-pr"}:
        raise Reject("window-gate-trust", f"{_where(name, WINDOW_JOB)} needs exactly a trusted checkout and a version-pr data checkout")
    if by_path["trusted"].get("ref") != TRUSTED_SHA_REF:
        raise Reject("window-gate-trust", f"{_where(name, WINDOW_JOB)} must take the checker from the trusted main commit {TRUSTED_SHA_REF}")
    if str(by_path["version-pr"].get("fetch-depth", "")) != "0":
        raise Reject("window-gate-history", f"{_where(name, WINDOW_JOB)} needs the full history of the version PR to prove ancestry")
    for step in job.get("steps", []):
        minutes = str(step.get("timeout-minutes", ""))
        if not minutes.isdigit() or not 1 <= int(minutes) <= WINDOW_STEP_TIMEOUT_MAX:
            raise Reject("window-gate-timeout", f"{_where(name, WINDOW_JOB)} step {step.get('name', '?')!r} needs a timeout-minutes of at most {WINDOW_STEP_TIMEOUT_MAX}")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    _check_bounded_downloads(name, tree)
    require_call(name, WINDOW_JOB, job, WINDOW_CALL, conditional=True)
    _check_window_config(root)


def check_version_pr_gate(root: Path) -> None:
    name = VERSION_PR_WORKFLOW
    tree = read_workflow(root / ".github/workflows" / VERSION_PR_WORKFLOW)
    triggers = tree.get("on")
    expected_types = ["opened", "synchronize", "reopened", "edited"]
    pull_request = triggers.get("pull_request") if isinstance(triggers, dict) else None
    if (set(triggers or {}) != {"pull_request"} or not isinstance(pull_request, dict)
            or pull_request.get("types") != expected_types or pull_request.get("branches") != ["main"]):
        raise Reject("version-pr-gate-trigger", f"{name} must run only on opened, synchronized, reopened or edited PRs to main")
    if tree.get("permissions") != {"contents": "read"}:
        raise Reject("version-pr-gate-permissions", f"{name} needs top-level contents: read only")
    jobs = tree.get("jobs", {})
    if set(jobs) != {VERSION_PR_JOB}:
        raise Reject("version-pr-gate-trust", f"{name} must contain exactly the pre-tag gate job")
    job = jobs[VERSION_PR_JOB]
    if _permissions(job, tree["permissions"]) != {"actions": "read", "contents": "read"}:
        raise Reject("version-pr-gate-permissions", f"{_where(name, VERSION_PR_JOB)} needs exactly actions: read and contents: read")
    if (job.get("name") != "version-pr-pre-tag-gate" or str(job.get("if", "")).strip() != VERSION_PR_IF
            or job.get("runs-on") != "ubuntu-22.04" or "needs" in job):
        raise Reject("version-pr-gate-trust", f"{_where(name, VERSION_PR_JOB)} must run only for the same-repository release-please version PR")
    if "timeout-minutes" in job:
        raise Reject("version-pr-gate-timeout", f"{_where(name, VERSION_PR_JOB)} must have per-step timeouts and no job-level timeout")
    steps = job.get("steps", [])
    expected_names = [VERSION_PR_STEP_NAMES[key] for key in ("trusted", "head", "body", "window", "state", "fetch", "bind")]
    if len(steps) != len(expected_names) or [step.get("name") for step in steps] != expected_names:
        raise Reject("version-pr-gate-trust", f"{_where(name, VERSION_PR_JOB)} must keep the trusted, data, window and R2 steps in order")
    for step in steps:
        minutes = str(step.get("timeout-minutes", ""))
        if not minutes.isdigit() or not 1 <= int(minutes) <= WINDOW_STEP_TIMEOUT_MAX:
            raise Reject("version-pr-gate-timeout", f"{_where(name, VERSION_PR_JOB)} step {step.get('name', '?')!r} needs a timeout from 1 to {WINDOW_STEP_TIMEOUT_MAX} minutes")
    _check_actions(name, tree)
    _check_disabled(name, tree)
    _check_ignored_failures(name, tree)
    _check_run_expressions(name, tree)
    _check_bounded_downloads(name, tree)
    _check_checkout_credentials(name, tree, (VERSION_PR_JOB,))
    _check_token_scope(name, VERSION_PR_JOB, job)
    _check_token_subject_execution(name, VERSION_PR_JOB, job)

    if job.get("env") != {
        "GH_REPO": "${{ github.repository }}",
        "PR_HEAD": "${{ github.event.pull_request.head.sha }}",
    }:
        raise Reject("version-pr-gate-trust", f"{_where(name, VERSION_PR_JOB)} must use the exact PR base and head identities")
    checkouts = _checkouts(job)
    by_path = {step.get("with", {}).get("path"): step.get("with", {}) for step in checkouts}
    if len(checkouts) != 2 or set(by_path) != {"trusted", "version-pr"}:
        raise Reject("version-pr-gate-trust", f"{_where(name, VERSION_PR_JOB)} needs one trusted base checkout and one version-pr data checkout")
    if (by_path["trusted"].get("ref") != "${{ github.event.pull_request.base.sha }}"
            or by_path["version-pr"].get("ref") != "${{ github.event.pull_request.head.sha }}"
            or any(str(by_path[path].get("fetch-depth", "")) != "0" for path in ("trusted", "version-pr"))):
        raise Reject("version-pr-gate-trust", f"{_where(name, VERSION_PR_JOB)} must trust the immutable PR base and read the full PR-head history as data")

    body = steps[2]
    if body.get("env", {}).get("PR_BODY") != "${{ github.event.pull_request.body }}":
        raise Reject("version-pr-gate-trust", "the PR body must pass through an environment variable before writing to a file")
    require_call(name, VERSION_PR_JOB, {"steps": [body]}, VERSION_PR_BODY_WRITE)

    window = steps[3]
    window_text = window.get("run", "")
    if "python3 -I version-pr/" in window_text:
        raise Reject("version-pr-gate-trust", "the version PR head is data and cannot provide the window checker")
    if "BASE_SHA=$(git -C trusted rev-parse HEAD)" not in window_text:
        raise Reject("version-pr-gate-trust", "the window base must be the immutable trusted PR-base checkout")
    require_call(name, VERSION_PR_JOB, {"steps": [window]}, VERSION_PR_WINDOW_CALL)
    state = steps[4]
    if state.get("id") != "window":
        raise Reject("version-pr-gate-trust", "the window state step must expose whether a valid active record exists")
    window_text = state.get("run", "")
    for pin in ('"version-window inactive pass "*', '"version-window active pass "*', 'active=false', 'active=true'):
        if pin not in window_text:
            raise Reject("version-pr-gate-trust", "the window step must pass an inactive record and gate rehearsal only for an active record")

    fetch = steps[5]
    active_if = "${{ steps.window.outputs.active == 'true' }}"
    if fetch.get("id") != "rehearsal" or fetch.get("if") != active_if \
            or fetch.get("env", {}).get("GH_TOKEN") != "${{ github.token }}":
        raise Reject("version-pr-gate-trust", "the rehearsal API read must run only after an active window using actions: read")
    fetch_text = fetch.get("run", "")
    for pin in ('version-pr/tests/data/version-window.json', 'RELEASE_TAG="v$version"',
                'printf \'tag=%s\\n\' "$RELEASE_TAG" >> "$GITHUB_OUTPUT"'):
        if pin not in fetch_text:
            raise Reject("version-pr-gate-trust", "the active version must select and name the rehearsal branch")
    fetch_job = {"steps": [{key: value for key, value in fetch.items() if key != "if"}]}
    require_call(name, VERSION_PR_JOB, fetch_job, VERSION_PR_RUNS_API)
    _check_token_step_commands(name, VERSION_PR_JOB, fetch_job)

    bind = steps[6]
    if (bind.get("if") != active_if or bind.get("working-directory") != "trusted"
            or bind.get("env", {}).get("RELEASE_TAG") != "${{ steps.rehearsal.outputs.tag }}"):
        raise Reject("version-pr-gate-trust", "the rehearsal judge must use trusted base code and run only for an active window")
    bind_job = {"steps": [{key: value for key, value in bind.items() if key != "if"}]}
    require_call(name, VERSION_PR_JOB, bind_job, VERSION_PR_BIND_CALL)



PERF_GATE_SCRIPT = "tests/scripts/run-perf-gate.sh"
RELEASE_GATES_CLI = "tests/scripts/verify-release-gates.py"
PERF_GATE_APPROVAL_PARTS = (
    # (fragment, how many times it must appear, the reason)
    ('--emit-exception-measurement "$WORK/exception-measurement.json"', 1, "the evaluator must write the measurement the owner approves"),
    ('python3 -I "$GATES" --review-approval --comment-json "$GBB_IR_EXCEPTION_COMMENT_JSON"', 1, "the release gate must verify the owner comment"),
    ('--measurement "$WORK/exception-measurement.json" \\\n      --rev "$head_revision" --output "$WORK/exception-decision.json" --exception-receipt "$WORK/exception-receipt.json" \\\n'
     '      --repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}" ||\n      fail exception-approval-refused', 1,
     "the approval must be bound to the measurement, the head and this repository, and its refusal must be fatal"),
    ('args+=(--exception-receipt "$WORK/exception-receipt.json")', 1, "only the receipt the gate wrote may reach the evaluator"),
)


def check_release_gate_wiring(root: Path) -> None:
    """RM-030: the actual conditional Ir exception path verifies an OWNER approval before the ratchet sees a receipt."""
    try:
        text = (root / PERF_GATE_SCRIPT).read_text(encoding="utf-8")
    except OSError as exc:
        raise Reject("release-gate-wiring", f"{PERF_GATE_SCRIPT} cannot be read: {exc.strerror}") from exc
    if not (root / RELEASE_GATES_CLI).is_file():
        raise Reject("release-gate-wiring", f"{RELEASE_GATES_CLI} is absent, so the approval path is defined but cannot run")
    for fragment, count, reason in PERF_GATE_APPROVAL_PARTS:
        if text.count(fragment) != count:
            raise Reject("release-gate-wiring", f"{PERF_GATE_SCRIPT}: {reason} (expected {count} of: {fragment[:70]})")
    if "GBB_PERF_EXCEPTION_RECEIPT" in text or text.count("--exception-receipt") != 2:
        raise Reject("release-gate-wiring", f"{PERF_GATE_SCRIPT} must not accept an exception receipt that the approval gate did not write")
    emit, review, handed = (text.find(part) for part in ('--emit-exception-measurement "$WORK', 'python3 -I "$GATES" --review-approval',
                                                          'args+=(--exception-receipt'))
    if not 0 < emit < review < handed:
        raise Reject("release-gate-wiring", f"{PERF_GATE_SCRIPT} must emit the measurement, verify the approval and only then hand over the receipt")


# CR-C01: the owner-approval inputs of a widened Ir limit reach run-perf-gate.sh only through these two environment
# names, and no workflow has a legitimate reason to supply them: an approval is verified locally by the owner, and no
# trusted step fetches the comment from the API. A workflow, job or step `env:`, a `$GITHUB_ENV` write, or any other
# text naming them (a split name included, so the suffixes are matched on their own, and case-insensitively because
# Windows environment names are) is refused in every workflow file, listed or not. The expected review repository
# comes from $GITHUB_REPOSITORY, so a workflow that assigns that name is refused too. With both rules, a hosted run
# fails closed for a widened limit.
IR_EXCEPTION_ENV = re.compile(r"GBB_IR_EXCEPTION|EXCEPTION_COMMENT_JSON|EXCEPTION_DECISION|GITHUB_REPOSITORY\s*[:=]", re.I)


def check_ir_exception_env(root: Path) -> None:
    directory = root / ".github/workflows"
    for path in sorted([*directory.glob("*.yml"), *directory.glob("*.yaml")]):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise Reject("ir-exception-env", f"{path.name} cannot be read: {exc.strerror}") from exc
        found = IR_EXCEPTION_ENV.search(text)
        if found:
            line = text.count("\n", 0, found.start()) + 1
            raise Reject("ir-exception-env", f"{path.name}:{line}: a workflow must not supply the Ir exception approval inputs "
                         f"or the expected review repository ({found.group(0)!r}); hosted runs fail closed for a widened limit")


# WR-C01: rules for every workflow file, including ones the specific checks above do not know. The workflow set is
# closed, so a new file is refused until it is listed and judged. No workflow may use a trigger that runs with the base
# repository's token on contributed code (pull_request_target, workflow_run), forward secrets to a called workflow, or
# interpolate event text an outsider controls (a branch name, a title, a body) into a run body. A write permission is
# allowed only where it is listed below, scope by scope; every top level is read-only.
WORKFLOW_FORBIDDEN_TRIGGERS = frozenset({"pull_request_target", "workflow_run"})
WORKFLOW_WRITE_ALLOWLIST = {
    ("release.yml", "release"): frozenset({"contents", "issues", "pull-requests"}),
    ("release.yml", "candidate"): frozenset({"contents"}),
    ("release.yml", "candidate-macos"): frozenset({"contents"}),
    ("release.yml", "candidate-windows"): frozenset({"contents"}),
    ("release.yml", "attach-v02-evidence"): frozenset({"contents"}),
    ("release.yml", "candidate-platform-manifest"): frozenset({"contents"}),
    ("release.yml", "publish-qualified-release"): frozenset({"contents"}),
    ("release-please.yml", "release"): frozenset({"contents", "issues", "pull-requests"}),
    ("nightly-asan.yml", "report-red"): frozenset({"issues"}),
}
# Event fields whose values are commit ids, not text an outsider writes; anything else under github.event, and
# github.head_ref, reaches a run body only through env:.
_EVENT_TEXT = re.compile(r"github\.head_ref|github\.event\.(?!(?:pull_request\.(?:head|base)\.sha|before|after)\b)\w")


def check_workflow_set(root: Path) -> None:
    """Runs first: an unlisted or vanished workflow file is refused before any rule reads a listed one."""
    directory = root / ".github/workflows"
    present = {path.name for path in [*directory.glob("*.yml"), *directory.glob("*.yaml")]}
    if present != set(WORKFLOWS):
        unknown, missing = sorted(present - set(WORKFLOWS)), sorted(set(WORKFLOWS) - present)
        raise Reject("workflow-unlisted", f"the workflow set must be exactly the judged list: unlisted {unknown}, missing {missing}")


def check_workflow_closed_world(root: Path) -> None:
    """Runs last, so a defect a specific rule names keeps that rule's code."""
    directory = root / ".github/workflows"
    for name in WORKFLOWS:
        tree = read_workflow(directory / name)
        forbidden = sorted(_trigger_names(tree) & WORKFLOW_FORBIDDEN_TRIGGERS)
        if forbidden:
            raise Reject("workflow-trigger", f"{name} must not run on {', '.join(forbidden)}")
        top = tree.get("permissions", {})
        if not isinstance(top, dict) or _writes(top):
            raise Reject("workflow-write-permissions", f"{name} top-level permissions must be an explicit read-only map")
        for job_id, job in tree["jobs"].items():
            if "secrets" in job:
                raise Reject("workflow-secrets", f"{_where(name, job_id)} must not forward secrets to a called workflow")
            perms = _permissions(job, tree)
            writes = {scope for scope, value in perms.items() if value == "write"}
            allowed = WORKFLOW_WRITE_ALLOWLIST.get((name, job_id), frozenset())
            if writes - allowed:
                raise Reject("workflow-write-permissions", f"{_where(name, job_id)} gains write access it is not listed for: "
                             f"{', '.join(sorted(writes - allowed))}")
            for step in job.get("steps", []):
                for expression in _EXPRESSION.findall(str(step.get("run", ""))):
                    if _EVENT_TEXT.search(expression):
                        raise Reject("run-expression", f"{_where(name, job_id)} step {step.get('name', '?')!r} interpolates "
                                     f"${{{{ {expression.strip()} }}}} into a run body; pass it through step-level env")


def check_all(root: Path, release_head: bool = False, git_root: Path | None = None, main_ref: str = "HEAD",
              disclosure_base: str | None = None) -> dict[str, int]:
    check_workflow_set(root)
    check_producer_script(root)
    check_ir_exception_env(root)
    check_rehearsal_flag_scope(root)
    check_rehearsal(root)
    check_ci(root)
    check_perf_attribution(root)
    check_nightly(root)
    check_readonly_workflows(root)
    check_preview_player_lane(root)
    check_release(root)
    check_release_gate_wiring(root)
    check_version_window(root)
    check_version_pr_gate(root)
    check_timeout_ledger(root, release_head, git_root, main_ref, disclosure_base)
    check_workflow_closed_world(root)
    residual = sorted(job_id for job_id, role in RELEASE_ROLES.items() if role == "residual")
    return {"residual": len(residual)}


# --------------------------------------------------------------------------- red-report body replay (IN-03)
# The reporting step's own run body is executed under bash against a `gh` stand-in that serves fixture-shaped label and issue
# lists (applying the body's own --jq with the real jq), refuses every other call with exit 97 and records the calls that would
# change GitHub. A comment is credited only for the exact title carrying the label, and a dry run must send nothing at all.
_REPORT_RED_STUB = r"""#!/usr/bin/env bash
set -eu
expr=""
previous=""
for argument in "$@"; do
  if [ "$previous" = "--jq" ]; then expr=$argument; fi
  previous=$argument
done
case "$1 ${2:-}" in
  "label list") printf '%s' "$STUB_LABELS" | jq -r "$expr" ;;
  "issue list") printf '%s' "$STUB_ISSUES" | jq -r "$expr" ;;
  "label create"|"issue create"|"issue comment") printf 'SENT gh %s\n' "$*" >> "$STUB_LOG" ;;
  *) printf 'unexpected gh call: %s\n' "$*" >&2; exit 97 ;;
esac
"""
_VERIFY_CITED_STUB = r"""#!/usr/bin/env bash
set -eu
case "${1:-} ${2:-}" in
  "api repos/{owner}/{repo}/actions/runs/40257161612")
    printf '{"head_sha":"%s","event":"workflow_dispatch"}\n' "$STUB_HEAD_SHA" ;;
  "api repos/{owner}/{repo}/actions/runs/40257161612/jobs?per_page=100")
    printf '{"jobs":[{"name":"%s","conclusion":"success","started_at":"2026-10-26T02:02:59Z","completed_at":"2026-10-26T02:03:07Z"}]}\n' "$STUB_JOB_NAME" ;;
  "api repos/{owner}/{repo}/git/commits/c6dc575b6a84cf51a56688948fce9241ba323400")
    printf '{"tree":{"sha":"%s"}}\n' "$STUB_TREE" ;;
  *) printf 'unexpected gh route: %s\n' "$*" >&2; exit 97 ;;
esac
"""
_REPORT_TITLE = "nightly-red: asan-full-replay"
_REPORT_LABEL = "nightly-red"


def _report_issue(number: int, title: str, labels: tuple[str, ...]) -> dict:
    return {"number": number, "title": title, "labels": [{"name": name, "color": "b60205", "description": ""} for name in labels]}


# name, open issues the stand-in serves, labels that exist, dry run -> the calls expected (sent, then recorded-not-sent)
_REPORT_SCENARIOS = (
    ("no open issue creates one with the label", [], [_REPORT_LABEL], False,
     [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("the exact title with the label is reused", [_report_issue(7, _REPORT_TITLE, (_REPORT_LABEL,))], [_REPORT_LABEL], False,
     ["issue comment 7 --body"], []),
    ("the lowest-numbered exact match is reused", [_report_issue(9, _REPORT_TITLE, (_REPORT_LABEL,)), _report_issue(4, _REPORT_TITLE, (_REPORT_LABEL, "bug"))],
     [_REPORT_LABEL], False, ["issue comment 4 --body"], []),
    ("an unrelated title containing the phrase opens a new issue", [_report_issue(7, f"Investigate {_REPORT_TITLE} flake", (_REPORT_LABEL,))],
     [_REPORT_LABEL], False, [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("a title that only starts with the phrase opens a new issue", [_report_issue(7, _REPORT_TITLE + " (old)", (_REPORT_LABEL,))],
     [_REPORT_LABEL], False, [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("the exact title under another label opens a new issue", [_report_issue(7, _REPORT_TITLE, ("bug",))],
     [_REPORT_LABEL], False, [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("the exact title with no label at all opens a new issue", [_report_issue(7, _REPORT_TITLE, ())],
     [_REPORT_LABEL], False, [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("a missing label is created before the issue", [], [], False,
     [f"label create {_REPORT_LABEL} --description Nightly ASan stall replay failed --color B60205",
      f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"], []),
    ("a dry run with no open issue sends nothing", [], [_REPORT_LABEL], True, [],
     [f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"]),
    ("a dry run with a match sends nothing", [_report_issue(7, _REPORT_TITLE, (_REPORT_LABEL,))], [_REPORT_LABEL], True, [],
     ["issue comment 7 --body"]),
    ("a dry run with a missing label sends nothing", [], [], True, [],
     [f"label create {_REPORT_LABEL} --description Nightly ASan stall replay failed --color B60205",
      f"issue create --title {_REPORT_TITLE} --label {_REPORT_LABEL} --body"]),
)


def _replay_report_body(body: str, scratch: Path, issues: list, labels: list[str], dry_run: bool) -> tuple[list[str], list[str], int]:
    """Run the body once. Returns (calls sent, calls recorded but not sent, exit status), each call cut before its --body text."""
    stub_dir = scratch / "bin"
    stub_dir.mkdir(exist_ok=True)
    stub = stub_dir / "gh"
    stub.write_bytes(_REPORT_RED_STUB.encode("utf-8"))
    stub.chmod(0o755)
    log = scratch / "calls.log"
    log.write_bytes(b"")
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "TMPDIR", "HOME", "LANG")}
    env.update(PATH=f"{stub_dir}{os.pathsep}{env.get('PATH', '')}", STUB_LOG=str(log),
               STUB_ISSUES=json.dumps(issues), STUB_LABELS=json.dumps([{"name": name} for name in labels]),
               RUN_URL="https://example.invalid/runs/1", ISSUE_TITLE=_REPORT_TITLE, ISSUE_LABEL=_REPORT_LABEL,
               DRY_RUN="true" if dry_run else "false", GH_TOKEN="stub", GH_REPO="owner/repo")
    done = subprocess.run(["bash", "-c", body], capture_output=True, text=True, check=False, env=env, timeout=30)

    def cut(line: str) -> str:
        line = line.split(" gh ", 1)[1] if " gh " in line else line
        return line.split("--body", 1)[0].strip() + (" --body" if "--body" in line else "")
    sent = [cut(line) for line in log.read_text(encoding="utf-8").splitlines() if line.startswith("SENT gh ")]
    recorded = [cut(line) for line in done.stdout.splitlines() if line.startswith("DRY-RUN not sent: gh ")]
    return sent, recorded, done.returncode


def report_red_replay_controls(root: Path) -> int:
    """Positive scenarios on the production body and body mutants that the scenarios must tell apart. POSIX only: the body is
    bash and the stand-in applies its jq filters with the real jq."""
    if os.name == "nt":
        print("skipped: red-report body replay (needs bash and jq; the static report-red rules above still apply)")
        return 0
    if shutil.which("bash") is None or shutil.which("jq") is None:
        raise SystemExit("self-test red-report replay needs bash and jq on PATH")
    tree = read_workflow(root / ".github/workflows/nightly-asan.yml")
    steps = tree["jobs"]["report-red"]["steps"]
    body = str(steps[0]["run"])
    controls = 0
    with tempfile.TemporaryDirectory(prefix="gbb-report-red.") as directory:
        scratch = Path(directory)

        def outcome(text: str, scenario: tuple) -> tuple[list[str], list[str], int]:
            return _replay_report_body(text, scratch, scenario[1], scenario[2], scenario[3])

        for scenario in _REPORT_SCENARIOS:
            sent, recorded, status = outcome(body, scenario)
            if status != 0 or sent != scenario[4] or recorded != scenario[5]:
                raise SystemExit(f"self-test red-report replay: {scenario[0]}: exit={status} sent={sent} recorded={recorded}, "
                                 f"wanted sent={scenario[4]} recorded={scenario[5]}")
            controls += 1
        # Each mutant must behave differently from the production body on the scenario that exists to catch it.
        by_name = {scenario[0]: scenario for scenario in _REPORT_SCENARIOS}
        mutants = (
            ("a title phrase match", "select(.title == env.ISSUE_TITLE and", "select((.title | contains(env.ISSUE_TITLE)) and",
             "an unrelated title containing the phrase opens a new issue"),
            ("a title prefix match", "select(.title == env.ISSUE_TITLE and", "select((.title | startswith(env.ISSUE_TITLE)) and",
             "a title that only starts with the phrase opens a new issue"),
            ("no label match", " and any(.labels[]; .name == env.ISSUE_LABEL))]", ")]",
             "the exact title under another label opens a new issue"),
            ("a label match on any label", "any(.labels[]; .name == env.ISSUE_LABEL)", "(.labels | length) > 0",
             "the exact title under another label opens a new issue"),
            ("the newest match", "sort_by(.number) | .[0].number", "sort_by(.number) | .[-1].number",
             "the lowest-numbered exact match is reused"),
            ("an issue write outside the wrapper", 'issue_write issue create --title', 'gh issue create --title',
             "a dry run with no open issue sends nothing"),
            ("a wrapper that always sends", 'if [ "$DRY_RUN" = true ]; then', 'if [ "$DRY_RUN" = never ]; then',
             "a dry run with a match sends nothing"),
            ("a missing label that is never created", '!= true ]; then\n', '!= true ] && false; then\n',
             "a missing label is created before the issue"),
        )
        for label, old, new, scenario_name in mutants:
            if body.count(old) < 1:
                raise SystemExit(f"self-test red-report replay: mutant anchor for {label!r} is absent from the production body")
            scenario = by_name[scenario_name]
            sent, recorded, status = outcome(body.replace(old, new, 1), scenario)
            if status == 0 and sent == scenario[4] and recorded == scenario[5]:
                raise SystemExit(f"self-test red-report replay: the mutant {label!r} behaved like the production body on {scenario_name!r}")
            controls += 1
    print(f"rejected: red-report body replay holds {len(_REPORT_SCENARIOS)} scenarios and refuses {len(mutants)} mutants")
    return controls


# --------------------------------------------------------------------------- self-test
WORKFLOWS = ("release-rehearsal.yml", "release.yml", "release-please.yml", "version-pr-gate.yml", "ci.yml", "fixture-repro.yml", "preview.yml", "perf-attribution.yml", "nightly-asan.yml", "libbet-repro.yml")


def _copy_fixture(root: Path, target: Path) -> None:
    for item in WORKFLOWS:
        destination = target / ".github/workflows" / item
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / ".github/workflows" / item).read_bytes())
    for extra in (LEDGER_PATH, "CMakeLists.txt", "tests/expected-tests.txt", WINDOW_CONFIG, WINDOW_CHECKER, WINDOW_RECORD, LIFECYCLE_SCRIPT,
                  PERF_GATE_SCRIPT, RELEASE_GATES_CLI):
        if (root / extra).is_file():
            (target / extra).parent.mkdir(parents=True, exist_ok=True)
            (target / extra).write_bytes((root / extra).read_bytes())
    script = target / PRODUCER_SCRIPT
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes((root / PRODUCER_SCRIPT).read_bytes()) if (root / PRODUCER_SCRIPT).is_file() else None


def _run_cli(fixture: Path, cwd: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(Path(__file__).resolve()), "--check", "--root", str(fixture),
         "--git-root", str(Path(__file__).resolve().parents[2]), *extra],
        capture_output=True, text=True, check=False, cwd=cwd, timeout=60,
    )


def _m(label: str, workflow: str, after: str, old: str, new: str, expected: str):
    return (label, workflow, [(after, old, new)], expected)


JUDGE_CALL = "python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject --release-head --git-root trusted-judge"
_REHEARSAL_TAG_LINE = "bash .github/scripts/produce-release-evidence.sh verify-subject --subject . --source-sha \"$GITHUB_SHA\" --tag \"$REHEARSAL_TAG\" --local-tag"
JUDGE_STEP = "      - name: Judge workflow privilege and trust wiring from the trusted checkout\n"
REHEARSAL_TAG_EXISTS_STEP = (
    '      - name: Refuse rehearsal after its release tag exists\n'
    '        shell: bash\n'
    '        run: |\n'
    '          set -euo pipefail\n'
    '          TAG="${GITHUB_REF_NAME#rehearsal/}"\n'
    '          if [[ "$TAG" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]; then\n'
    '            tag_ref=$(git ls-remote --tags "https://github.com/$GITHUB_REPOSITORY" "refs/tags/$TAG")\n'
    '            if [[ -n "$tag_ref" ]]; then\n'
    '              echo "Tag $TAG already exists; a rehearsal after the tag cannot bind a release." >&2\n'
    '              exit 1\n'
    '            fi\n'
    '          fi\n'
)
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
        _m("release candidate perf gate receipt verifier is removed", rel, "  candidate-fuzz:\n",
           "python3 -I tests/scripts/verify-perf-gate.py --verify-receipt",
           "# python3 -I tests/scripts/verify-perf-gate.py --verify-receipt", "required-command-not-executed"),
        _m("CI perf gate receipt upload is not retained on failure", "ci.yml", "  perf-gate:\n",
           "        if: always()\n", "        if: success()\n", "artifact-flow"),
        _m("CI perf gate receipt upload is removed", "ci.yml", "  perf-gate:\n",
           "uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
           "uses: actions/download-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", "artifact-flow"),
        ("CI perf gate receipt upload is delayed until after the seeded control", "ci.yml", [
            ("  perf-gate:\n", "      - name: Retain the perf-gate receipt on pass or failure\n        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2\n        if: always()\n        with:\n          name: perf-gate-${{ github.run_id }}-${{ github.run_attempt }}\n          path: build/perf-gate-receipt.json\n          if-no-files-found: error\n          retention-days: 7\n", ""),
            ("  perf-gate:\n", "      - name: Prove the gate rejects a seeded regression\n        shell: bash\n        run: bash tests/scripts/run-perf-gate.sh --seeded-regression\n", "      - name: Prove the gate rejects a seeded regression\n        shell: bash\n        run: bash tests/scripts/run-perf-gate.sh --seeded-regression\n      - name: Retain the perf-gate receipt on pass or failure\n        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2\n        if: always()\n        with:\n          name: perf-gate-${{ github.run_id }}-${{ github.run_attempt }}\n          path: build/perf-gate-receipt.json\n          if-no-files-found: error\n          retention-days: 7\n")], "artifact-flow"),
        _m("release attacher takes attached evidence on every run", rel, "  attach-v02-evidence:\n",
           ATTACH_REUSE_GUARD, "if true; then", "attach-reuse-unguarded"),
        _m("release attacher retry flag is a constant", rel, "  attach-v02-evidence:\n",
           "      RETRY: ${{ inputs.retry }}", "      RETRY: 'true'", "attach-reuse-env"),
        _m("release attacher reuse block uploads", rel, "  attach-v02-evidence:\n",
           '                cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"',
           '                cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n                gh release upload "$RELEASE_TAG" "$dir/$name" --clobber --repo "$GH_REPO"', "attach-reuse-write"),
        _m("rehearsal aggregate verifies fuzz as the hosted release does", reh, "  aggregate:\n",
           '"$RUNNER_TEMP/source-archive.tar.gz" --rehearsal', '"$RUNNER_TEMP/source-archive.tar.gz"', "required-command-not-executed"),
        _m("rehearsal judge verifies the fuzz receipt without its source", reh, "  judge:\n",
           ' --source-sha "$GITHUB_SHA"', "", "required-command-not-executed"),
        _m("release passes --rehearsal to the evidence gate", "lifecycle", "# BEGIN validate-evidence\n",
           '"$RUNNER_TEMP/source-archive.tar.gz"\n# END validate-evidence',
           '"$RUNNER_TEMP/source-archive.tar.gz" --rehearsal\n# END validate-evidence', "rehearsal-flag-scope"),
        _m("a rehearsal producer job passes --rehearsal", reh, "  fuzz:\n",
           "run-bounded-fuzz.sh --self-test", "run-bounded-fuzz.sh --self-test --rehearsal", "rehearsal-flag-scope"),
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
        _m("rehearsal perf-gate deterministic and realtime gate removed", reh, "  perf-gate:\n",
         "bash tests/scripts/run-perf-gate.sh --gate", "true", "required-command-not-executed"),
        _m("rehearsal perf-gate seeded-regression control removed", reh, "  perf-gate:\n",
         "bash tests/scripts/run-perf-gate.sh --seeded-regression", "true", "required-command-not-executed"),
        # Planning-only lane (16-04, D-21): each mutation removes one piece of the fail-toward-full wiring.
        _m("classifier step stops reading the base commit's copy", "ci.yml", "  changes:\n",
           'git show "$base:.github/scripts/classify-changes.py" > "$RUNNER_TEMP/classify-changes.py"',
           'cat .github/scripts/classify-changes.py > "$RUNNER_TEMP/classify-changes.py"', "classifier-source"),
        _m("classifier step runs the head's own copy", "ci.yml", "  changes:\n",
           'python3 -I "$RUNNER_TEMP/classify-changes.py"', 'python3 -I .github/scripts/classify-changes.py', "classifier-source"),
        _m("heavy job loses the kind condition", "ci.yml", "  perf-gate:\n", "    if: needs.changes.outputs.kind == 'full'\n", "",
           "planning-lane-condition"),
        _m("heavy job runs for kind planning", "ci.yml", "  native-windows:\n", "kind == 'full'", "kind == 'planning'", "planning-lane-condition"),
        _m("heavy job stops needing changes", "ci.yml", "  cmake-floor-3-25-3:\n", "    needs: changes\n", "", "planning-lane-condition"),
        _m("native macOS state pin lane is missing", "ci.yml", "", "  native-macos:\n", "  native-macos-disabled:\n", "workflow-job-missing"),
        _m("native state pin ratchet uses its own source as the base", "ci.yml", "  native-linux:\n",
           '-DGBB_STATE_PIN_BASE_REV="$STATE_PIN_BASE"', '-DGBB_STATE_PIN_BASE_REV="$GITHUB_SHA"',
           "state-pin-base"),
        _m("ordinary push state pin base bypasses its event before SHA", "ci.yml", "  native-linux:\n",
           'base="$PUSH_BEFORE"', 'base=$(git merge-base HEAD origin/main)', "state-pin-base"),
        # WR-C05: an unreachable push parent (a rebase or force-push) must fall back to the merge base, not fail.
        _m("WR-C05 state pin base fails on an unreachable push parent", "ci.yml", "  native-macos:\n",
           'if [ -z "${base//0/}" ] || ! git cat-file -e "${base}^{commit}"; then', 'if [ -z "${base//0/}" ]; then',
           "state-pin-base"),
        # WR-C02: every token kept, but the resolved base is replaced by HEAD (the ratchet compares HEAD with itself).
        _m("WR-C02 state pin base overwritten with HEAD after validation", "ci.yml", "  native-windows:\n",
           'echo "base=$base" >> "$GITHUB_OUTPUT"', 'base=$(git rev-parse HEAD)\n{I}echo "base=$base" >> "$GITHUB_OUTPUT"',
           "state-pin-base"),
        _m("WR-C02 state pin base gains an environment override", "ci.yml", "  native-linux:\n",
           "          PUSH_BEFORE: ${{ github.event.before }}\n        run: |\n          if [ \"$EVENT_NAME\"",
           "          PUSH_BEFORE: ${{ github.event.before }}\n          BASH_ENV: build/override.sh\n        run: |\n          if [ \"$EVENT_NAME\"",
           "state-pin-base"),
        _m("native state pin target is replaced by its controls test", "ci.yml", "  native-linux:\n",
           "state_portable_pins", "state_pin_controls", "state-pin-target"),
        _m("native installed consumer route drops its inventory gate", "ci.yml", "  native-linux:\n",
           "--installed", "", "required-command-not-executed"),
        _m("required-native loses if: always()", "ci.yml", "  required-native:\n", "    if: always()\n", "", "workflow-dependency"),
        _m("required-native stops waiting for planning-checks", "ci.yml", "  required-native:\n", "      - planning-checks\n", "", "workflow-dependency"),
        _m("required-native stops reading the classification", "ci.yml", "  required-native:\n",
           "          KIND: ${{ needs.changes.outputs.kind }}\n", "", "workflow-dependency"),
        _m("required-native stops running the aggregator script", "ci.yml", "  required-native:\n",
           "python3 -I .github/scripts/check-required-native.py", "true", "required-command-not-executed"),
        _m("changes job gains a write permission", "ci.yml", "  changes:\n", "    permissions:\n      contents: read\n",
           "    permissions:\n      contents: write\n", "producer-write-authority"),
        _m("planning-checks job gains a write permission", "ci.yml", "  planning-checks:\n", "    permissions:\n      contents: read\n",
           "    permissions:\n      contents: write\n", "producer-write-authority"),
        _m("planning-checks stops running the planning label", "ci.yml", "  planning-checks:\n", "-L planning", "-L unit",
           "required-command-not-executed"),
        _m("planning-checks runs for every kind", "ci.yml", "  planning-checks:\n", "    if: needs.changes.outputs.kind == 'planning'\n", "",
           "planning-lane"),
        _m("ci gains pull_request_target", "ci.yml", "", "  push:\n", "  pull_request_target:\n  push:\n", "workflow-trigger"),
        _m("required-native stops waiting for perf-gate", "ci.yml", "  required-native:\n", "      - perf-gate\n", "", "workflow-dependency"),
        _m("required-native ignores the perf-gate result", "ci.yml", "  required-native:\n",
           "          PERF_GATE: ${{ needs.perf-gate.result }}\n", "", "workflow-dependency"),
        _m("ci perf-gate gate command replaced by echo", "ci.yml", "  perf-gate:\n",
           "run: bash tests/scripts/run-perf-gate.sh --gate", "run: echo bash tests/scripts/run-perf-gate.sh --gate",
           "required-command-not-executed"),
        _m("ci budget ratchet drops --base", "ci.yml", "  native-linux:\n",
           'python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --base "$BUDGET_BASE" --repo "$GITHUB_WORKSPACE"',
           'python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --repo "$GITHUB_WORKSPACE"',
           "required-command-not-executed"),
        _m("ci budget ratchet runs the head copy instead of the base copy", "ci.yml", "  native-linux:\n",
           'python3 -I "$RUNNER_TEMP/verify-test-budget.py" --build-dir build --base "$BUDGET_BASE" --repo "$GITHUB_WORKSPACE"',
           'python3 -I tests/scripts/verify-test-budget.py --build-dir build --base "$BUDGET_BASE"', "required-command-not-executed"),
        _m("ci budget checker self-test is removed", "ci.yml", "  native-linux:\n",
           "python3 -I tests/scripts/verify-test-budget.py --self-test", "echo budget self-test removed",
           "required-command-not-executed"),
        _m("ci budget base loses the unreachable-parent fallback", "ci.yml", "      - name: Resolve the per-test budget base commit\n",
           ' || ! git cat-file -e "${base}^{commit}"; then', "; then", "budget-base-fallback"),
        _m("ci budget base stops failing closed", "ci.yml", "      - name: Resolve the per-test budget base commit\n",
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
        _m("nightly report step loses its timeout", "nightly-asan.yml", "  report-red:\n", "        timeout-minutes: 5\n", "", "nightly-report-timeout"),
        _m("nightly report step timeout is an hour", "nightly-asan.yml", "  report-red:\n", "        timeout-minutes: 5", "        timeout-minutes: 60", "nightly-report-timeout"),
        _m("nightly report job loses its ledgered timeout", "nightly-asan.yml", "  report-red:\n", "    runs-on: ubuntu-24.04\n    timeout-minutes: 5\n",
           "    runs-on: ubuntu-24.04\n", "timeout-ledger-stale"),
        _m("nightly report dedupes on a title phrase search", "nightly-asan.yml", "  report-red:\n",
           "--state open --label", "--state open --search \"$ISSUE_TITLE in:title\" --label", "nightly-report-dedupe"),
        _m("nightly report matches the title as a substring", "nightly-asan.yml", "  report-red:\n",
           "select(.title == env.ISSUE_TITLE and", "select((.title | contains(env.ISSUE_TITLE)) and", "nightly-report-dedupe"),
        _m("nightly report ignores the label when matching", "nightly-asan.yml", "  report-red:\n",
           " and any(.labels[]; .name == env.ISSUE_LABEL))]", ")]", "nightly-report-dedupe"),
        _m("nightly report lists without the label filter", "nightly-asan.yml", "  report-red:\n",
           '--state open --label "$ISSUE_LABEL" --limit', "--state open --limit", "nightly-report-dedupe"),
        _m("nightly report creates the issue without the label", "nightly-asan.yml", "  report-red:\n",
           'issue_write issue create --title "$ISSUE_TITLE" --label "$ISSUE_LABEL"', 'issue_write issue create --title "$ISSUE_TITLE"', "nightly-report-dedupe"),
        _m("nightly report title is another phrase", "nightly-asan.yml", "  report-red:\n",
           'ISSUE_TITLE: "nightly-red: asan-full-replay"', 'ISSUE_TITLE: "nightly-red"', "nightly-report-body"),
        _m("nightly report label is another label", "nightly-asan.yml", "  report-red:\n",
           "ISSUE_LABEL: nightly-red", "ISSUE_LABEL: bug", "nightly-report-body"),
        _m("nightly report dry-run flag is ignored", "nightly-asan.yml", "  report-red:\n",
           "DRY_RUN: ${{ inputs.report_red_dry_run && 'true' || 'false' }}", "DRY_RUN: 'false'", "nightly-report-body"),
        _m("nightly report writes the issue outside the recording wrapper", "nightly-asan.yml", "  report-red:\n",
           'issue_write issue comment "$number" --body "$body"', 'gh issue comment "$number" --body "$body"', "nightly-report-dedupe"),
        _m("nightly report wrapper always sends", "nightly-asan.yml", "  report-red:\n",
           'if [ "$DRY_RUN" = true ]; then', 'if [ "$DRY_RUN" = never ]; then', "nightly-report-dry-run"),
        _m("nightly report swallows a failed write", "nightly-asan.yml", "  report-red:\n",
           '              gh "$@"\n', '              gh "$@" || true\n', "nightly-report-dry-run"),
        _m("nightly report step continues on error", "nightly-asan.yml", "  report-red:\n",
           "        timeout-minutes: 5\n", "        timeout-minutes: 5\n        continue-on-error: true\n", "ignored-gate"),
        _m("nightly report runs on every success too", "nightly-asan.yml", "  report-red:\n",
           "if: ${{ failure() || (always() && inputs.report_red_dry_run) }}", "if: ${{ always() }}", "nightly-report-trigger"),
        _m("nightly report no longer needs the replay", "nightly-asan.yml", "  report-red:\n",
           "    needs: asan-full-replay\n", "", "nightly-report-trigger"),
        _m("nightly replay can be skipped by anything", "nightly-asan.yml", "  asan-full-replay:\n",
           "if: ${{ !inputs.report_red_dry_run }}", "if: ${{ github.event_name == 'schedule' }}", "nightly-replay-trigger"),
        _m("nightly dispatch gains a free-form input", "nightly-asan.yml", "",
           "        default: false\n", "        default: false\n      note:\n        description: x\n        type: string\n", "workflow-trigger"),
        _m("nightly dry run defaults to on", "nightly-asan.yml", "", "        default: false\n", "        default: true\n", "workflow-trigger"),
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
        _m("libbet-repro checkout persists credentials", "libbet-repro.yml", "  libbet-repro:\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("perf-attribution dry run before cachegrind work removed", "perf-attribution.yml", "  attribution:\n",
           "run: bash tests/scripts/run-perf-gate.sh --attribution-dry-run", "run: true", "required-command-not-executed"),
        _m("rehearsal fuzz artifact no longer retained", reh, "  fuzz:\n", "name: " + REHEARSAL_FUZZ_ARTIFACT,
         "name: renamed-" + REHEARSAL_FUZZ_ARTIFACT, "artifact-flow"),
        _m("rehearsal checkout persists credentials", reh, "  corpus:\n", "persist-credentials: false",
         "persist-credentials: true", "checkout-credentials"),
        _m("unpinned action", reh, "", "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
         "actions/upload-artifact@v4", "workflow-unpinned-action"),
        _m("YAML anchor", reh, "", "  cancel-in-progress: true\n", "  cancel-in-progress: &stop true\n", "workflow-unsupported-yaml"),
        _m("release corpus producer gains contents: write", rel, "  candidate-corpus:\n", "      contents: read\n",
         "      contents: write\n", "producer-write-authority"),
        _m("release corpus producer receives the job token", rel, "  candidate-corpus:\n", "    env:\n",
         "    env:\n      GH_TOKEN: ${{ github.token }}\n", "producer-token"),
        _m("release performance checkout persists credentials", rel, "  candidate-performance:\n",
         "persist-credentials: false", "persist-credentials: true", "checkout-credentials"),
        _m("release candidate rehearsal binding call removed", rel, "  candidate:\n",
           REHEARSAL_BIND_COMMAND, "true", "required-command-not-executed"),
        _m("release candidate rehearsal binding loses --pr-head", rel, "  candidate:\n",
           REHEARSAL_BIND_COMMAND, REHEARSAL_BIND_COMMAND.replace(' --pr-head "$PR_HEAD_SHA"', ""),
           "required-command-not-executed"),
        _m("release candidate rehearsal binding loses --merged-at", rel, "  candidate:\n",
           REHEARSAL_BIND_COMMAND, REHEARSAL_BIND_COMMAND.replace(' --merged-at "$PR_MERGED_AT"', ""),
           "required-command-not-executed"),
        _m("release candidate rehearsal binding loses --attempt-jobs", rel, "  candidate:\n",
           REHEARSAL_BIND_COMMAND,
           REHEARSAL_BIND_COMMAND.replace(' --attempt-jobs "$RUNNER_TEMP/rehearsal-attempt-jobs.json"', ""),
           "required-command-not-executed"),
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
        _m("rehearsal judge tag-existence refusal removed", reh, "  judge:\n", REHEARSAL_TAG_EXISTS_STEP, "",
           "rehearsal-tag-exists"),
        _m("step disabled with if false", "release-rehearsal.yml", "  judge:\n", JUDGE_STEP, JUDGE_STEP + "        if: ${{ false }}\n", "disabled-gate"),
        _m("judge job disabled with if false", "release-rehearsal.yml", "  judge:\n", "    runs-on: ubuntu-24.04\n", "    if: ${{ false }}\n    runs-on: ubuntu-24.04\n", "disabled-gate"),
        _m("trusted judge checkout loses full history", "release-rehearsal.yml", "  judge:\n",
           "          path: trusted-judge\n          fetch-depth: 0\n", "          path: trusted-judge\n", "judge-history-shallow"),
        _m("release-head judge call loses explicit git root", "release-rehearsal.yml", "  judge:\n",
           JUDGE_CALL, JUDGE_CALL.removesuffix(" --git-root trusted-judge"), "required-command-not-executed"),
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
           "      - name: Reuse the qualified rehearsal receipt of this exact tree, else measure the clean paired v0.1.0 baseline and exact-tag candidate\n",
           "      - name: Reuse the qualified rehearsal receipt of this exact tree, else measure the clean paired v0.1.0 baseline and exact-tag candidate\n        if: ${{ false }}\n", "disabled-gate"),
        _m("rehearsal dispatch restores ordinary timing approval input", reh, "  workflow_dispatch:\n", "permissions:\n",
           "    inputs:\n      performance_decision:\n        required: false\n        type: string\npermissions:\n", "performance-advisory-path"),
        *[_m(f"rehearsal {job} restores an ordinary timing decision", reh, f"  {job}:\n",
             "          bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json\n",
             "          bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json\n          python3 -I tests/scripts/verify-v02-performance.py --apply-decision --measurement m --decision d --output build/v02-performance-receipt.json\n",
             "performance-advisory-path") for job in ("performance", "aggregate")],
        *[_m(f"rehearsal {job} gains actions: write", reh, f"  {job}:\n", "      contents: read\n",
             "      contents: read\n      actions: write\n", "producer-write-authority")
          for job in ("performance", "aggregate")],
        *[_m(f"rehearsal {job} gains actions: read", reh, f"  {job}:\n", "      contents: read\n",
             "      contents: read\n      actions: read\n", "producer-permissions")
          for job in ("performance", "aggregate")],
        _m("rehearsal performance receipt retained only on success", reh, "  performance:\n", "        if: ${{ always() }}\n", "", "artifact-flow"),
        _m("release candidate performance route requires the advisory verifier", "release.yml", "  candidate-performance:\n",
           "python3 -I tests/scripts/verify-v02-performance.py --verify build/v02-performance-receipt.json",
           "true", "required-command-not-executed"),
        _m("release candidate performance route adds timing review approval", "release.yml", "  candidate-performance:\n",
           "bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json",
           "bash tests/scripts/measure-release-baseline.sh --qualify-v02 --output build/v02-performance-receipt.json\n            python3 -I tests/scripts/verify-v02-performance.py --apply-decision --measurement m --decision d --output build/v02-performance-receipt.json",
           "performance-advisory-path"),
        _m("rehearsal judge stops cross-checking the tree version", reh, "  judge:\n", '--derive-rehearsal-tag "$GITHUB_REF_NAME" --root subject',
           '--derive-rehearsal-tag "rehearsal/v0.2.0" --root subject', "required-command-not-executed"),
        _m("rehearsal corpus falls back to a fixed tag", reh, "  corpus:\n", '--derive-rehearsal-tag "$GITHUB_REF_NAME"',
           '--derive-rehearsal-tag "rehearsal/v0.2.0"', "required-command-not-executed"),
        _m("release reuses a rehearsal receipt without --verify-reuse", "release.yml", "  candidate-performance:\n",
           '--verify-reuse "$found" --tag-tree "$tag_tree"', '--verify "$found"', "performance-reuse-unbound"),
        _m("release reuse compares against the wrong tree", "release.yml", "  candidate-performance:\n",
           'tag_tree=$(git rev-parse "$SOURCE_SHA^{tree}")', 'tag_tree=$(git rev-parse "HEAD^{tree}")', "performance-reuse-unbound"),
        _m("release fetches the receipt from any branch", "release.yml", "  candidate-performance:\n",
           "runs?branch=rehearsal/$RELEASE_TAG&", "runs?branch=main&", "performance-reuse-unbound"),
        _m("release fetches the receipt of an unsuccessful run", "release.yml", "  candidate-performance:\n",
           "&status=success&", "&status=failure&", "performance-reuse-unbound"),
        _m("release picks the newest run without judging it", "release.yml", "  candidate-performance:\n",
           'if run_id=$(python3 -I "$RUNNER_TEMP/verify-release-source-proof.py" --select-performance-run "$RUNNER_TEMP/rehearsal-runs.json"',
           'if run_id=$(jq -r ".workflow_runs[0].id" "$RUNNER_TEMP/rehearsal-runs.json"; true',
           "performance-reuse-unbound"),
        _m("release judges the run with the tagged tree's copy", "release.yml", "  candidate-performance:\n",
           'if run_id=$(python3 -I "$RUNNER_TEMP/verify-release-source-proof.py"', "if run_id=$(python3 -I .github/scripts/verify-release-source-proof.py",
           "performance-reuse-unbound"),
        _m("release stops binding the run to the tag source", "release.yml", "  candidate-performance:\n",
           '--tag "$RELEASE_TAG" --source-sha "$SOURCE_SHA" --repo', '--tag "$RELEASE_TAG" --source-sha "$GITHUB_SHA" --repo',
           "performance-reuse-unbound"),
        _m("release downloads any rehearsal artifact of the run", "release.yml", "  candidate-performance:\n",
           '--name "$artifact"', "--pattern 'rehearsal-performance-*'", "performance-reuse-unbound"),
        _m("release skips the artifact binding", "release.yml", "  candidate-performance:\n",
           'if artifact=$(python3 -I "$RUNNER_TEMP/verify-release-source-proof.py" --select-performance-artifact',
           'if artifact=$(echo rehearsal-performance-x; true', "performance-reuse-unbound"),
        _m("release swallows a refused selection", "release.yml", "  candidate-performance:\n",
           '--selected-run "$RUNNER_TEMP/rehearsal-run.json"); then', '--selected-run "$RUNNER_TEMP/rehearsal-run.json" || true); then',
           "performance-reuse-unbound"),
        _m("release fetch step gains a write API call", "release.yml", "  candidate-performance:\n",
           'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n', 'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n          gh api -X POST "repos/$GITHUB_REPOSITORY/issues" -f title=x\n',
           "producer-write-command"),
        _m("release fetch step reads an unlisted API path", "release.yml", "  candidate-performance:\n",
           'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n', 'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n          gh api "repos/$GITHUB_REPOSITORY/issues?per_page=100" > x\n',
           "producer-write-command"),
        _m("release performance job gains actions: write", "release.yml", "  candidate-performance:\n", "      actions: read\n", "      actions: write\n",
           "producer-write-authority"),
        _m("release performance job gains contents: write", "release.yml", "  candidate-performance:\n", "      actions: read\n", "      actions: read\n      pull-requests: write\n",
           "producer-write-authority"),
        _m("release fetch step runs tagged code while holding the token", "release.yml", "  candidate-performance:\n",
           'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n', 'mkdir -p "$RUNNER_TEMP/rehearsal-performance"\n          bash tests/scripts/measure-release-baseline.sh\n', "producer-token"),
        _m("release attacher upload commented out", "release.yml", "  attach-v02-evidence:\n", 'gh release upload "$RELEASE_TAG" "$1/$2"',
           '# gh release upload "$RELEASE_TAG" "$1/$2"', "required-command-not-executed"),
        _m("release manifest judge call replaced by echo", "release.yml", "  candidate-platform-manifest:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence',
           'echo bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence', "required-command-not-executed"),
        _m("release manifest judge taken from the subject checkout", "release.yml", "  candidate-platform-manifest:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-v02-evidence',
           'bash .github/scripts/verify-release-gates.sh --check-v02-evidence', "subject-judge-execution"),
        _m("release manifest trusted checkout points at the tag", "release.yml", "  candidate-platform-manifest:\n", "          ref: ${{ github.sha }}\n          path: trusted",
           "          ref: ${{ env.SOURCE_SHA }}\n          path: trusted", "judge-trust"),
        _m("release publisher final gate taken from the subject checkout", "release.yml", "  publish-qualified-release:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final',
           'bash .github/scripts/verify-release-gates.sh --check-draft-final', "subject-judge-execution"),
        _m("release publisher published-asset verifier taken from the subject checkout", "release.yml", "  publish-qualified-release:\n", "python3 -I trusted/.github/scripts/verify-published-release-assets.py",
           "python3 .github/scripts/verify-published-release-assets.py", "subject-judge-execution"),
        ("release publication runs before the final downloaded-byte gate", "release.yml", [
            ("  publish-qualified-release:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"', "true"),
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
        _m("preview player wait stops excusing the planning skip", "preview.yml", "  player-package-smoke-macos:\n",
           "          --planning-skippable macos-player-package\n", "", "preview-player-lane"),
        _m("preview player wait also excuses required-native", "preview.yml", "  player-package-smoke-macos:\n",
           "--planning-skippable macos-player-package", "--planning-skippable macos-player-package --planning-skippable required-native",
           "preview-player-lane"),
        _m("preview player wait stops requiring macos-player-package", "preview.yml", "  player-package-smoke-macos:\n",
           "--require required-native --require macos-player-package", "--require required-native", "preview-player-lane"),
        _m("preview player download guard inverted", "preview.yml", "      - name: Download run-scoped candidate package\n",
           "kind != 'planning'", "kind == 'planning'", "preview-player-lane"),
        _m("preview player byte verification no longer guarded", "preview.yml", "      - name: Verify downloaded package bytes and create consumer receipt\n",
           "        if: steps.candidate.outputs.kind != 'planning'\n", "", "preview-player-lane"),
        _m("preview player upload guard made unconditional", "preview.yml", "      - name: Upload qualified macOS player preview and receipt\n",
           "kind != 'planning'", "kind != 'planning' || true", "preview-player-lane"),
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
        _m("candidate skips the exact-source active version-window check", rel, "  candidate:\n",
           VERSION_WINDOW_SOURCE_CALL, "true", "required-command-not-executed"),
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
            ("  publish-qualified-release:\n", 'bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"', "true"),
            ("  publish-qualified-release:\n", 'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag',
             'gh release edit "$RELEASE_TAG" --repo "$GH_REPO" --draft=false --verify-tag\n{I}bash trusted/.github/scripts/verify-release-gates.sh --check-draft-final "$RELEASE_ID" "$RELEASE_TAG" "$SOURCE_SHA"')],
         "publication-order"),
        _m("W6-16 published asset verifier neutered", rel, "  publish-qualified-release:\n",
           'python3 -I trusted/.github/scripts/verify-published-release-assets.py "$assets" build/release-final/api-assets.json',
           'python3 -I trusted/.github/scripts/verify-published-release-assets.py --help "$assets" build/release-final/api-assets.json',
           "required-command-not-executed"),
        _m("W6-19 entrypoint stops calling release.yml", "release-please.yml", "", "uses: ./.github/workflows/release.yml",
           "uses: ./.github/workflows/release-renamed.yml", "release-entrypoint"),
        # RM-030 (17-11): the nightly gate and the owner-approval gate are called by the real paths, in order, from the trusted revision.
        _m("G17-01 workflow stops calling the nightly gate", rel, "  publish-qualified-release:\n",
           "run: bash trusted/.github/scripts/release-evidence-lifecycle.sh nightly-gate", "run: true", "lifecycle-wiring"),
        _m("G17-02 nightly gate replaced by echo", "lifecycle", "# BEGIN nightly-gate\n",
           "python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate", "echo python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate",
           "required-command-not-executed"),
        _m("G17-03 nightly gate taken from the tagged checkout", "lifecycle", "# BEGIN nightly-gate\n",
           "python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate", "python3 -I tests/scripts/verify-release-gates.py --nightly-gate",
           "token-subject-execution"),
        _m("G17-04 nightly gate failure swallowed", "lifecycle", "# BEGIN nightly-gate\n",
           '--output "$RUNNER_TEMP/nightly-gate-receipt.json"\n', '--output "$RUNNER_TEMP/nightly-gate-receipt.json" || true\n',
           "required-command-not-executed"),
        _m("G17-05 nightly gate loses the tagged-source binding", "lifecycle", "# BEGIN nightly-gate\n",
           ' --rev "$SOURCE_SHA" --branch', ' --branch', "required-command-not-executed"),
        _m("G17-06 nightly gate loses the rehearsal branch filter", "lifecycle", "# BEGIN nightly-gate\n",
           ' --branch "rehearsal/$RELEASE_TAG" --output', ' --output', "required-command-not-executed"),
        _m("G17-07 nightly gate judges a different head than the rehearsed one", "lifecycle", "# BEGIN nightly-gate\n",
           '--head "$head" --rev', '--head "$SOURCE_SHA" --rev', "required-command-not-executed"),
        ("G17-08 nightly gate moved after the publication transition", "lifecycle", [
            ("# BEGIN nightly-gate\n", "python3 -I trusted/tests/scripts/verify-release-gates.py --nightly-gate", "echo skipped")],
         "required-command-not-executed"),
        _m("G17-09 publisher gains actions: write", rel, "  publish-qualified-release:\n", "      actions: read\n", "      actions: write\n",
           "nightly-gate-permissions"),
        _m("G17-10 publisher loses actions: read", rel, "  publish-qualified-release:\n", "      actions: read\n", "", "nightly-gate-permissions"),
        # WR-C01: generic rules over every workflow file.
        _m("WR-C01 release-please caller forwards secrets", "release-please.yml", "  release:\n", "    permissions:\n      actions: read\n",
           "    secrets: inherit\n    permissions:\n      actions: read\n", "workflow-secrets"),
        _m("WR-C01 release-please caller gains packages and id-token write", "release-please.yml", "  release:\n",
           "    permissions:\n      actions: read\n", "    permissions:\n      packages: write\n      id-token: write\n      actions: read\n",
           "workflow-write-permissions"),
        _m("WR-C01 release-please top level grants contents write", "release-please.yml", "", "permissions:\n  contents: read\n\njobs:",
           "permissions:\n  contents: write\n\njobs:", "workflow-write-permissions"),
        _m("WR-C01 release-please runs on pull_request_target", "release-please.yml", "", "on:\n  push:\n    branches: [main]\n",
           "on:\n  pull_request_target:\n  push:\n    branches: [main]\n", "workflow-trigger"),
        _m("WR-C01 rehearsal runs on workflow_run", "release-rehearsal.yml", "", "on:\n  push:\n",
           "on:\n  workflow_run:\n    workflows: [ci]\n  push:\n", "workflow-trigger"),
        _m("WR-C01 fixture-repro top level grants contents write", "fixture-repro.yml", "", "permissions:\n  contents: read\n",
           "permissions:\n  contents: write\n", "workflow-write-permissions"),
        _m("WR-C01 libbet-repro job grants contents write", "libbet-repro.yml", "  libbet-repro:\n", "    timeout-minutes: 20\n",
           "    timeout-minutes: 20\n    permissions:\n      contents: write\n", "workflow-write-permissions"),
        _m("WR-C01 ci run body interpolates the head ref", "ci.yml", "  perf-gate:\n", "          sudo apt-get update -qq\n",
           '          echo "${{ github.head_ref }}"\n          sudo apt-get update -qq\n', "run-expression"),
        _m("WR-C01 fixture-repro run body interpolates the PR title", "fixture-repro.yml", "", "        run: |\n",
           '        run: |\n          echo "${{ github.event.pull_request.title }}"\n', "run-expression"),
        # WR-C02: edits outside the mode regions that disable the gates while every region and dispatch line survives.
        _m("WR-C02 lifecycle overrides python3 after the top-level set", "lifecycle", "", "set -euo pipefail\n\nlifecycle_attach_evidence() {",
           "set -euo pipefail\npython3() { return 0; }\n\nlifecycle_attach_evidence() {", "lifecycle-wiring"),
        _m("WR-C02 lifecycle overrides bash before the dispatch", "lifecycle", "", '\ncase "${1:-}" in\n',
           '\nbash() { return 0; }\ncase "${1:-}" in\n', "lifecycle-wiring"),
        _m("WR-C02 lifecycle traps errors to success", "lifecycle", "", "set -euo pipefail\n\nlifecycle_attach_evidence() {",
           "set -euo pipefail\ntrap 'exit 0' ERR\n\nlifecycle_attach_evidence() {", "lifecycle-wiring"),
        _m("WR-C02 lifecycle dispatch gains an earlier nightly-gate arm", "lifecycle", "", '\ncase "${1:-}" in\n',
           '\ncase "${1:-}" in\n  nightly-gate) exit 0 ;;\n', "lifecycle-wiring"),
        _m("WR-C02 lifecycle exits between two mode functions", "lifecycle", "", "\n# END final-gate\n}\n",
           "\n# END final-gate\n}\nexit 0\n", "lifecycle-wiring"),
        _m("G17-11 owner approval gate no longer called", "perfgate", "", "python3 -I \"$GATES\" --review-approval", "python3 -I \"$GATES\" --digest", "release-gate-wiring"),
        _m("G17-12 a receipt is handed to the evaluator without the approval", "perfgate", "",
           "  if [[ -n \"${GBB_IR_EXCEPTION_COMMENT_JSON:-}\" || -n \"${GBB_IR_EXCEPTION_DECISION:-}\" ]]; then\n",
           "  if [[ -n \"${GBB_PERF_EXCEPTION_RECEIPT:-}\" ]]; then args+=(--exception-receipt \"$GBB_PERF_EXCEPTION_RECEIPT\"); fi\n"
           "  if [[ -n \"${GBB_IR_EXCEPTION_COMMENT_JSON:-}\" || -n \"${GBB_IR_EXCEPTION_DECISION:-}\" ]]; then\n", "release-gate-wiring"),
        _m("G17-13 approval refusal swallowed", "perfgate", "", '--repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}" ||',
           '--repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}" || true ||', "release-gate-wiring"),
        # CR-C01: the approval is bound to this repository, and no workflow may supply the approval inputs.
        _m("CR-C01-1 approval not bound to this repository", "perfgate", "", ' \\\n      --repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}" ||', " ||",
           "release-gate-wiring"),
        _m("CR-C01-2 approval bound to a repository the caller chose", "perfgate", "", '--repository "${GITHUB_REPOSITORY:-szTheory/gabbaboy}"',
           '--repository "${GBB_REVIEW_REPOSITORY:-szTheory/gabbaboy}"', "release-gate-wiring"),
        _m("CR-C01-3 ci perf-gate step sets the approval comment", "ci.yml", "  perf-gate:\n", "        run: bash tests/scripts/run-perf-gate.sh --gate\n",
           "        env:\n          GBB_IR_EXCEPTION_COMMENT_JSON: tests/data/approval-comment.json\n"
           "          GBB_IR_EXCEPTION_DECISION: tests/data/approval-decision.json\n        run: bash tests/scripts/run-perf-gate.sh --gate\n", "ir-exception-env"),
        _m("CR-C01-4 rehearsal perf-gate job sets the approval decision", "release-rehearsal.yml", "  perf-gate:\n", "    timeout-minutes: 40\n",
           "    timeout-minutes: 40\n    env:\n      GBB_IR_EXCEPTION_DECISION: tests/data/approval-decision.json\n", "ir-exception-env"),
        _m("CR-C01-5 ci workflow-level env sets the approval inputs", "ci.yml", "", "permissions:\n  contents: read\n",
           "env:\n  GBB_IR_EXCEPTION_COMMENT_JSON: c.json\n  GBB_IR_EXCEPTION_DECISION: d.json\npermissions:\n  contents: read\n", "ir-exception-env"),
        _m("CR-C01-6 ci writes the approval inputs to GITHUB_ENV", "ci.yml", "  perf-gate:\n", "          sudo apt-get update -qq\n",
           "          echo \"GBB_IR_EXCEPTION_DECISION=tests/data/d.json\" >> \"$GITHUB_ENV\"\n          sudo apt-get update -qq\n", "ir-exception-env"),
        _m("CR-C01-7 ci writes a split approval name to GITHUB_ENV", "ci.yml", "  perf-gate:\n", "          sudo apt-get update -qq\n",
           "          p=GBB_IR; echo \"${p}_EXCEPTION_COMMENT_JSON=c.json\" >> \"$GITHUB_ENV\"\n          sudo apt-get update -qq\n", "ir-exception-env"),
        _m("CR-C01-8 perf-attribution sets a lower-case approval name", "perf-attribution.yml", "", "permissions:\n",
           "env:\n  gbb_ir_exception_decision: d.json\npermissions:\n", "ir-exception-env"),
        _m("CR-C01-9 ci perf-gate step redefines the expected review repository", "ci.yml", "  perf-gate:\n",
           "        run: bash tests/scripts/run-perf-gate.sh --gate\n",
           "        env:\n          GITHUB_REPOSITORY: example-owner/example-repo\n        run: bash tests/scripts/run-perf-gate.sh --gate\n", "ir-exception-env"),
        _m("G17-14 evaluator never receives the derived receipt", "perfgate", "", 'args+=(--exception-receipt "$WORK/exception-receipt.json")', "true", "release-gate-wiring"),
        _m("G17-15 evaluator stops writing the measurement", "perfgate", "", '--emit-exception-measurement "$WORK/exception-measurement.json"', "", "release-gate-wiring"),
        _m("G17-16 approval bound to another head", "perfgate", "", '--rev "$head_revision" --output', '--rev "$V020_EXPECTED" --output', "release-gate-wiring"),
        _m("G17-17 ci perf-gate loses the release gate controls", "ci.yml", "  perf-gate:\n",
           'run: python3 -I tests/scripts/verify-release-gates.py --self-test --rev "$GITHUB_SHA"', "run: true", "required-command-not-executed"),
        _m("G17-18 rehearsal perf-gate loses the release gate controls", reh, "  perf-gate:\n",
           'run: python3 -I tests/scripts/verify-release-gates.py --self-test --rev "$GITHUB_SHA"', "run: true", "required-command-not-executed"),
        _m("G17-19 rehearsal release gate controls replaced by echo", reh, "  perf-gate:\n",
           'run: python3 -I tests/scripts/verify-release-gates.py --self-test --rev "$GITHUB_SHA"',
           'run: echo python3 -I tests/scripts/verify-release-gates.py --self-test --rev "$GITHUB_SHA"', "required-command-not-executed"),
        # RM-028 lifecycle extraction (17-09): extracted code must be executed by the workflow, from the trusted checkout, once.
        _m("L17-01 workflow stops calling an extracted mode", rel, "  publish-qualified-release:\n",
           "run: bash trusted/.github/scripts/release-evidence-lifecycle.sh publish-draft", "run: true", "lifecycle-wiring"),
        _m("L17-02 workflow calls one mode twice", rel, "  candidate-platform-manifest:\n",
           "release-evidence-lifecycle.sh validate-evidence", "release-evidence-lifecycle.sh build-manifest", "lifecycle-wiring"),
        _m("L17-03 workflow runs the lifecycle script from the tagged checkout", rel, "  attach-v02-evidence:\n",
           "bash trusted/.github/scripts/release-evidence-lifecycle.sh attach-evidence",
           "bash .github/scripts/release-evidence-lifecycle.sh attach-evidence", "lifecycle-wiring"),
        _m("L17-04 workflow calls a mode from another job", rel, "  attach-v02-evidence:\n",
           "release-evidence-lifecycle.sh attach-evidence", "release-evidence-lifecycle.sh publish-draft", "lifecycle-wiring"),
        _m("L17-05 lifecycle mode loses its end marker", "lifecycle", "", "# END final-gate\n", "", "lifecycle-wiring"),
        _m("L17-06 lifecycle dispatch drops a mode", "lifecycle", "", "  publish-draft) lifecycle_publish_draft ;;\n", "", "lifecycle-wiring"),
        _m("L17-07 lifecycle mode is not the body of its own function", "lifecycle", "", "lifecycle_final_gate() {\n# BEGIN final-gate",
           "lifecycle_other() {\n# BEGIN final-gate", "lifecycle-wiring"),
        # IN-01: the retry tamper check is independent and runs before attached bytes replace regenerated ones.
        _m("L17-08 retry tamper check removed", "lifecycle", "# BEGIN attach-evidence\n",
           ATTACH_TAMPER_CHECK + '\n', "true\n", "attach-tamper-order"),
        _m("L17-09 retry tamper check masked", "lifecycle", "# BEGIN attach-evidence\n",
           ATTACH_TAMPER_CHECK + '\n', ATTACH_TAMPER_CHECK + ' || true\n',
           "required-command-not-executed"),
        _m("L17-10 retry tamper check replaced by echo", "lifecycle", "# BEGIN attach-evidence\n",
           ATTACH_TAMPER_CHECK + '\n', "echo " + ATTACH_TAMPER_CHECK + "\n", "required-command-not-executed"),
        ("L17-11 retry tamper check moved after the reuse copy", "lifecycle", [
            ("# BEGIN attach-evidence\n", ATTACH_TAMPER_CHECK + '\n', "true\n"),
            ("# BEGIN attach-evidence\n", '      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n    fi\n  done\n',
             '      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n    fi\n  done\n  ' + ATTACH_TAMPER_CHECK + '\n')],
         "attach-tamper-order"),
        ("L17-12 retry tamper check moved after the recovery decision", "lifecycle", [
            ("# BEGIN attach-evidence\n", ATTACH_TAMPER_CHECK + '\n', "true\n"),
            ("# BEGIN attach-evidence\n", 'decision=$(cat "$RUNNER_TEMP/recovery-decision.txt")\n',
             'decision=$(cat "$RUNNER_TEMP/recovery-decision.txt")\n' + ATTACH_TAMPER_CHECK + '\n')],
         "attach-tamper-order"),
        _m("L17-13 retry tamper check taken from the tagged checkout", "lifecycle", "# BEGIN attach-evidence\n",
           ATTACH_TAMPER_CHECK, ATTACH_TAMPER_CHECK.replace("trusted/.github", ".github"), "attach-tamper-order"),
        _m("L17-14 retry copies the attachments twice", "lifecycle", "# BEGIN attach-evidence\n",
           '      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n',
           '      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n      cp "$RUNNER_TEMP/attached-$name/$name" "$dir/$name"\n', "attach-tamper-order"),
    ]



def _window_mutations():
    """Version-window gate wiring (RM-028): each defect must be rejected with its own code while the baseline passes."""
    rp = WINDOW_WORKFLOW
    window = f"  {WINDOW_JOB}:\n"
    return [
        _m("W17-01 window gate job removed", rp, "", window, "  version-window-renamed:\n", "window-gate-missing"),
        _m("W17-02 gate no longer waits for regeneration", rp, window, "needs: [release]", "needs: []", "window-gate-order"),
        _m("W17-03 gate skipped when the release job fails", rp, window, "if: ${{ !cancelled() && inputs.retry != true }}",
           "if: ${{ success() && inputs.retry != true }}", "window-gate-skipped"),
        _m("W17-04 gate disabled by a constant condition", rp, window, "if: ${{ !cancelled() && inputs.retry != true }}",
           "if: ${{ false }}", "window-gate-skipped"),
        _m("W17-05 gate gains write authority", rp, window, "pull-requests: read", "pull-requests: write", "window-gate-permissions"),
        _m("W17-06 version PR checkout persists credentials", rp, "path: version-pr\n", "persist-credentials: false",
           "persist-credentials: true", "checkout-credentials"),
        _m("W17-07 checker taken from the version PR head", rp, "name: Check out the trusted main commit\n", "ref: ${{ github.sha }}",
           "ref: ${{ steps.discover.outputs.head }}", "window-gate-trust"),
        _m("W17-08 version PR history shallow", rp, "path: version-pr\n", "fetch-depth: 0", "fetch-depth: 1", "window-gate-history"),
        _m("W17-09 step without a timeout", rp, "name: Judge the regenerated version PR against its frozen window\n",
           "        timeout-minutes: 5\n", "", "window-gate-timeout"),
        _m("W17-10 window validation call removed", rp, "Judge the regenerated version PR against its frozen window", WINDOW_CALL,
           'echo "window judged"', "required-command-not-executed"),
        _m("W17-11 fake green stale window (|| true)", rp, "Judge the regenerated version PR against its frozen window", WINDOW_CALL,
           WINDOW_CALL + " || true", "required-command-not-executed"),
        _m("W17-12 fake green stale window (continue-on-error)", rp, "name: Judge the regenerated version PR against its frozen window\n",
           "        timeout-minutes: 5\n", "        timeout-minutes: 5\n        continue-on-error: true\n", "ignored-gate"),
        _m("W17-13 judge compares against the PR head as base", rp, "Judge the regenerated version PR against its frozen window",
           '--base "$MAIN_SHA"', '--base "$PR_HEAD"', "required-command-not-executed"),
        _m("W17-14 judge stops reading the regenerated body", rp, "Judge the regenerated version PR against its frozen window",
           ' --body "$RUNNER_TEMP/version-pr-body.md"', "", "required-command-not-executed"),
        _m("W17-15 judge runs the version PR's own checker", rp, "Judge the regenerated version PR against its frozen window",
           "python3 -I trusted/tests/scripts/verify-version-window.py", "python3 -I version-pr/tests/scripts/verify-version-window.py",
           "required-command-not-executed"),
        _m("W17-16 release-please push trigger path-filtered", rp, "", "    branches: [main]\n",
           "    branches: [main]\n    paths-ignore: [CHANGELOG.md]\n", "window-trigger-filtered"),
        _m("W17-17 blanket path exclusion", "config", "", '"exclude-paths": [".github/workflows", ".github/scripts"]',
           '"exclude-paths": [".github/workflows", ".github/scripts", "."]', "window-path-excluded"),
        _m("W17-18 release-note path excluded", "config", "", '"exclude-paths": [".github/workflows", ".github/scripts"]',
           '"exclude-paths": [".github/workflows", ".github/scripts", "docs/support"]', "window-path-excluded"),
        _m("W17-19 changelog skipped", "config", "", '"include-v-in-tag": true,', '"include-v-in-tag": true,\n      "skip-changelog": true,',
           "window-config"),
        _m("W17-20 changelog path moved", "config", "", '"changelog-path": "CHANGELOG.md"', '"changelog-path": "docs/CHANGELOG.md"',
           "window-config"),
    ]


def _version_pr_gate_mutations():
    """The new pre-tag gate must be same-repository, read-only, trusted and fatal on both window and R2 defects."""
    workflow = VERSION_PR_WORKFLOW
    job = f"  {VERSION_PR_JOB}:\n"
    judge = f"name: {VERSION_PR_STEP_NAMES['window']}\n"
    return [
        _m("version PR gate uses pull_request_target", workflow, "on:\n", "  pull_request:\n",
           "  pull_request_target:\n", "version-pr-gate-trigger"),
        _m("version PR gate changes its trusted base to the PR head", workflow, "name: Check out the trusted PR base\n",
           "ref: ${{ github.event.pull_request.base.sha }}", "ref: ${{ github.event.pull_request.head.sha }}",
           "version-pr-gate-trust"),
        _m("version PR gate gains actions write permission", workflow, job, "      actions: read\n",
           "      actions: write\n", "version-pr-gate-permissions"),
        _m("version PR gate gains contents write permission", workflow, job, "      contents: read\n",
           "      contents: write\n", "version-pr-gate-permissions"),
        _m("version PR window judge loses its step timeout", workflow, judge,
           "        timeout-minutes: 5\n", "", "version-pr-gate-timeout"),
        _m("version PR window checker runs from the PR head", workflow, judge,
           "python3 -I trusted/tests/scripts/verify-version-window.py",
           "python3 -I version-pr/tests/scripts/verify-version-window.py", "version-pr-gate-trust"),
        _m("version PR gate ignores a failing window judge", workflow, judge,
           "        timeout-minutes: 5\n", "        timeout-minutes: 5\n        continue-on-error: true\n", "ignored-gate"),
        _m("version PR gate drops the R2 bind call", workflow, f"name: {VERSION_PR_STEP_NAMES['bind']}\n",
           VERSION_PR_BIND_CALL, "echo 'rehearsal omitted'", "required-command-not-executed"),
    ]


def _ledger_edit(fixture: Path, edit) -> None:
    path = fixture / LEDGER_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    edit(data)
    path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")


def _ledger_mutations():
    """(label, mutate(fixture), extra CLI args, expected code) for the timeout ledger, run through the CLI."""
    def yaml_edit(workflow: str, old: str, new: str):
        def apply(fixture: Path) -> None:
            path = fixture / ".github/workflows" / workflow
            text = path.read_text(encoding="utf-8")
            if old not in text:
                raise SystemExit(f"self-test anchor missing in {workflow}: {old[:50]!r}")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return apply

    def ledger(edit):
        return lambda fixture: _ledger_edit(fixture, edit)

    def bound_at(key: str, edit=None):
        def apply(fixture: Path) -> None:
            def set_bound(data: dict) -> None:
                row = {**bound, "timeout_minutes": data[key]["timeout_minutes"]}
                if edit is not None:
                    edit(row)
                data[key] = row
            _ledger_edit(fixture, set_bound)
        return apply

    def both(first, second):
        def apply(fixture: Path) -> None:
            first(fixture)
            second(fixture)
        return apply

    bound = {"timeout_minutes": 5, "release_bound": True, "provisional": False, "sizing_basis": "sized from a worst-case budget"}
    return [
        ("ledger: edited YAML timeout", yaml_edit("ci.yml", "    runs-on: ubuntu-22.04\n    timeout-minutes: 31\n", "    runs-on: ubuntu-22.04\n    timeout-minutes: 32\n"), (), "timeout-ledger-stale"),
        ("ledger: removed row", ledger(lambda d: d.pop("ci.yml:native-linux")), (), "timeout-ledger-missing-row"),
        ("ledger: p50 above half of the timeout", ledger(lambda d: d["ci.yml:native-linux"].update(p50_minutes="15.51")), (), "timeout-ledger-ratio"),
        ("ledger: stale ledger value", ledger(lambda d: d["ci.yml:native-linux"].update(timeout_minutes=29)), (), "timeout-ledger-stale"),
        ("ledger: new job with no row", yaml_edit("ci.yml", "\n  required-native:\n", "\n  extra-job:\n    runs-on: ubuntu-22.04\n    timeout-minutes: 5\n    steps:\n      - run: true\n\n  required-native:\n"), (), "timeout-ledger-missing-row"),
        ("ledger: row for a job that no longer exists", ledger(lambda d: d.update({"ci.yml:gone": dict(d["ci.yml:native-linux"])})), (), "timeout-ledger-stale"),
        ("ledger: duplicate key", lambda fixture: (fixture / LEDGER_PATH).write_text(
            (fixture / LEDGER_PATH).read_text(encoding="utf-8").replace('"ci.yml:native-linux": {', '"ci.yml:native-linux": {"samples": 1, "samples": 2, ', 1), encoding="utf-8"), (), "timeout-ledger-schema"),
        ("ledger: provisional row under --release-head", ledger(lambda d: d["ci.yml:native-linux"].update(provisional=True)), ("--release-head",), "timeout-ledger-provisional"),
        ("ledger: longest gating p50 of 30.1", both(yaml_edit("ci.yml", "timeout-minutes: 50\n", "timeout-minutes: 70\n"),
            ledger(lambda d: d["ci.yml:native-windows"].update(timeout_minutes=70, p50_minutes="30.1"))), (), "timeout-ledger-whole-run"),
        ("ledger: release_bound row under a different key", ledger(lambda d: d.update({"ci.yml:native-linux": {**bound, "timeout_minutes": 31}})), (), "timeout-ledger-release-bound"),
        ("ledger: release_bound row under a third key", ledger(lambda d: d["fixture-repro.yml:fixture-repro"].clear() or d["fixture-repro.yml:fixture-repro"].update({**bound, "timeout_minutes": 15})), (), "timeout-ledger-release-bound"),
        ("ledger: release_bound row once VERSION is above 0.2.1", both(bound_at("release-rehearsal.yml:judge"), lambda fixture: (fixture / "CMakeLists.txt").write_text(
            re.sub(r"VERSION \d+\.\d+\.\d+", "VERSION 0.3.0", (fixture / "CMakeLists.txt").read_text(encoding="utf-8"), count=1), encoding="utf-8")), (), "timeout-ledger-release-bound"),
        ("ledger: normal row with samples removed", ledger(lambda d: d["ci.yml:native-linux"].pop("samples")), (), "timeout-ledger-schema"),
        ("ledger: cited_tree without tree_equal_sha", ledger(lambda d: d["ci.yml:native-linux"].update(cited_tree="b" * 40)), (), "timeout-ledger-schema"),
        ("ledger: tree_equal_sha without cited_tree", ledger(lambda d: d["ci.yml:native-linux"].update(tree_equal_sha="b" * 40)), (), "timeout-ledger-schema"),
        ("ledger: unknown optional field", ledger(lambda d: d["ci.yml:native-linux"].update(sizing_note="not allowed")), (), "timeout-ledger-schema"),
        ("ledger: release_bound row that also cites a run", bound_at("release-rehearsal.yml:judge", lambda row: row.update(cited_run_id=1)), (), "timeout-ledger-schema"),
        ("ledger: release_bound row that is provisional", bound_at("release.yml:candidate-fuzz", lambda row: row.update(provisional=True)), (), "timeout-ledger-schema"),
        ("ledger: release_bound row without a sizing basis", bound_at("release.yml:attach-v02-evidence", lambda row: row.update(sizing_basis=" ")), (), "timeout-ledger-schema"),
        ("ledger: empty ledger", lambda fixture: (fixture / LEDGER_PATH).write_text("{}\n", encoding="utf-8"), (), "timeout-ledger-schema"),
    ]


def _ledger_boundary_controls() -> int:
    """In-process precision controls: Fraction arithmetic, never floats."""
    row = {"timeout_minutes": 25, "cited_run_id": 1, "cited_sha": "a" * 40, "p50_minutes": "12.4", "samples": 1, "provisional": False}
    done = 0

    def judge(overrides: dict, timeout: int = 25, gating: bool = False, version=(0, 2, 0), head: bool = False) -> None:
        merged = {**row, **overrides, "timeout_minutes": timeout}
        judge_timeout_ledger({"w.yml:j": merged}, {"w.yml:j": timeout}, {"w.yml:j"} if gating else set(), version, head)

    judge({})                                   # exactly ceil(2 x 12.4) = 25 passes
    done += 1
    judge({"tree_equal_sha": "b" * 40, "cited_tree": "c" * 40})
    done += 1
    for label, code, call in (
        ("timeout one minute below ceil(2 x p50) fails", "timeout-ledger-ratio", lambda: judge({}, timeout=24)),
        ("tree-equal row one minute below ceil(2 x p50) fails", "timeout-ledger-ratio",
         lambda: judge({"tree_equal_sha": "b" * 40, "cited_tree": "c" * 40}, timeout=24)),
        ("p50 of exactly 30 behind required-native passes", None, lambda: judge({"p50_minutes": "30"}, timeout=60, gating=True)),
        ("p50 of 30.1 behind required-native fails", "timeout-ledger-whole-run", lambda: judge({"p50_minutes": "30.1"}, timeout=61, gating=True)),
        ("p50 of 30.1 outside required-native passes", None, lambda: judge({"p50_minutes": "30.1"}, timeout=61)),
        ("a binary-float trap p50 of 0.1 + 0.2 style decimal is exact", None, lambda: judge({"p50_minutes": "12.500000000000000001"}, timeout=26)),
        ("a non-provisional row passes at the release head", None, lambda: judge({}, head=True)),
        ("a provisional row passes before the release head", None, lambda: judge({"provisional": True})),
        ("a provisional row fails at the release head", "timeout-ledger-provisional", lambda: judge({"provisional": True}, head=True)),
        ("a p50 given as a number is rejected", "timeout-ledger-schema", lambda: judge({"p50_minutes": 12.4})),
        ("a boolean samples count is rejected", "timeout-ledger-schema", lambda: judge({"samples": True})),
    ):
        try:
            call()
        except Reject as exc:
            if exc.code != code:
                raise SystemExit(f"self-test boundary {label!r}: wrong code {exc.code}")
        else:
            if code is not None:
                raise SystemExit(f"self-test boundary {label!r}: accepted")
        done += 1
    return done


def _ledger_git_object_controls() -> int:
    """Use injected Git results to pin each offline tree-equality refusal and default-ref behavior."""
    anchor = "a" * 40
    tree = "b" * 40
    commit = "c" * 40
    row = {"timeout_minutes": 45, "cited_run_id": 1, "cited_sha": "d" * 40,
           "p50_minutes": "0.14", "samples": 1, "provisional": False,
           "tree_equal_sha": anchor, "cited_tree": tree}

    def fake_git(anchor_tree: str = tree, ancestor_code: int = 0, unreadable_anchor: bool = False,
                 reject_origin: bool = False, calls: list | None = None):
        if calls is None:
            calls = []

        def invoke(*args: str, cwd: Path):
            calls.append(args)
            if reject_origin and any("origin/" in arg for arg in args):
                return subprocess.CompletedProcess(["git", *args], 1, "", "origin refs are forbidden in this control")
            if args[0] == "rev-parse":
                target = args[-1]
                if target == "HEAD^{commit}":
                    return subprocess.CompletedProcess(["git", *args], 0, commit, "")
                if target == "origin/main^{commit}":
                    return subprocess.CompletedProcess(["git", *args], 1, "", "unknown ref")
                if target == f"{anchor}^{{tree}}":
                    if unreadable_anchor:
                        return subprocess.CompletedProcess(["git", *args], 128, "", "missing object")
                    return subprocess.CompletedProcess(["git", *args], 0, anchor_tree, "")
            if args[0] == "merge-base":
                return subprocess.CompletedProcess(["git", *args], ancestor_code, "", "")
            raise SystemExit(f"unhandled fake git request: {args!r}")

        return invoke, calls

    done = 0
    valid, calls = fake_git(reject_origin=True)
    check_ledger_git_objects({"w.yml:j": row}, Path("."), "HEAD", False, git=valid)
    if any("origin/" in arg for call in calls for arg in call):
        raise SystemExit("self-test tree-equality default ref read origin/*")
    done += 1

    def expect(label: str, expected: str, invoke) -> None:
        try:
            invoke()
        except Reject as exc:
            if exc.code != expected:
                raise SystemExit(f"self-test git-object control {label!r}: wrong code {exc.code}")
        else:
            raise SystemExit(f"self-test git-object control {label!r}: accepted")

    mismatch, _ = fake_git(anchor_tree="e" * 40)
    expect("tree mismatch", "timeout-ledger-tree-mismatch",
           lambda: check_ledger_git_objects({"w.yml:j": row}, Path("."), "HEAD", False, git=mismatch))
    done += 1
    off_main, _ = fake_git(ancestor_code=1)
    expect("anchor not on main", "timeout-ledger-anchor-not-on-main",
           lambda: check_ledger_git_objects({"w.yml:j": row}, Path("."), "HEAD", False, git=off_main))
    done += 1
    missing, _ = fake_git(unreadable_anchor=True)
    expect("unreadable anchor", "timeout-ledger-git-unavailable",
           lambda: check_ledger_git_objects({"w.yml:j": row}, Path("."), "HEAD", False, git=missing))
    done += 1
    no_live_ref, _ = fake_git(reject_origin=True)
    expect("explicit origin ref is honored", "timeout-ledger-git-unavailable",
           lambda: check_ledger_git_objects({"w.yml:j": row}, Path("."), "origin/main", False, git=no_live_ref))
    done += 1
    return done


def _ledger_disclosure_scratch_controls() -> int:
    """Exercise changed, unchanged and disabled disclosure checks against a real scratch Git repository."""
    with tempfile.TemporaryDirectory(prefix="gbb-ledger-disclosure.") as directory:
        repo = Path(directory)
        workflow = repo / ".github/workflows/ci.yml"
        workflow.parent.mkdir(parents=True)
        base_text = ("name: fixture\n"
                     "jobs:\n"
                     "  build:\n"
                     "    runs-on: ubuntu-latest\n"
                     "    steps:\n"
                     "      - run: echo before\n"
                     "  stable:\n"
                     "    runs-on: ubuntu-latest\n"
                     "    steps:\n"
                     "      - run: echo stable\n")
        workflow.write_text(base_text, encoding="utf-8")
        env = os.environ.copy()
        env.update(GIT_AUTHOR_NAME="GabbaBoy Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="GabbaBoy Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")

        def git(*args: str) -> subprocess.CompletedProcess[str]:
            result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env, check=False, timeout=30)
            if result.returncode != 0:
                raise SystemExit(f"self-test disclosure scratch git failed: {' '.join(args)}: {result.stderr.strip()}")
            return result

        git("init", "-q", "--initial-branch=main")
        git("add", ".github/workflows/ci.yml")
        git("commit", "-q", "-m", "fixture base")
        changed_text = base_text.replace("echo before", "echo after", 1)
        workflow.write_text(changed_text, encoding="utf-8")

        def check(row: dict, key: str = "ci.yml:build", base: str | None = "main") -> None:
            check_ledger_git_objects({key: row}, repo, "HEAD", False,
                                     disclosure_base=base, workflow_root=repo)

        try:
            check({})
        except Reject as exc:
            if exc.code != "timeout-ledger-body-undisclosed":
                raise SystemExit(f"self-test disclosure scratch: wrong refusal {exc.code}")
        else:
            raise SystemExit("self-test disclosure scratch: changed job body without disclosure was accepted")
        check({"disclosure": "changed this job's body after the cited run"})
        check({}, key="ci.yml:stable")
        check({}, base=None)
    return 4


def _ledger_release_object_scratch_controls(root: Path, work: Path) -> int:
    """Prove release-head reads tree-equal commit objects but leaves merged-PR plain citations alone."""
    with tempfile.TemporaryDirectory(prefix="gbb-ledger-release-objects.") as directory:
        scratch = Path(directory)
        fixture = scratch / "subject"
        repo = scratch / "trusted-objects"
        _copy_fixture(root, fixture)
        cmake = fixture / "CMakeLists.txt"
        cmake_text = cmake.read_text(encoding="utf-8")
        bumped, replacements = re.subn(r"(project\(\s*\w+\s+VERSION\s+)\d+\.\d+\.\d+", r"\g<1>0.3.0", cmake_text, count=1)
        if replacements != 1:
            raise SystemExit("self-test release-object scratch: fixture VERSION could not be set to 0.3.0")
        cmake.write_text(bumped, encoding="utf-8")
        ledger_path = fixture / LEDGER_PATH
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"), object_pairs_hook=_ledger_pairs)
        tree_rows = [(key, row) for key, row in ledger.items() if "tree_equal_sha" in row]
        plain_rows = [(key, row) for key, row in ledger.items() if "tree_equal_sha" not in row]
        if not tree_rows or not plain_rows:
            raise SystemExit("self-test release-object scratch: live ledger needs tree-equal and plain rows")
        repo.mkdir()
        env = os.environ.copy()
        env.update(GIT_AUTHOR_NAME="GabbaBoy Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="GabbaBoy Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid",
                   GIT_CONFIG_GLOBAL=str(scratch / "gitconfig"), GIT_CONFIG_SYSTEM="/dev/null" if os.name != "nt" else "NUL")

        def git(*args: str, allow_failure: bool = False) -> subprocess.CompletedProcess[str]:
            result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, env=env,
                                    check=False, timeout=30)
            if result.returncode != 0 and not allow_failure:
                raise SystemExit(f"self-test release-object scratch git failed: {' '.join(args)}: {result.stderr.strip()}")
            return result

        git("init", "-q", "--initial-branch=main")
        (repo / "CMakeLists.txt").write_text(bumped, encoding="utf-8")
        git("add", "CMakeLists.txt")
        git("commit", "-q", "-m", "main anchor")
        anchor = git("rev-parse", "HEAD").stdout.strip()
        tree = git("rev-parse", "HEAD^{tree}").stdout.strip()
        cited = git("commit-tree", tree, "-p", anchor, "-m", "same-tree citation").stdout.strip()
        git("update-ref", "refs/heads/side", cited)
        for _, row in tree_rows:
            row.update(tree_equal_sha=anchor, cited_sha=cited, cited_tree=tree)
        plain_rows[0][1]["cited_sha"] = "f" * 40
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        script = Path(__file__).resolve()

        def check() -> subprocess.CompletedProcess[str]:
            return subprocess.run([sys.executable, "-I", str(script), "--check", "--release-head", "--root", str(fixture),
                                   "--git-root", str(repo), "--main-ref", "main"], cwd=work, capture_output=True,
                                  text=True, check=False, timeout=60)

        positive = check()
        if positive.returncode != 0 or "PASS: workflow privilege and trust wiring" not in positive.stdout:
            raise SystemExit(f"self-test release-object positive control failed: exit={positive.returncode} stderr={positive.stderr.strip()!r}")
        print("passed: release-head reads retained tree-equal citations and skips an unreadable plain citation")
        git("update-ref", "-d", "refs/heads/side")
        git("reflog", "expire", "--expire=now", "--all")
        git("gc", "--prune=now")
        if git("cat-file", "-e", f"{cited}^{{commit}}", allow_failure=True).returncode == 0:
            raise SystemExit("self-test release-object scratch: cited commit survived pruning")
        negative = check()
        expected = f"REJECT timeout-ledger-cited-object-missing: {tree_rows[0][0]}:"
        if negative.returncode != 1 or expected not in negative.stderr or "PASS:" in negative.stdout:
            raise SystemExit(f"self-test release-object negative control failed: exit={negative.returncode} stderr={negative.stderr.strip()!r}")
        print(f"rejected: pruned tree-equal cited object: {negative.stderr.strip()}")
    return 2


def verify_cited_stub_controls(root: Path, work: Path) -> int:
    """Verify online tree-equal and predecessor-name checks through a refusing gh stand-in."""
    if os.name == "nt":
        print("skipped: online citation gh stub (POSIX shell stand-in)")
        return 0
    ledger_path = root / LEDGER_PATH
    original = ledger_path.read_text(encoding="utf-8")
    data = json.loads(original, object_pairs_hook=_ledger_pairs)
    row = dict(data["release-rehearsal.yml:performance"])
    ledger_path.write_text(json.dumps({"release-rehearsal.yml:performance": row}, indent=1) + "\n", encoding="utf-8")
    stub_dir = work / "verify-cited-bin"
    stub_dir.mkdir(exist_ok=True)
    stub = stub_dir / "gh"
    stub.write_bytes(_VERIFY_CITED_STUB.encode("utf-8"))
    stub.chmod(0o755)
    env = {key: value for key, value in os.environ.items() if key in ("PATH", "TMPDIR", "HOME", "LANG")}
    env.update(PATH=f"{stub_dir}{os.pathsep}{env.get('PATH', '')}",
               STUB_HEAD_SHA="c6dc575b6a84cf51a56688948fce9241ba323400",
               STUB_JOB_NAME="rehearse-paired-performance-qualification",
               STUB_TREE="b02c14bbdc9be80b7aa6b6145cb8b89331388cca")

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--check", "--verify-cited", "--root", str(root)],
                              cwd=work, capture_output=True, text=True, check=False, env=env, timeout=60)

    controls = 0
    try:
        positive = run()
        if positive.returncode != 0 or "verify-cited rows=1 failures=0" not in positive.stdout:
            raise SystemExit(f"self-test verify-cited positive control failed: {positive.stdout!r} {positive.stderr!r}")
        controls += 1
        row["cited_job_name"] = "missing predecessor job"
        ledger_path.write_text(json.dumps({"release-rehearsal.yml:performance": row}, indent=1) + "\n", encoding="utf-8")
        missing_job = run()
        if missing_job.returncode != 1 or "FAIL release-rehearsal.yml:performance: job missing or not successful" not in missing_job.stdout:
            raise SystemExit(f"self-test verify-cited missing-job control failed: {missing_job.stdout!r} {missing_job.stderr!r}")
        controls += 1
        row["cited_job_name"] = "rehearse-paired-performance-qualification"
        ledger_path.write_text(json.dumps({"release-rehearsal.yml:performance": row}, indent=1) + "\n", encoding="utf-8")
        env["STUB_TREE"] = "e" * 40
        wrong_tree = run()
        if wrong_tree.returncode != 1 or "does not match cited_tree" not in wrong_tree.stdout:
            raise SystemExit(f"self-test verify-cited wrong-tree control failed: {wrong_tree.stdout!r} {wrong_tree.stderr!r}")
        controls += 1
    finally:
        ledger_path.write_text(original, encoding="utf-8")
    print("passed: online citation stub verifies tree-equal heads and refuses missing jobs and mismatched API trees")
    return controls


_LIFECYCLE_JOB_ANCHORS = {f"  {job}:\n": next(mode for mode, owner in LIFECYCLE_MODES.items() if owner == job) for job in set(LIFECYCLE_MODES.values())}
_JOB_HEADER = re.compile(r"\n  [a-z0-9-]+:\n")


def _outdent(text: str) -> str:
    """A step body sits ten columns deep in release.yml (a run block under a step) and at column zero in the script."""
    return "\n".join(line[10:] if line.startswith(" " * 10) else line for line in text.split("\n"))


def _route_lifecycle(workflow: str, edits, workflow_text: str, script_text: str):
    """A mutation written against release.yml whose anchor text now lives in the lifecycle script is applied to the script.

    The edit keeps its meaning (the same text in the same job, in the same order); only the file that holds the text moved
    with the extraction. An edit whose text is in neither file is a stale mutant and fails the self-test loudly."""
    if workflow != "release.yml":
        return workflow, edits
    routed, kept = [], []
    for after, old, replacement in edits:
        start = workflow_text.find(after) if after else 0
        end = len(workflow_text)
        if after in _LIFECYCLE_JOB_ANCHORS and start >= 0:
            following = _JOB_HEADER.search(workflow_text, start + len(after))
            end = following.start() if following else end
        if start >= 0 and 0 <= workflow_text.find(old, start) < end:
            kept.append((after, old, replacement))
        elif _outdent(old) in script_text:
            routed.append((f"# BEGIN {_LIFECYCLE_JOB_ANCHORS[after]}\n" if after in _LIFECYCLE_JOB_ANCHORS else "",
                           _outdent(old), _outdent(replacement)))
        else:
            kept.append((after, old, replacement))
    if routed and kept:
        raise SystemExit(f"self-test mutation mixes release.yml and lifecycle-script edits: {routed[0][1][:60]!r}")
    return ("lifecycle", routed) if routed else (workflow, edits)


def rehearsal_tag_guard_controls(root: Path) -> int:
    tree = read_workflow(root / ".github/workflows/release-rehearsal.yml")
    step = tree["jobs"]["judge"]["steps"][0]
    shell = step["run"]
    harness = '''
git() {
  printf '%s\\n' "$*" >> "$TAG_GIT_LOG"
  if [[ "$TAG_EXISTS" == true ]]; then
    printf '0123456789abcdef0123456789abcdef01234567\\trefs/tags/v0.3.0\\n'
  fi
}
'''
    with tempfile.TemporaryDirectory(prefix="gbb-release-tag-guard.") as directory:
        log = Path(directory) / "git.log"

        def run(ref_name: str, tag_exists: bool) -> subprocess.CompletedProcess[str]:
            log.write_text("", encoding="utf-8")
            env = {**os.environ, "GITHUB_REF_NAME": ref_name, "GITHUB_REPOSITORY": "szTheory/gabbaboy",
                   "TAG_EXISTS": "true" if tag_exists else "false", "TAG_GIT_LOG": str(log)}
            return subprocess.run(["bash", "-c", harness + shell], capture_output=True, text=True,
                                  check=False, env=env, timeout=10)

        absent = run("rehearsal/v0.3.0", False)
        if absent.returncode != 0 or len(log.read_text(encoding="utf-8").splitlines()) != 1:
            raise SystemExit("self-test release tag guard failed to allow an untagged release rehearsal")
        present = run("rehearsal/v0.3.0", True)
        if (present.returncode == 0 or "Tag v0.3.0 already exists; a rehearsal after the tag cannot bind a release." not in present.stderr
                or len(log.read_text(encoding="utf-8").splitlines()) != 1):
            raise SystemExit("self-test release tag guard did not refuse an existing release tag")
        other = run("rehearsal/phase-15.1-demo", True)
        if other.returncode != 0 or log.read_text(encoding="utf-8").strip():
            raise SystemExit("self-test release tag guard did not skip a non-release rehearsal branch")
    print("PASS: rehearsal tag guard allows an untagged release rehearsal and refuses an existing tag; non-release branch skips")
    return 1


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
        rejected += rehearsal_tag_guard_controls(fixture)
        baselines = {item: (fixture / ".github/workflows" / item).read_text(encoding="utf-8") for item in WORKFLOWS}
        baselines["script"] = (fixture / PRODUCER_SCRIPT).read_text(encoding="utf-8")
        baselines["config"] = (fixture / WINDOW_CONFIG).read_text(encoding="utf-8")
        baselines["lifecycle"] = (fixture / LIFECYCLE_SCRIPT).read_text(encoding="utf-8")
        baselines["perfgate"] = (fixture / PERF_GATE_SCRIPT).read_text(encoding="utf-8")

        def target(workflow: str) -> Path:
            if workflow == "perfgate":
                return fixture / PERF_GATE_SCRIPT
            if workflow == "config":
                return fixture / WINDOW_CONFIG
            if workflow == "lifecycle":
                return fixture / LIFECYCLE_SCRIPT
            return fixture / (PRODUCER_SCRIPT if workflow == "script" else f".github/workflows/{workflow}")

        for label, workflow, edits, expected in (*_mutations(), *_window_mutations(), *_version_pr_gate_mutations()):
            workflow, edits = _route_lifecycle(workflow, edits, baselines["release.yml"], baselines["lifecycle"])
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
        # Timeout ledger (D-20): data mutations through the CLI, each restoring the baseline afterwards.
        ledger_baseline = (fixture / LEDGER_PATH).read_text(encoding="utf-8")
        cmake_baseline = (fixture / "CMakeLists.txt").read_text(encoding="utf-8")
        for label, mutate, extra, expected in _ledger_mutations():
            mutate(fixture)
            result = _run_cli(fixture, work, *extra)
            diagnostic = result.stderr.strip()
            if result.returncode != 1 or f"REJECT {expected}:" not in diagnostic or "PASS:" in result.stdout:
                raise SystemExit(f"self-test negative {label!r} failed: want REJECT {expected}, exit={result.returncode}, "
                                 f"stdout={result.stdout!r}, stderr={diagnostic!r}")
            rejected += 1
            print(f"rejected: {label}: {diagnostic}")
            (fixture / LEDGER_PATH).write_text(ledger_baseline, encoding="utf-8")
            (fixture / "CMakeLists.txt").write_text(cmake_baseline, encoding="utf-8")
            for item in WORKFLOWS:
                (fixture / ".github/workflows" / item).write_text(baselines[item], encoding="utf-8")
        rejected += _ledger_boundary_controls()
        rejected += _ledger_git_object_controls()
        rejected += _ledger_disclosure_scratch_controls()
        rejected += _ledger_release_object_scratch_controls(root, work)
        rejected += verify_cited_stub_controls(fixture, work)
        # WR-C01: the workflow set is closed. A new file (here a pull_request_target job with contents: write) is refused
        # before anything reads it, and so is a judged file that disappears.
        intruder = fixture / ".github/workflows/evil.yml"
        intruder.write_text("name: evil\non:\n  pull_request_target:\npermissions:\n  contents: write\njobs:\n  evil:\n"
                            "    runs-on: ubuntu-22.04\n    steps:\n      - run: echo evil\n", encoding="utf-8")
        for label, mutate, restore in (
            ("WR-C01 an unlisted workflow file", lambda: None, intruder.unlink),
            ("WR-C01 a judged workflow file renamed to .yaml",
             lambda: (fixture / ".github/workflows/libbet-repro.yml").rename(fixture / ".github/workflows/libbet-repro.yaml"),
             lambda: (fixture / ".github/workflows/libbet-repro.yaml").rename(fixture / ".github/workflows/libbet-repro.yml")),
        ):
            mutate()
            result = _run_cli(fixture, work)
            restore()
            if result.returncode != 1 or "REJECT workflow-unlisted:" not in result.stderr or "PASS:" in result.stdout:
                raise SystemExit(f"self-test negative {label!r} failed: exit={result.returncode} stderr={result.stderr.strip()!r}")
            rejected += 1
            print(f"rejected: {label}: {result.stderr.strip()}")
        # Equivalent shell formatting of a required call stays valid: continuation, quoting, extra spaces,
        # interleaved comments and blank lines do not change what runs.
        path = fixture / ".github/workflows/release-rehearsal.yml"
        accepted = 0
        for variant in (
            "python3  -I \\\n{I}  trusted-judge/.github/scripts/verify-workflow-policy.py \\\n{I}  --check --root subject --release-head",
            'python3 -I "trusted-judge/.github/scripts/verify-workflow-policy.py" --check --root \'subject\' --release-head',
            "# the judge\n{I}\n{I}python3 -I trusted-judge/.github/scripts/verify-workflow-policy.py --check --root subject --release-head  # trailing",
        ):
            variant = variant.replace("--release-head", "--release-head --git-root trusted-judge")
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
    rejected += report_red_replay_controls(root)
    print(f"PASS: workflow policy self-test negative_controls={rejected} positive_controls={1 + accepted}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true", help="judge the workflow files under --root")
    modes.add_argument("--self-test", action="store_true", help="run positive and intended-defect controls through the CLI")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2],
                        help="tree whose .github/workflows files are judged as data")
    parser.add_argument("--git-root", type=Path, default=None,
                        help="git object database for citation checks (default: --root)")
    parser.add_argument("--main-ref", default="HEAD",
                        help="revision under test for tree-equal anchor ancestry (default: HEAD in --git-root)")
    parser.add_argument("--disclosure-base", default=None,
                        help="optional commit whose workflow job bodies are compared for required disclosures")
    parser.add_argument("--release-head", action="store_true",
                        help="judge as the release head: provisional rows and unreadable tree-equal citation objects are rejected")
    parser.add_argument("--verify-cited", action="store_true",
                        help="online and advisory (never in CTest): confirm each ledger citation through gh")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.self_test:
            self_test(root)
            return 0
        if args.verify_cited:
            return verify_cited(root)
        facts = check_all(root, args.release_head, args.git_root.resolve() if args.git_root else root,
                          args.main_ref, args.disclosure_base)
        print(f"PASS: workflow privilege and trust wiring residual_write_jobs={facts['residual']}")
        return 0
    except Reject as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
