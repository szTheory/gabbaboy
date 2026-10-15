#!/usr/bin/env python3
"""Check consumer-facing CGB HDMA claims against the selected bounded model."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
NATIVE_SURFACES = (
    "docs/native-integration.md",
    "docs/support/unreleased.md",
    "docs/preview.md",
    "README.md",
)
PLAYER_SURFACES = (
    "src/player/limitations.h",
    "src/player/main.c",
    "tests/player/claims_agree.cmake",
    ".github/workflows/preview.yml",
)
ALL_SURFACES = NATIVE_SURFACES + PLAYER_SURFACES
SYMBOL_RE = re.compile(r"\b(?:gbb_[A-Za-z0-9_]+|GBB_[A-Z0-9_]+)\b")
STALE_HDMA = re.compile(
    r"(?:no HDMA|HDMA.{0,70}(?:not implemented|not claimed)|"
    r"not implemented.{0,70}HDMA)",
    re.IGNORECASE,
)
CGB_C_QUALIFIER = re.compile(
    r"Optional Mealybug CGB-C cases are\s+`not-run:rights-gate-G1`,\s*"
    r"informational only, and outside the CGB-E\s+denominator\.",
    re.IGNORECASE,
)


class ContractError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def replace_cgb_c_qualifier(text: str, replacement: str) -> str:
    changed, count = CGB_C_QUALIFIER.subn(replacement, text, count=1)
    require(count == 1, "cannot find the retained CGB-C rights-gate qualifier")
    return changed


def source_texts(paths: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = ROOT / relative
        try:
            result[relative] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ContractError(f"missing or unreadable surface: {relative}: {error}") from error
    return result


def validate_subject(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"malformed subject JSON: {error}") from error
    require(isinstance(payload, dict), "malformed subject: expected an object keyed by relative paths")
    actual = set(payload)
    expected = set(ALL_SURFACES)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    require(not missing, f"subject is missing required surfaces: {', '.join(missing)}")
    require(not extra, f"subject has unexpected surfaces: {', '.join(extra)}")
    for relative, text in payload.items():
        require(isinstance(text, str), f"malformed subject text for {relative}: expected a string")
    return payload


def check_symbols(texts: dict[str, str]) -> None:
    try:
        header = (ROOT / "include/gabbaboy/gabbaboy.h").read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError(f"public declaration header unavailable: {error}") from error
    declared = set(SYMBOL_RE.findall(header))
    for relative, text in texts.items():
        if relative not in NATIVE_SURFACES:
            continue
        for symbol in sorted(set(SYMBOL_RE.findall(text)) - declared):
            raise ContractError(f"{relative}: cited public symbol is not declared: {symbol}")


def check_context(native_text: str) -> None:
    profile_path = ROOT / "docs/cgb-profile.md"
    dispositions_path = ROOT / "tests/external/cgb-hdma-dispositions.json"
    try:
        profile = profile_path.read_text(encoding="utf-8")
        dispositions = json.loads(dispositions_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"model or disposition context is unavailable: {error}") from error
    require(
        re.search(r"(?:selected cgb-cpu-e|cgb-cpu-e selected)\s+software model", profile, re.IGNORECASE)
        and "UNKNOWN/POLICY" in profile,
        "cgb-profile.md no longer records the selected software model and physical CGB-E UNKNOWN/POLICY limit",
    )
    require(
        "every four master half-dots" in profile and "64 per block" in profile,
        "cgb-profile.md no longer records the selected 64-half-dot, four-half-dot cadence",
    )
    policy = dispositions.get("policy", {})
    require(
        policy.get("hardware_claim") is False,
        "HDMA disposition policy must keep hardware_claim false",
    )
    rows = [
        row
        for suite in dispositions.get("suites", [])
        for row in suite.get("rows", [])
        if suite.get("suite") == "mealybug-cgb-c"
    ]
    require(rows and all(
        row.get("target_revision") == "CGB-C"
        and row.get("included_in_cgb_e_denominator") is False
        and row.get("disposition") == "not-run:rights-gate-G1"
        for row in rows
    ), "optional CGB-C evidence must remain rights-gated and outside the CGB-E denominator")
    if "CGB-C" in native_text:
        require(
            "rights-gate-G1" in native_text
            and "informational only" in native_text
            and "outside the CGB-E denominator" in native_text,
            "native evidence claim lost the optional CGB-C rights-gate or denominator qualifier",
        )


def check_contract(texts: dict[str, str], paths: tuple[str, ...], context: bool = True) -> None:
    require(set(texts) == set(paths), "internal subject surface selection mismatch")
    combined = "\n".join(texts.values())
    for relative, text in texts.items():
        if STALE_HDMA.search(text):
            raise ContractError(f"{relative}: obsolete HDMA-not-implemented limitation remains")

    for relative in NATIVE_SURFACES:
        if relative in texts:
            require(
                "HBlank DMA" in texts[relative],
                f"{relative}: missing required behavior claim: HBlank DMA",
            )

    native_text = "\n".join(texts[path] for path in NATIVE_SURFACES if path in texts)
    native_requirements = (
        ("GDMA", "GDMA behavior"),
        ("HBlank DMA", "HBlank DMA behavior"),
        ("FF55", "FF55 status/readback"),
        ("cancel", "HDMA cancellation"),
        ("HALT", "HALT behavior"),
        ("instruction-boundary", "instruction-boundary pending-steal approximation"),
        ("64 half-dots", "64-half-dot selected block budget"),
        ("four master half-dots", "four-master-half-dot selected byte cadence"),
        ("invalid", "invalid-transfer handling"),
        ("overflow", "address-overflow handling"),
        ("gbb_run", "unchanged gbb_run consumer path"),
        ("physical CGB-E remains UNKNOWN/POLICY", "physical CGB-E qualification"),
        ("CGB mode-3 timing", "mode-3 timing limitation"),
        ("APU", "APU limitation"),
        ("game compatibility", "game-compatibility limitation"),
        ("rights-gate-G1", "optional CGB-C rights gate"),
        ("informational only", "optional CGB-C informational status"),
        ("outside the CGB-E denominator", "optional CGB-C denominator exclusion"),
    )
    folded_native = native_text.casefold()
    require(
        re.search(r"(?:selected cgb-cpu-e|cgb-cpu-e selected)\s+software model", folded_native),
        "native claims are missing selected model qualification",
    )
    for token, label in native_requirements:
        require(token.casefold() in folded_native, f"native claims are missing {label}")

    for line in combined.splitlines():
        if re.search(r"CGB-C", line, re.IGNORECASE) and re.search(
            r"(?:proves|qualifies|confirms|demonstrates).{0,55}(?:physical )?CGB-E|"
            r"(?:physical )?CGB-E.{0,55}(?:proves|qualifies|confirms|demonstrates)",
            line,
            re.IGNORECASE,
        ):
            raise ContractError("CGB-C evidence must not be presented as physical CGB-E qualification")

    if set(paths) == set(ALL_SURFACES):
        require("CGB mode-3 timing" in combined, "player/package claims must retain the mode-3 timing limit")
        require("APU" in combined, "player/package claims must retain the APU limit")
        require(
            "physical CGB-E" in combined and "game compatibility" in combined.casefold(),
            "player/package claims must retain physical hardware and game-compatibility limits",
        )
        for relative in PLAYER_SURFACES:
            require(relative in texts, f"missing player/package surface: {relative}")
            if relative in ("src/player/limitations.h", "src/player/main.c", ".github/workflows/preview.yml"):
                require(
                    "HDMA" in texts[relative] or "HBlank DMA" in texts[relative],
                    f"{relative}: delivered HDMA behavior is missing from the player/package claim",
                )
        player_scope = (
            "GDMA and HBlank DMA run on the selected bootless CGB-CPU-E software model",
            "CGB mode-3 timing is not claimed",
            "CGB-profile audio uses the DMG APU model",
            "physical CGB-E remains UNKNOWN/POLICY",
            "General game compatibility is not claimed",
        )
        for relative in (
            "src/player/limitations.h",
            "src/player/main.c",
            "README.md",
            ".github/workflows/preview.yml",
        ):
            folded = texts[relative].casefold()
            for phrase in player_scope:
                require(
                    phrase.casefold() in folded,
                    f"{relative}: player/package copy is missing required claim: {phrase}",
                )
        claim_contract = texts["tests/player/claims_agree.cmake"].casefold()
        for phrase in player_scope:
            require(
                phrase.casefold() in claim_contract,
                f"claims_agree.cmake is missing required player-scope assertion: {phrase}",
            )
        workflow = texts[".github/workflows/preview.yml"]
        require(
            not STALE_HDMA.search(workflow),
            "preview package workflow retains an obsolete HDMA limitation",
        )
    check_symbols(texts)
    if context:
        check_context(native_text)


def check_subject_file(path: Path) -> int:
    texts = validate_subject(path)
    check_contract(texts, ALL_SURFACES)
    print(f"CGB HDMA claims: passed all {len(ALL_SURFACES)} subject surfaces")
    return 0


def self_test() -> int:
    native = source_texts(NATIVE_SURFACES)
    check_contract(native, NATIVE_SURFACES)
    try:
        complete = source_texts(ALL_SURFACES)
        check_contract(complete, ALL_SURFACES)
        paths = ALL_SURFACES
        clean = complete
    except ContractError:
        paths = NATIVE_SURFACES
        clean = native

    def mutation_error(mutated: dict[str, str], expected: str) -> None:
        try:
            check_contract(mutated, paths)
        except ContractError as error:
            require(expected in str(error), f"self-test expected diagnostic {expected!r}, got: {error}")
            return
        raise ContractError(f"self-test mutation was accepted: {expected}")

    stale = dict(clean)
    stale["docs/native-integration.md"] += "\nHDMA is not implemented.\n"
    mutation_error(stale, "obsolete HDMA-not-implemented limitation remains")

    unqualified = dict(clean)
    for relative in paths:
        unqualified[relative] = re.sub(
            re.escape("physical CGB-E remains UNKNOWN/POLICY"),
            "physical CGB-E behavior is qualified",
            unqualified[relative],
            flags=re.IGNORECASE,
        )
    mutation_error(unqualified, "physical CGB-E qualification")

    for pattern, diagnostic in (
        (r"CGB mode-3 timing", "mode-3 timing limitation"),
        (r"APU", "APU limitation"),
        (r"game compatibility", "game-compatibility limitation"),
    ):
        removed = dict(clean)
        for relative in paths:
            removed[relative] = re.sub(pattern, "", removed[relative], flags=re.IGNORECASE)
        mutation_error(removed, diagnostic)

    def subject_rejection(subject_text: str, expected: str) -> None:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-cgb-hdma-subject-") as directory:
            path = Path(directory) / "subject.json"
            path.write_text(subject_text, encoding="utf-8")
            try:
                result = subprocess.run(
                    [sys.executable, "-I", str(SCRIPT), "--subject", str(path)],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise ContractError(f"subject self-test timed out for {expected}: {error}") from error
            require(
                result.returncode == 1 and expected in result.stderr,
                f"subject self-test expected {expected!r}, got exit {result.returncode}: {result.stderr}",
            )

    subject = source_texts(ALL_SURFACES)
    missing_surface = dict(subject)
    missing_surface.pop(ALL_SURFACES[-1])
    subject_rejection(
        json.dumps(missing_surface), "subject is missing required surfaces"
    )
    extra_surface = dict(subject)
    extra_surface["README.extra.md"] = "unexpected"
    subject_rejection(
        json.dumps(extra_surface), "subject has unexpected surfaces"
    )
    subject_rejection("{malformed", "malformed subject JSON")

    undeclared = dict(clean)
    undeclared["docs/native-integration.md"] += "\nCall `gbb_get_hdma_status` for the transfer state.\n"
    mutation_error(undeclared, "cited public symbol is not declared: gbb_get_hdma_status")

    conflated = dict(clean)
    guide = conflated["docs/native-integration.md"]
    conflated["docs/native-integration.md"] = replace_cgb_c_qualifier(
        guide, "Optional CGB-C evidence proves physical CGB-E hardware behavior."
    )
    mutation_error(conflated, "CGB-C evidence must not be presented as physical CGB-E qualification")
    print(
        f"CGB HDMA claims: self-test passed ({len(paths)} surfaces, seven claim mutations and three subject rejections)"
    )
    return 0


def prepare_prohibition_subjects(build_dir: Path) -> int:
    try:
        resolved = build_dir.resolve()
        require(resolved == ROOT / "build" or (ROOT / "build" in resolved.parents),
                "subject output directory must be inside the checkout build directory")
        resolved.mkdir(parents=True, exist_ok=True)
        clean = source_texts(ALL_SURFACES)
        check_contract(clean, ALL_SURFACES)
        guide = clean["docs/native-integration.md"]
        bad = dict(clean)
        bad["docs/native-integration.md"] = replace_cgb_c_qualifier(
            guide,
            "Optional CGB-C evidence proves physical CGB-E hardware behavior.",
        )
        clean_path = resolved / "clean.json"
        bad_path = resolved / "known-bad.json"
        clean_path.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        bad_path.write_text(json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        clean_run = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--subject", str(clean_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        require(clean_run.returncode == 0,
                f"clean subject failed ({clean_run.returncode}): {clean_run.stdout}{clean_run.stderr}")
        bad_run = subprocess.run(
            [sys.executable, "-I", str(SCRIPT), "--subject", str(bad_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        require(bad_run.returncode == 1, f"known-bad subject returned {bad_run.returncode}, expected 1")
        require(
            "CGB-C evidence must not be presented as physical CGB-E qualification" in bad_run.stderr,
            f"known-bad subject failed for an unrelated reason: {bad_run.stdout}{bad_run.stderr}",
        )
        print(f"CGB HDMA claims: prepared and verified {clean_path} and {bad_path}")
        return 0
    except (ContractError, OSError, subprocess.TimeoutExpired) as error:
        print(f"CGB HDMA claims: subject preparation failed: {error}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--native", action="store_true", help="check the four native documents")
    selection.add_argument(
        "--native-player", action="store_true", help="check native, player and preview workflow claims"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--subject", type=Path, metavar="JSON_PATH")
    parser.add_argument("--prepare-prohibition-subjects", type=Path, metavar="BUILD_DIR")
    args = parser.parse_args()
    try:
        if args.self_test:
            return self_test()
        if args.subject:
            return check_subject_file(args.subject)
        if args.prepare_prohibition_subjects:
            return prepare_prohibition_subjects(args.prepare_prohibition_subjects)
        paths = NATIVE_SURFACES if args.native else ALL_SURFACES
        texts = source_texts(paths)
        check_contract(texts, paths)
        print(f"CGB HDMA claims: passed {len(paths)} surfaces")
        return 0
    except (ContractError, OSError, UnicodeError) as error:
        print(f"CGB HDMA claims: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
