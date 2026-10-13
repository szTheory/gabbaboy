#!/usr/bin/env python3
"""Check that plan SUMMARY `coverage:` blocks let /gsd-verify-work auto-pass (DECISIONS D-069).

The GSD classifier (`uat.classify-coverage`) only auto-passes an entry written in its block-style
schema. Phases 9 and 10 used a `deliverable:` key and flow-style `{kind: ctest, ...}` items, which
the classifier rejects, so every automated item fell back to manual mapping at verify-work. This
script repeats the classifier's validation rules (copied, not imported: the GSD runtime is not
present in CI) and adds the D-069 rule: an entry with `human_judgment: false` must cite at least
one verification and every one must be `status: pass`, so it never reaches the owner as UAT.

Usage:
  verify-summary-coverage.py [--phases-dir DIR] [--since N]   check SUMMARYs of phases >= N
  verify-summary-coverage.py --file PATH                       check one SUMMARY
  verify-summary-coverage.py --self-test                       check the rules against mutants
"""

import argparse
import os
import re
import sys
import tempfile

VALID_KINDS = ("unit", "integration", "e2e", "automated_ui", "manual_procedural", "other")
VALID_STATUSES = ("pass", "fail", "unknown")


class CoverageError(Exception):
    pass


def frontmatter_lines(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CoverageError("missing-frontmatter")
    for end in range(1, len(lines)):
        if lines[end].strip() == "---":
            return lines[1:end]
    raise CoverageError("unterminated-frontmatter")


def scalar(raw):
    value = raw.strip()
    if value.startswith(("'", '"')):
        quote = value[0]
        close = value.find(quote, 1)
        if close < 0:
            raise CoverageError("unterminated-string")
        return value[1:close]
    if re.search(r"\s#", value):
        # The GSD classifier keeps a trailing comment as part of the value, so `pass  # x` is invalid.
        raise CoverageError("inline-comment-not-supported value=%r" % value)
    if value.startswith(("{", "[")) and value != "[]":
        raise CoverageError("flow-style-not-supported")
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    return value


def significant(line):
    stripped = line.strip()
    return stripped != "" and not stripped.startswith("#")


def indent(line):
    return len(line) - len(line.lstrip(" "))


def parse_sequence(lines, start, item_indent):
    """Parse `- key: value` items at item_indent; return (list, next index)."""
    items = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not significant(line):
            i += 1
            continue
        if indent(line) < item_indent:
            break
        if indent(line) != item_indent or not line.lstrip().startswith("- "):
            raise CoverageError("malformed-sequence line=%r" % line.strip())
        body = line.lstrip()[2:]
        if body.lstrip().startswith(("{", "[")):
            raise CoverageError("flow-style-not-supported line=%r" % line.strip())
        if ":" not in body:
            raise CoverageError("item-not-a-mapping line=%r" % line.strip())
        entry, i = parse_mapping(lines, i, item_indent + 2, first=body)
        items.append(entry)
    return items, i


def parse_mapping(lines, start, key_indent, first):
    entry = {}
    pending = [first]
    i = start + 1
    while True:
        text = pending.pop() if pending else None
        if text is None:
            while i < len(lines) and not significant(lines[i]):
                i += 1
            if i >= len(lines) or indent(lines[i]) < key_indent:
                return entry, i
            if indent(lines[i]) != key_indent or lines[i].lstrip().startswith("- "):
                return entry, i
            text = lines[i].strip()
            i += 1
        key, _, rest = text.partition(":")
        key = key.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise CoverageError("bad-key %r" % key)
        if key in entry:
            raise CoverageError("duplicate-key %s" % key)
        if rest.strip() == "":
            seq, i = parse_sequence(lines, i, key_indent + 2)
            entry[key] = seq
        else:
            entry[key] = scalar(rest)


def coverage_entries(text):
    lines = frontmatter_lines(text)
    for index, line in enumerate(lines):
        if line.startswith("coverage:"):
            rest = line[len("coverage:"):]
            if rest.strip():
                value = scalar(rest)
                if value != []:
                    raise CoverageError("coverage-not-a-list")
                return []
            block = []
            for follow in lines[index + 1:]:
                if significant(follow) and indent(follow) == 0:
                    break
                block.append(follow)
            first = next((b for b in block if significant(b)), None)
            if first is None:
                return []
            entries, consumed = parse_sequence(block, 0, indent(first))
            if any(significant(b) for b in block[consumed:]):
                raise CoverageError("malformed-block")
            return entries
    raise CoverageError("missing-coverage-block")


def entry_errors(entry, seen):
    errors = []
    ident = entry.get("id")
    if not isinstance(ident, str) or not ident.strip():
        errors.append("missing-id")
    elif ident in seen:
        errors.append("duplicate-id %s" % ident)
    else:
        seen.add(ident)
    label = ident if isinstance(ident, str) and ident else "?"
    if not isinstance(entry.get("description"), str) or not entry["description"].strip():
        errors.append("missing-description %s" % label)
    judgment = entry.get("human_judgment")
    if not isinstance(judgment, bool):
        errors.append("missing-human-judgment %s" % label)
    rationale = entry.get("rationale")
    if judgment is True and (not isinstance(rationale, str) or not rationale.strip()):
        errors.append("missing-rationale %s" % label)
    verification = entry.get("verification", [])
    if not isinstance(verification, list):
        errors.append("verification-not-list %s" % label)
        verification = []
    for item in verification:
        if item.get("kind") not in VALID_KINDS:
            errors.append("invalid-kind %s %r" % (label, item.get("kind")))
        if item.get("status") not in VALID_STATUSES:
            errors.append("invalid-status %s %r" % (label, item.get("status")))
        if not isinstance(item.get("ref"), str) or not item["ref"].strip():
            errors.append("missing-ref %s" % label)
    if judgment is False:
        if not verification:
            errors.append("not-auto-passable %s: no verification" % label)
        elif any(item.get("status") != "pass" for item in verification):
            errors.append("not-auto-passable %s: a verification is not pass" % label)
    return errors


def check_text(text):
    try:
        entries = coverage_entries(text)
    except CoverageError as exc:
        return 0, [str(exc)]
    seen = set()
    errors = []
    for entry in entries:
        errors.extend(entry_errors(entry, seen))
    return len(entries), errors


def phase_number(dirname):
    match = re.match(r"^[A-Z]+-(\d+(?:\.\d+)?)-", dirname)
    return float(match.group(1)) if match else None


def check_tree(phases_dir, since):
    files = 0
    entries = 0
    failures = []
    for dirname in sorted(os.listdir(phases_dir)):
        number = phase_number(dirname)
        if number is None or number < since:
            continue
        directory = os.path.join(phases_dir, dirname)
        for name in sorted(os.listdir(directory)):
            if not name.endswith("-SUMMARY.md"):
                continue
            files += 1
            with open(os.path.join(directory, name), encoding="utf-8") as handle:
                count, errors = check_text(handle.read())
            entries += count
            failures.extend("%s: %s" % (name, error) for error in errors)
    return files, entries, failures


GOOD = """---
plan: 99-01
coverage:
  - id: D1
    description: "Tracer passes"
    requirement: CGB-01
    verification:
      - kind: integration
        ref: "ctest -R '^tracer$'"
        status: pass
    human_judgment: false
  - id: D2
    description: "Colour looks right on a panel"
    verification: []
    human_judgment: true
    rationale: "perceptual judgement on real hardware"
status: complete
---
# body
"""

MUTANTS = (
    ("flow-style-not-supported", GOOD.replace(
        "      - kind: integration\n        ref: \"ctest -R '^tracer$'\"\n        status: pass\n",
        "      - {kind: integration, ref: tracer, status: pass}\n")),
    ("invalid-kind D1 'ctest'", GOOD.replace("kind: integration", "kind: ctest")),
    ("missing-id", GOOD.replace("  - id: D1\n    description", "  - deliverable: x\n    description")),
    ("missing-description D1", GOOD.replace('    description: "Tracer passes"\n', "")),
    ("missing-human-judgment D1", GOOD.replace("    human_judgment: false\n", "")),
    ("missing-rationale D2", GOOD.replace('    rationale: "perceptual judgement on real hardware"\n', "")),
    ("not-auto-passable D1: a verification is not pass", GOOD.replace("status: pass", "status: unknown")),
    ("not-auto-passable D1: no verification", GOOD.replace(
        "    verification:\n      - kind: integration\n        ref: \"ctest -R '^tracer$'\"\n"
        "        status: pass\n    human_judgment: false",
        "    verification: []\n    human_judgment: false")),
    ("duplicate-id D1", GOOD.replace("id: D2", "id: D1")),
    ("missing-ref D1", GOOD.replace("        ref: \"ctest -R '^tracer$'\"\n", "")),
    ("missing-coverage-block", GOOD.replace("coverage:", "coverage_old:")),
    ("inline-comment-not-supported", GOOD.replace("status: pass", "status: pass  # latest run")),
)


def self_test():
    count, errors = check_text(GOOD)
    if errors or count != 2:
        print("summary-coverage self-test FAIL good entries=%d errors=%s" % (count, errors))
        return 1
    for expected, text in MUTANTS:
        if text == GOOD:
            print("summary-coverage self-test FAIL mutant unchanged: %s" % expected)
            return 1
        _, errors = check_text(text)
        if not any(error.startswith(expected) for error in errors):
            print("summary-coverage self-test FAIL mutant %r not rejected: %s" % (expected, errors))
            return 1
    with tempfile.TemporaryDirectory() as root:
        old = os.path.join(root, "GB-05-old")
        new = os.path.join(root, "GB-06.1-new")
        os.mkdir(old)
        os.mkdir(new)
        with open(os.path.join(old, "05-01-SUMMARY.md"), "w", encoding="utf-8") as handle:
            handle.write(MUTANTS[1][1])
        with open(os.path.join(new, "06.1-01-SUMMARY.md"), "w", encoding="utf-8") as handle:
            handle.write(GOOD)
        files, _, failures = check_tree(root, 6)
        if files != 1 or failures:
            print("summary-coverage self-test FAIL since filter files=%d failures=%s" % (files, failures))
            return 1
        files, _, failures = check_tree(root, 0)
        if files != 2 or not failures:
            print("summary-coverage self-test FAIL old phase not checked when in range")
            return 1
    print("summary-coverage self-test pass mutants=%d" % len(MUTANTS))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--phases-dir", default=".planning/phases")
    parser.add_argument("--since", type=float, default=11)
    parser.add_argument("--file")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            count, errors = check_text(handle.read())
        files, failures = 1, ["%s: %s" % (os.path.basename(args.file), e) for e in errors]
    else:
        files, count, failures = check_tree(args.phases_dir, args.since)
    for failure in failures:
        print("summary-coverage-invalid: %s" % failure)
    if failures:
        print("summary-coverage FAIL files=%d problems=%d" % (files, len(failures)))
        return 1
    print("summary-coverage pass files=%d entries=%d" % (files, count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
