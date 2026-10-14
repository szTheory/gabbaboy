#!/usr/bin/env python3
"""Reject CPU speed reads inside PPU, APU, and RTC function bodies."""
from __future__ import annotations

import pathlib
import re
import sys


def mask_noncode(source: str) -> str:
    out = list(source)
    i = 0
    mode = "code"
    while i < len(source):
        ch = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if mode == "code":
            if ch == "/" and nxt == "*":
                out[i] = out[i + 1] = " "
                i += 2
                mode = "block"
                continue
            if ch == "/" and nxt == "/":
                out[i] = out[i + 1] = " "
                i += 2
                mode = "line"
                continue
            if ch == '"':
                out[i] = " "
                mode = "string"
            elif ch == "'":
                out[i] = " "
                mode = "char"
        elif mode == "block":
            if ch == "*" and nxt == "/":
                out[i] = out[i + 1] = " "
                i += 2
                mode = "code"
                continue
            if ch != "\n":
                out[i] = " "
        elif mode == "line":
            if ch == "\n":
                mode = "code"
            else:
                out[i] = " "
        else:
            if ch == "\\" and i + 1 < len(source):
                out[i] = " "
                if source[i + 1] != "\n":
                    out[i + 1] = " "
                i += 2
                continue
            if (mode == "string" and ch == '"') or (mode == "char" and ch == "'"):
                mode = "code"
            if ch != "\n":
                out[i] = " "
        i += 1
    return "".join(out)


def function_bodies(source: str):
    code = mask_noncode(source)
    depth = 0
    start = 0
    opening = re.compile(r"\b((?:ppu|apu|rtc)_[A-Za-z0-9_]*)\s*\([^;{}]*\)\s*$", re.S)
    for i, ch in enumerate(code):
        if ch == "{" and depth == 0:
            boundary = max(code.rfind(";", start, i), code.rfind("}", start, i)) + 1
            match = opening.search(code[boundary:i])
            if match:
                name = match.group(1)
                body_start = i + 1
                nested = 1
                j = body_start
                while j < len(code) and nested:
                    if code[j] == "{":
                        nested += 1
                    elif code[j] == "}":
                        nested -= 1
                    j += 1
                yield name, code[body_start:j - 1]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                start = i + 1


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: verify-speed-domains.py <core-source>", file=sys.stderr)
        return 2
    path = pathlib.Path(argv[1])
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"speed-domain-input-error {exc}", file=sys.stderr)
        return 2
    bodies = list(function_bodies(source))
    if not bodies:
        print("speed-domain-input-error functions=0", file=sys.stderr)
        return 2
    for name, body in bodies:
        if re.search(r"\bdouble_speed\b", body):
            print(f"speed-domain-violation {name}")
            return 1
    print(f"speed-domains pass functions={len(bodies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
