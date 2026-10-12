#!/usr/bin/env python3
"""Model-gate scanner for the GabbaBoy core (CGB-02, decision D-08).

Standard library only; run as `python3 -I`. Every model difference between DMG and CGB must be
declared in a source comment and in docs/model-gates.md, and this scanner proves the two agree.
It only reads its inputs and prints deterministic output, so running it twice gives one answer.

Tag grammar (a C comment):
    MODEL: CLASS GATE-NN [GUARD=token] [basis=ref] [research:N] [expected-failure:reason] [-- prose]
CLASS is DMG_ONLY, CGB_ONLY, BOTH or UNKNOWN. `ref` and `reason` are a bare word or a "quoted string".
GATE-00 is the shared id for model-neutral function tags (OQ4): class BOTH with a basis= only.

Rules:
  R1 every top-level function definition has a MODEL tag in the comment block directly above it
  R2 code tags and the doc table are a bijection by GATE id with identical class, GUARD, resolution
  R3 UNKNOWN needs research:N or expected-failure:reason; under --release research: also fails
  R4 DMG_ONLY / CGB_ONLY need their GUARD token in code within the next 12 code lines
  R5 hazard tokens under BOTH need basis=
"""
from __future__ import annotations

import argparse
import bisect
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_PATH = "src/core/gabbaboy.c"
DOC_PATH = "docs/model-gates.md"
BEGIN_MARK = "<!-- model-gates-begin -->"
END_MARK = "<!-- model-gates-end -->"
CLASSES = ("DMG_ONLY", "CGB_ONLY", "BOTH", "UNKNOWN")
GUARD_WINDOW = 12
MIN_REAL_FUNCTIONS = 126  # the core at the time the scanner was written (T-10-01)

# R5: a hazard is a register or state that differs on real hardware by model. The pattern is
# deliberately broad; a false hit is cured by writing the basis= that justifies BOTH.
HAZARD = re.compile(r"0[xX][Ff][Ff][4-7][0-9A-Fa-f]\b|\bstopped\b|halt_bug|dma_|apu_power|ppu_mode"
                    r"|\breturn\s+0[xX][Ff][Ff][uU]?\b")

ID_RE = r"GATE-\d\d"
HEAD_RE = re.compile(r"MODEL:\s+(DMG_ONLY|CGB_ONLY|BOTH|UNKNOWN)\s+(" + ID_RE + r")(?=\s|$)")
ITEM_RES = (
    ("guard", re.compile(r"\s+GUARD=([A-Za-z0-9_]+)(?=\s|$)")),
    ("basis", re.compile(r'\s+basis=("[^"]*"|[^\s"]+)(?=\s|$)')),
    ("research", re.compile(r"\s+research:(\d+)(?=\s|$)")),
    ("expected_failure", re.compile(r'\s+expected-failure:("[^"]*"|[^\s"]+)(?=\s|$)')),
)


def fail(token: str, detail: str | None = None) -> None:
    raise ValueError(token if detail is None else f"{token}: {detail}")


# ---------------------------------------------------------------------------------------------
# C lexing: comments, strings, character literals and preprocessor lines become spaces so brace
# counting sees only code. Newlines are kept, so indexes and line numbers stay aligned.
# ---------------------------------------------------------------------------------------------

def lex(text: str):
    n = len(text)
    out = list(text)
    comments: list[tuple[int, int, str]] = []
    i = 0
    line = 1
    bol = True
    preprocessor = False

    def blank(a: int, b: int) -> None:
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = text[i]
        if c == "\n":
            if preprocessor and not text[:i].rstrip("\r").endswith("\\"):
                preprocessor = False
            line += 1
            bol = True
            i += 1
            continue
        if c in " \t\r\f\v":
            i += 1
            continue
        if c == "#" and bol:
            preprocessor = True
        bol = False
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                fail("gate-unbalanced", f"unterminated comment at line {line}")
            body = text[i + 2:j]
            end_line = line + body.count("\n")
            comments.append((line, end_line, body))
            blank(i, j + 2)
            line = end_line
            i = j + 2
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            comments.append((line, line, text[i + 2:j]))
            blank(i, j)
            i = j
            continue
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                if text[j] == "\\":
                    j += 1
                    if j < n and text[j] == "\n":
                        line += 1
                elif text[j] == "\n":
                    fail("gate-unbalanced", f"unterminated literal at line {line}")
                j += 1
            if j >= n:
                fail("gate-unbalanced", f"unterminated literal at line {line}")
            blank(i, j + 1)
            i = j + 1
            continue
        if preprocessor:
            out[i] = " "
        i += 1
    return "".join(out), comments


def find_functions(code: str):
    """Top-level definitions: a depth-0 `{` whose previous code character is `)`."""
    starts = [0]
    for k, ch in enumerate(code):
        if ch == "\n":
            starts.append(k + 1)

    def line_of(index: int) -> int:
        return bisect.bisect_right(starts, index)

    functions = []
    depth = 0
    decl = 0
    current = None
    for i, c in enumerate(code):
        if c == "{":
            if depth == 0:
                current = None
                k = i - 1
                while k >= 0 and code[k].isspace():
                    k -= 1
                if k >= 0 and code[k] == ")":
                    nest = 0
                    m = k
                    while m >= 0:
                        if code[m] == ")":
                            nest += 1
                        elif code[m] == "(":
                            nest -= 1
                            if nest == 0:
                                break
                        m -= 1
                    if m < 0:
                        fail("gate-unbalanced", f"unbalanced parenthesis before line {line_of(i)}")
                    p = m - 1
                    while p >= 0 and code[p].isspace():
                        p -= 1
                    end = p
                    while p >= 0 and (code[p].isalnum() or code[p] == "_"):
                        p -= 1
                    name = code[p + 1:end + 1]
                    if not name:
                        fail("gate-unbalanced", f"unnamed definition at line {line_of(i)}")
                    first = decl
                    while first < i and code[first].isspace():
                        first += 1
                    current = {"name": name, "start_line": line_of(first)}
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                fail("gate-unbalanced", f"unmatched closing brace at line {line_of(i)}")
            if depth == 0:
                if current is not None:
                    current["end_line"] = line_of(i)
                    functions.append(current)
                    current = None
                decl = i + 1
        elif c == ";" and depth == 0:
            decl = i + 1
    if depth != 0:
        fail("gate-unbalanced", "unbalanced braces at end of source")
    return functions


# ---------------------------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------------------------

def comment_text(body: str) -> str:
    lines = [re.sub(r"^\s*\*+\s?", "", raw) for raw in body.split("\n")]
    return " ".join(" ".join(lines).split())


def parse_tag(text: str, line: int) -> dict:
    where = f"line {line}"
    start = text.find("MODEL:")
    if text.count("MODEL:") != 1:
        fail("gate-malformed-tag", f"{where}: exactly one MODEL: per comment")
    rest = text[start:]
    head = HEAD_RE.match(rest)
    if head is None:
        fail("gate-malformed-tag", f"{where}: expected MODEL: CLASS GATE-NN")
    tag = {"cls": head.group(1), "gate": head.group(2), "guard": None, "basis": None,
           "research": None, "expected_failure": None, "line": line}
    pos = head.end()
    while True:
        for key, pattern in ITEM_RES:
            m = pattern.match(rest, pos)
            if m is not None:
                if tag[key] is not None:
                    fail("gate-malformed-tag", f"{where}: duplicate {key}")
                tag[key] = m.group(1)
                pos = m.end()
                break
        else:
            break
    tail = rest[pos:].strip()
    if tail and not tail.startswith("--"):
        fail("gate-malformed-tag", f"{where}: unparsed text '{tail[:30]}'")
    if tag["gate"] == "GATE-00" and (tag["cls"] != "BOTH" or tag["basis"] is None):
        fail("gate-malformed-tag", f"{where}: GATE-00 is BOTH with a basis= only")
    return tag


def resolution_text(tag: dict) -> str:
    parts = []
    if tag["basis"] is not None:
        parts.append(f"basis={tag['basis']}")
    if tag["research"] is not None:
        parts.append(f"research:{tag['research']}")
    if tag["expected_failure"] is not None:
        parts.append(f"expected-failure:{tag['expected_failure']}")
    return " ".join(parts) if parts else "-"


def collect_tags(comments, functions):
    """Return (tags, function_tag_by_name_line). Function tags come from the comment chain
    ending on the line directly above a definition; every other MODEL comment is a branch tag."""
    by_end = {}
    for index, (start, end, _body) in enumerate(comments):
        by_end.setdefault(end, []).append(index)
    chain_of = {}
    for func in functions:
        want = func["start_line"] - 1
        chain = []
        while want in by_end:
            index = by_end[want][-1]
            chain.append(index)
            want = comments[index][0] - 1
        chain_of[func["start_line"]] = chain
    owner = {}
    for func in functions:
        for index in chain_of[func["start_line"]]:
            owner[index] = func
    tags = []
    tagged_funcs = set()
    for index, (start, end, body) in enumerate(comments):
        text = comment_text(body)
        if "MODEL:" not in text:
            continue
        tag = parse_tag(text, start)
        tag["end_line"] = end
        func = owner.get(index)
        if func is None:
            tag["kind"] = "branch"
        else:
            if func["start_line"] in tagged_funcs:
                fail("gate-malformed-tag", f"line {start}: {func['name']} has two MODEL tags")
            tagged_funcs.add(func["start_line"])
            tag["kind"] = "function"
            tag["func"] = func
        tags.append(tag)
    return tags, tagged_funcs


# ---------------------------------------------------------------------------------------------
# Doc table
# ---------------------------------------------------------------------------------------------

def parse_doc(doc: str) -> list[dict]:
    if doc.count(BEGIN_MARK) != 1 or doc.count(END_MARK) != 1:
        fail("gate-doc-mismatch", "doc needs exactly one model-gates marker pair")
    begin = doc.index(BEGIN_MARK)
    end = doc.index(END_MARK)
    if end < begin:
        fail("gate-doc-mismatch", "model-gates markers are out of order")
    base_line = doc[:begin].count("\n") + 1
    rows = []
    for offset, raw in enumerate(doc[begin + len(BEGIN_MARK):end].split("\n")):
        text = raw.strip()
        if not text.startswith("|"):
            continue
        cells = [cell.strip() for cell in text.strip("|").split("|")]
        if not re.fullmatch(ID_RE, cells[0]):
            continue  # header and separator rows
        line = base_line + offset
        if len(cells) < 6:
            fail("gate-doc-mismatch", f"doc line {line}: row needs six cells")
        if cells[1] not in CLASSES:
            fail("gate-doc-mismatch", f"doc line {line}: unknown class {cells[1]}")
        rows.append({"gate": cells[0], "cls": cells[1], "guard": cells[2],
                     "resolution": " ".join(cells[3].split()), "line": line})
    if not rows:
        fail("gate-doc-mismatch", "doc table holds no gate rows")
    seen = set()
    for row in rows:
        if row["gate"] in seen:
            fail("gate-doc-mismatch", f"doc line {row['line']}: duplicate {row['gate']}")
        seen.add(row["gate"])
    for before, after in zip(rows, rows[1:]):
        if after["gate"] < before["gate"]:
            fail("gate-doc-order", f"doc line {after['line']}: {after['gate']} follows {before['gate']}")
    if sum(1 for row in rows if row["gate"] == "GATE-00") > 1:
        fail("gate-doc-mismatch", "doc carries more than one GATE-00 row")
    return rows


# ---------------------------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------------------------

def verify(source: str, doc: str, release: bool = False) -> dict:
    rows = parse_doc(doc)
    code, comments = lex(source)
    code_lines = code.split("\n")
    functions = find_functions(code)
    tags, tagged = collect_tags(comments, functions)
    findings: list[tuple[int, int, str, str]] = []

    def add(line: int, token: str, detail: str) -> None:
        findings.append((line, len(findings), token, detail))

    def window(after_line: int) -> list[str]:
        picked = []
        for text in code_lines[after_line:]:
            if text.strip():
                picked.append(text)
                if len(picked) == GUARD_WINDOW:
                    break
        return picked

    for func in functions:
        if func["start_line"] not in tagged:
            add(func["start_line"], "gate-untagged-function", f"{func['name']} (line {func['start_line']})")

    code_gates: dict[str, list[dict]] = {}
    for tag in tags:
        code_gates.setdefault(tag["gate"], []).append(tag)
        gate = f"{tag['gate']} line {tag['line']}"
        if tag["cls"] == "UNKNOWN":
            if tag["research"] is None and tag["expected_failure"] is None:
                add(tag["line"], "gate-unresolved-unknown", f"{gate} has no research: or expected-failure:")
            elif release and tag["research"] is not None:
                add(tag["line"], "gate-unresolved-unknown", f"{gate} research:{tag['research']} under --release")
        if tag["cls"] in ("DMG_ONLY", "CGB_ONLY"):
            guard = tag["guard"]
            if guard is None or not any(guard in text for text in window(tag["end_line"])):
                add(tag["line"], "gate-guard-missing",
                    f"{gate} {tag['cls']} guard {guard or '(none)'} not within {GUARD_WINDOW} code lines")
        if tag["cls"] == "BOTH" and tag["basis"] is None:
            if tag["kind"] == "function":
                span = code_lines[tag["func"]["start_line"] - 1:tag["func"]["end_line"]]
            else:
                span = window(tag["end_line"])
            hit = next((HAZARD.search(text) for text in span if HAZARD.search(text)), None)
            if hit is not None:
                add(tag["line"], "gate-hazard-under-both", f"{gate} BOTH without basis= over '{hit.group(0)}'")

    doc_by_gate = {row["gate"]: row for row in rows}
    for gate, group in code_gates.items():
        if gate == "GATE-00":
            continue
        if len(group) > 1:
            add(group[1]["line"], "gate-doc-mismatch", f"{gate} appears {len(group)} times in code")
            continue
        tag = group[0]
        row = doc_by_gate.get(gate)
        if row is None:
            add(tag["line"], "gate-doc-mismatch", f"{gate} has no doc row")
            continue
        want = (tag["cls"], tag["guard"] or "-", resolution_text(tag))
        have = (row["cls"], row["guard"], row["resolution"])
        if want != have:
            add(tag["line"], "gate-doc-mismatch", f"{gate} code {want} differs from doc {have}")
    row00 = doc_by_gate.get("GATE-00")
    if row00 is not None and (row00["cls"] != "BOTH" or not row00["resolution"].startswith("basis=")):
        add(10**9 + row00["line"], "gate-doc-mismatch", "doc GATE-00 row must be BOTH with a basis=")
    for row in rows:
        if row["gate"] != "GATE-00" and row["gate"] not in code_gates:
            add(10**9 + row["line"], "gate-doc-mismatch", f"doc {row['gate']} has no code tag")

    if findings:
        _line, _order, token, detail = min(findings)
        fail(token, detail)
    unknown = len({tag["gate"] for tag in tags if tag["cls"] == "UNKNOWN"})
    return {"functions": len(functions), "gates": len(rows), "unknown": unknown}


def summary_line(result: dict) -> str:
    return f"model-gates pass functions={result['functions']} gates={result['gates']} unknown={result['unknown']}"


# ---------------------------------------------------------------------------------------------
# Self-test: every control must be rejected with its own token
# ---------------------------------------------------------------------------------------------

class Counter:
    mutants = 0


def expect(token: str, action, label: str) -> None:
    Counter.mutants += 1
    try:
        action()
    except ValueError as error:
        if not str(error).startswith(token):
            fail("self-test", f"{label}: expected {token}, got {error}")
        return
    fail("self-test", f"{label}: mutation was accepted")


def corpus() -> tuple[str, str]:
    source = (
        '/* MODEL: BOTH GATE-00 basis="model-neutral" */\n'
        "static int neutral(int x) { return x + 1; }\n"
        "\n"
        "/* MODEL: DMG_ONLY GATE-01 GUARD=model_is_dmg */\n"
        "static int dmg_only(int model) {\n"
        "    if (model_is_dmg(model)) return 1;\n"
        "    return 0;\n"
        "}\n"
        "\n"
        '/* MODEL: BOTH GATE-00 basis="model-neutral" */\n'
        "static int multi(int a,\n"
        "                 int b) {\n"
        "    /* MODEL: UNKNOWN GATE-02 research:12 */\n"
        "    a += b;\n"
        "    /* MODEL: BOTH GATE-03 basis=pandocs-ff4d */\n"
        "    if (a == 0xFF4Du) return 0xFFu;\n"
        "    return a;\n"
        "}\n"
    )
    doc = (
        "# Model gates\n\n"
        f"{BEGIN_MARK}\n"
        "| Gate | Class | Guard | Resolution | Site | Note |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        '| GATE-00 | BOTH | - | basis="model-neutral" | all | neutral functions |\n'
        "| GATE-01 | DMG_ONLY | model_is_dmg | - | dmg_only | synthetic |\n"
        "| GATE-02 | UNKNOWN | - | research:12 | multi | synthetic |\n"
        "| GATE-03 | BOTH | - | basis=pandocs-ff4d | multi | synthetic |\n"
        f"{END_MARK}\n"
    )
    return source, doc


def independent_function_count(text: str) -> int:
    """A second counter that shares no code with lex()/find_functions(): regex stripping, then a
    per-character depth walk counting each 0->1 transition whose previous token is `)`."""
    text = re.sub(r"(?m)^[ \t]*#(?:\\\n|[^\n])*", " ", text)
    text = re.sub(r"//[^\n]*|/\*.*?\*/|\"(?:\\.|[^\"\\\n])*\"|'(?:\\.|[^'\\\n])*'", " ", text, flags=re.S)
    depth = 0
    previous = ""
    count = 0
    for ch in text:
        if ch == "{":
            if depth == 0 and previous == ")":
                count += 1
            depth += 1
        elif ch == "}":
            depth -= 1
        if not ch.isspace():
            previous = ch
    return count


def tag_every_function(text: str) -> str:
    """Neutralise any existing tags, then put a GATE-00 BOTH tag above every definition."""
    text = text.replace("MODEL:", "MODEL-")
    code, _comments = lex(text)
    lines = text.split("\n")
    for func in sorted(find_functions(code), key=lambda f: f["start_line"], reverse=True):
        lines.insert(func["start_line"] - 1, "/* MODEL: BOTH GATE-00 basis=self-test */")
    return "\n".join(lines)


def self_test() -> None:
    source, doc = corpus()
    base = verify(source, doc)
    if base != {"functions": 3, "gates": 4, "unknown": 1}:
        fail("self-test", f"synthetic corpus did not pass cleanly: {base}")
    # The 12-line guard window is inclusive: a guard on the 12th code line passes.
    filler = "    pad();\n"
    inside = source.replace("static int dmg_only(int model) {\n", "static int dmg_only(int model) {\n" + filler * 10)
    verify(inside, doc)
    outside = source.replace("static int dmg_only(int model) {\n", "static int dmg_only(int model) {\n" + filler * 11)

    def without(text: str, old: str, new: str) -> str:
        if old not in text:
            fail("self-test", f"mutation anchor missing: {old!r}")
        return text.replace(old, new)

    expect("gate-untagged-function",
           lambda: verify(without(source, '/* MODEL: BOTH GATE-00 basis="model-neutral" */\nstatic int neutral', "static int neutral"), doc),
           "deleted tag")
    expect("gate-doc-mismatch",
           lambda: verify(source, without(doc, "| GATE-01 | DMG_ONLY |", "| GATE-01 | CGB_ONLY |")), "doc class differs")
    expect("gate-doc-mismatch",
           lambda: verify(source, without(doc, "| model_is_dmg |", "| other_guard |")), "doc guard differs")
    expect("gate-doc-mismatch",
           lambda: verify(source, without(doc, "| basis=pandocs-ff4d |", "| basis=other |")), "doc resolution differs")
    unknown_none_src = without(source, " research:12", "")
    unknown_none_doc = without(doc, "| research:12 |", "| - |")
    expect("gate-unresolved-unknown", lambda: verify(unknown_none_src, unknown_none_doc), "UNKNOWN without resolution")
    expect("gate-unresolved-unknown", lambda: verify(source, doc, release=True), "UNKNOWN research under --release")
    verify(without(source, " research:12", " expected-failure:pending-hardware-oracle"),
           without(doc, "| research:12 |", "| expected-failure:pending-hardware-oracle |"), release=True)
    expect("gate-guard-missing", lambda: verify(outside, doc), "DMG_ONLY guard 13 lines below")
    expect("gate-guard-missing", lambda: verify(without(source, " GUARD=model_is_dmg", ""),
                                                without(doc, "| model_is_dmg |", "| - |")), "DMG_ONLY without GUARD")
    expect("gate-hazard-under-both",
           lambda: verify(without(source, " basis=pandocs-ff4d", ""), without(doc, "| basis=pandocs-ff4d |", "| - |")),
           "BOTH branch over 0xFFu without basis")
    reordered = without(without(doc, "| GATE-02 | UNKNOWN | - | research:12 | multi | synthetic |\n", ""),
                        "| GATE-03 | BOTH | - | basis=pandocs-ff4d | multi | synthetic |\n",
                        "| GATE-03 | BOTH | - | basis=pandocs-ff4d | multi | synthetic |\n"
                        "| GATE-02 | UNKNOWN | - | research:12 | multi | synthetic |\n")
    expect("gate-doc-order", lambda: verify(source, reordered), "doc rows out of order")
    table_start = doc.index("| Gate |")
    table_end = doc.index(END_MARK)
    expect("gate-doc-mismatch", lambda: verify(source, doc[:table_start] + doc[table_end:]), "empty marker block")
    expect("gate-doc-mismatch", lambda: verify(source, doc.replace(BEGIN_MARK, "")), "missing marker")
    expect("gate-doc-mismatch",
           lambda: verify(without(source, "GATE-02 research:12 */", "GATE-02 research:12 */\n    /* MODEL: UNKNOWN GATE-02 research:12 */"), doc),
           "duplicated GATE id in code")
    expect("gate-malformed-tag",
           lambda: verify(without(source, "BOTH GATE-00 basis=\"model-neutral\" */\nstatic int neutral",
                                  "DMG_ONLY GATE-00 basis=\"model-neutral\" */\nstatic int neutral"), doc),
           "GATE-00 not BOTH")
    expect("gate-malformed-tag",
           lambda: verify(without(source, "BOTH GATE-00 basis=\"model-neutral\" */\nstatic int neutral",
                                  "BOTH GATE-00 */\nstatic int neutral"), doc), "GATE-00 without basis")
    expect("gate-malformed-tag", lambda: verify(without(source, "GATE-03", "GATE-3"), doc), "malformed id")
    expect("gate-unbalanced", lambda: verify(source + "\nstatic int open_brace(void) {\n", doc), "unbalanced brace")

    # Idempotency: two runs over the same input print the same thing.
    if summary_line(verify(source, doc)) != summary_line(verify(source, doc)):
        fail("self-test", "scanner output is not repeatable")

    # R1 scale: the real file's definitions are counted by two independent implementations, and an
    # untagged function appended to the real text is found by the real-file parse.
    real = (ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    scanner_count = len(find_functions(lex(real)[0]))
    independent = independent_function_count(real)
    if scanner_count != independent:
        fail("self-test", f"function count {scanner_count} differs from independent count {independent}")
    if scanner_count < MIN_REAL_FUNCTIONS:
        fail("self-test", f"real file holds {scanner_count} functions, expected at least {MIN_REAL_FUNCTIONS}")
    real_doc = doc.replace(
        doc[doc.index("| GATE-01 |"):doc.index(END_MARK)], "")
    tagged_real = tag_every_function(real)
    result = verify(tagged_real, real_doc)
    if result["functions"] != scanner_count:
        fail("self-test", "tagged real source lost functions")
    expect("gate-untagged-function",
           lambda: verify(tagged_real + "\nstatic int self_test_untagged(void) { return 0; }\n", real_doc),
           "untagged function appended to the real source")
    print(f"model-gates self-test pass mutants={Counter.mutants} functions={scanner_count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=pathlib.Path, default=ROOT / SOURCE_PATH)
    parser.add_argument("--doc", type=pathlib.Path, default=ROOT / DOC_PATH)
    parser.add_argument("--release", action="store_true", help="every research: UNKNOWN fails")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        source = args.source.read_text(encoding="utf-8")
        doc = args.doc.read_text(encoding="utf-8")
        print(summary_line(verify(source, doc, args.release)))
    except (ValueError, OSError) as error:
        print(f"model-gates verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
