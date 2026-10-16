#!/usr/bin/env python3
"""Check the public CGB game-evidence boundary and its negative controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
MAX_DOCUMENT_BYTES = 1_048_576
GAME_GUIDE = "docs/game-acceptance.md"
README = "README.md"
ABSENCE_STATEMENT = "No CGB game-level evidence exists"
UNSUPPORTED_GAME_CLAIM = re.compile(
    r"\bCGB\s+game(?:-level)?\s+(?:acceptance\s+)?"
    r"(?:passes?|passed|is\s+(?:qualified|verified|accepted)|"
    r"has\s+(?:passed|qualified|verified|evidence))\b",
    re.IGNORECASE,
)


class ContractError(Exception):
    """A named failure in the adoption contract."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ContractError(reason)


def read_document(root: Path, relative: str) -> str:
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        size = resolved.stat().st_size
        if size > MAX_DOCUMENT_BYTES:
            raise ContractError(f"document-too-large:{relative}")
        return resolved.read_text(encoding="utf-8")
    except ContractError:
        raise
    except (OSError, UnicodeError, ValueError) as error:
        raise ContractError(f"document-unavailable:{relative}") from error


def check_game(root: Path) -> int:
    text = read_document(root, GAME_GUIDE)
    checks = 0

    require(ABSENCE_STATEMENT in text,
            f"absence-statement-missing:{GAME_GUIDE}")
    checks += 1
    require(UNSUPPORTED_GAME_CLAIM.search(text) is None,
            f"unsupported-cgb-game-qualification:{GAME_GUIDE}")
    checks += 1

    evidence = (
        ("cc2966e1643d480d0780fb6cc5b9ef53d5ef6898", "candidate-source-missing"),
        ("RGBDS v1.0.4", "rgbds-1.0.4-result-missing"),
        ("2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645",
         "rgbds-1.0.1-archive-digest-missing"),
        ("494 assembler errors", "rgbds-1.0.1-build-failure-missing"),
        ("No output ROM or ROM digest was produced", "candidate-output-absence-missing"),
        ("asset rights remain unresolved", "candidate-rights-limit-missing"),
        ("195765b8ca3b0fb7d37b7b92d0242d6c7e01ec71f27f93e565fa081e449cbb92",
         "historical-candidate-digest-missing"),
        ("unverified historical metadata", "historical-candidate-status-missing"),
        ("Libbet and the Magic Floor v0.08 remains the DMG game acceptance",
         "dmg-game-acceptance-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("No physical or perceptual audio/color qualification is claimed",
         "perceptual-output-limit-missing"),
        ("[CGB corpus contract](cgb-corpus.md)", "cgb-corpus-evidence-link-missing"),
    )
    for expected, reason in evidence:
        require(expected in text, f"{reason}:{GAME_GUIDE}")
        checks += 1
    return checks


def check_readme(root: Path) -> int:
    text = read_document(root, README)
    checks = 0
    require(ABSENCE_STATEMENT in text,
            f"absence-statement-missing:{README}")
    checks += 1
    require(UNSUPPORTED_GAME_CLAIM.search(text) is None,
            f"unsupported-cgb-game-qualification:{README}")
    checks += 1
    evidence = (
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("No physical or perceptual audio/color qualification is claimed",
         "perceptual-output-limit-missing"),
        ("CGB test-ROM corpus results are software-model evidence, not game acceptance",
         "corpus-game-evidence-confused"),
        ("[CGB corpus contract](docs/cgb-corpus.md)", "cgb-corpus-evidence-link-missing"),
        ("[game acceptance evidence](docs/game-acceptance.md)",
         "game-evidence-link-missing"),
    )
    for expected, reason in evidence:
        require(expected in text, f"{reason}:{README}")
        checks += 1
    return checks


def check_docs(root: Path) -> int:
    return check_game(root) + check_readme(root)


def child_result(root: Path, mode: str, reason: str | None = None) -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--check", mode, "--root", str(root)],
        cwd=DEFAULT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if reason is None:
        require(result.returncode == 0,
                "self-test-positive-check-failed:" + result.stderr.strip())
        try:
            summary = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ContractError("self-test-positive-summary-invalid") from error
        require(summary.get("positive_success") is True,
                "self-test-positive-summary-missing")
        return
    require(result.returncode != 0, f"negative-control-not-rejected:{reason}")
    require(reason in result.stderr,
            f"negative-control-wrong-reason:{reason}")


def run_self_test_game(root: Path) -> tuple[int, int]:
    baseline = read_document(root, GAME_GUIDE)
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-game-") as temp:
        test_root = Path(temp)
        guide_path = test_root / GAME_GUIDE
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        guide_path.write_text(baseline, encoding="utf-8")
        child_result(test_root, "game")

        mutations = (
            ("missing-absence-statement",
             baseline.replace(ABSENCE_STATEMENT, "", 1),
             f"absence-statement-missing:{GAME_GUIDE}"),
            ("contrary-positive-claim",
             baseline + "\nCGB game passes all acceptance checks.\n",
             f"unsupported-cgb-game-qualification:{GAME_GUIDE}"),
        )
        for name, changed, reason in mutations:
            require(changed != baseline, f"self-test-mutation-no-op:{name}")
            guide_path.write_text(changed, encoding="utf-8")
            child_result(test_root, "game", reason)
        guide_path.write_text(baseline, encoding="utf-8")
        child_result(test_root, "game")
    return 2, 2


def run_self_test_docs(root: Path) -> tuple[int, int]:
    originals = {
        relative: read_document(root, relative)
        for relative in (GAME_GUIDE, README)
    }
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-docs-") as temp:
        test_root = Path(temp)
        paths: dict[str, Path] = {}
        for relative, text in originals.items():
            path = test_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            paths[relative] = path

        child_result(test_root, "docs")
        mutations = (
            ("missing-readme-absence", README, ABSENCE_STATEMENT, "",
             f"absence-statement-missing:{README}"),
            ("missing-guide-absence", GAME_GUIDE, ABSENCE_STATEMENT, "",
             f"absence-statement-missing:{GAME_GUIDE}"),
            ("readme-positive-claim", README, None,
             "\nCGB game passes all acceptance checks.\n",
             f"unsupported-cgb-game-qualification:{README}"),
            ("guide-positive-claim", GAME_GUIDE, None,
             "\nCGB game passes all acceptance checks.\n",
             f"unsupported-cgb-game-qualification:{GAME_GUIDE}"),
            ("missing-readme-corpus-link", README,
             "[CGB corpus contract](docs/cgb-corpus.md)", "",
             f"cgb-corpus-evidence-link-missing:{README}"),
            ("missing-readme-game-link", README,
             "[game acceptance evidence](docs/game-acceptance.md)", "",
             f"game-evidence-link-missing:{README}"),
            ("missing-guide-corpus-link", GAME_GUIDE,
             "[CGB corpus contract](cgb-corpus.md)", "",
             f"cgb-corpus-evidence-link-missing:{GAME_GUIDE}"),
        )
        for name, relative, old, new, reason in mutations:
            original = originals[relative]
            if old is None:
                changed = original + new
            else:
                changed = original.replace(old, new, 1)
                require(changed != original, f"self-test-mutation-no-op:{name}")
            paths[relative].write_text(changed, encoding="utf-8")
            child_result(test_root, "docs", reason)
            paths[relative].write_text(original, encoding="utf-8")
        child_result(test_root, "docs")
    return len(mutations), len(mutations)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", choices=("game", "docs"))
    group.add_argument("--self-test", choices=("game", "docs"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        require(root.is_dir(), "root-not-directory")
        if args.check:
            checks = check_game(root) if args.check == "game" else check_docs(root)
            print(json.dumps({
                "mode": "check",
                "target": args.check,
                "checks": checks,
                "negative_controls": 0,
                "rejected_controls": 0,
                "positive_success": True,
            }, sort_keys=True))
            return 0
        if args.self_test == "game":
            checks = check_game(root)
            negative_controls, rejected_controls = run_self_test_game(root)
        else:
            checks = check_docs(root)
            negative_controls, rejected_controls = run_self_test_docs(root)
        print(json.dumps({
            "mode": "self-test",
            "target": args.self_test,
            "checks": checks,
            "negative_controls": negative_controls,
            "rejected_controls": rejected_controls,
            "positive_success": True,
        }, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError) as error:
        print("verify-v02-adoption fail: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
