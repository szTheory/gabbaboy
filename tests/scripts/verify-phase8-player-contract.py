#!/usr/bin/env python3
"""Check Phase 8's historical unsupported-battery player status contract.

Phase 9 later added MBC2/MBC5 persistence, so this check deliberately reads the
Phase 8 evidence boundary rather than the current checkout's player behavior.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys


# The boundary is a durable annotated tag on the Phase 8 verification commit (D-12). It is resolved once to a
# commit id and never falls back to a literal SHA, so an unreadable tag fails closed.
DEFAULT_BOUNDARY = "historical/phase-08-boundary"
STATUS = (
    "Battery saving is not supported for this cartridge type yet; "
    "progress is not kept"
)
WARNING = f"gabbaboy-player: warning: {STATUS}\\n"
LIMITATION_CLAUSE = (
    "MBC2 type $06 and MBC5 types $1B and $1E battery cartridges run, "
    "but their progress is not saved yet"
)


def resolve_boundary(rev: str) -> str | None:
    """Return the commit id for rev, or None when rev is empty, option-shaped or not a readable commit."""
    if not rev or rev.startswith("-"):
        return None
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    sha = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None
    return sha


def read_boundary(boundary: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{boundary}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"could not read {path} at Phase 8 boundary: {result.stderr.strip()}")
    return result.stdout


def section(source: str, start: str, end: str) -> str:
    try:
        return source.split(start, 1)[1].split(end, 1)[0]
    except IndexError:
        return ""


def verify_contract(files: dict[str, str]) -> list[str]:
    errors: list[str] = []
    main = files["src/player/main.c"]
    session = files["src/player/session.c"]
    session_test = files["tests/player/test_session.c"]
    limitations = files["src/player/limitations.h"]
    limitation_test = files["tests/player/test_limitations.c"]
    player_cmake = files["tests/player/CMakeLists.txt"]

    startup = section(
        main,
        "static bool create_machine(player *app, const char *demo_rom_path) {",
        "static bool create_video(player *app, bool hidden) {",
    )
    replacement = section(
        main,
        "static bool replace_session_rom(player *app, const char *path) {",
        "static void finish_transition(player *app, bool continue_without_saving);",
    )
    for label, path in (("startup", startup), ("replacement", replacement)):
        branch = section(
            path,
            "else if (app->save_identity.battery_unsupported)",
            "\n    } else {" if label == "startup" else "\n    } else\n",
        )
        # The replacement branch ends in a newline plus plain else; keep a
        # fallback slice so harmless formatting does not hide its contents.
        if not branch:
            marker = "else if (app->save_identity.battery_unsupported)"
            branch = path.split(marker, 1)[1] if marker in path else ""
        if f'set_status(app, "{STATUS}");' not in branch:
            errors.append(f"{label} status branch does not set the pinned warning copy")
        if f'fputs("{WARNING}", stderr);' not in branch:
            errors.append(f"{label} status branch does not write the pinned stderr warning")

    if not startup or not replacement:
        errors.append("startup or replacement ROM-load function was not found")

    if not (
        "out_identity->battery_unsupported = rom[0x147u] == 0x06u ||" in session
        and "rom[0x147u] == 0x1Bu" in session
        and "rom[0x147u] == 0x1Eu;" in session
        and "out_identity->battery_backed = rom[0x147u] == 0x03u &&" in session
    ):
        errors.append("session identity does not distinguish the three unsupported battery types from MBC1")

    # Prove the status field is connected to the user-visible window title.
    set_status = section(
        main,
        "static void set_status(player *app, const char *status) {",
        "static void show_help(player *app) {",
    )
    title = section(
        main,
        "static void format_window_title(const player *app, char *title, size_t title_size) {",
        "static void update_window_title(player *app) {",
    )
    update_title = section(
        main,
        "static void update_window_title(player *app) {",
        "static void set_status(player *app, const char *status) {",
    )
    if not (
        "snprintf(app->status, sizeof(app->status), \"%s\", status)" in set_status
        and "update_window_title(app)" in set_status
        and "app->status[0] == '\\0' ? \"Ready\" : app->status" in title
        and "SDL_SetWindowTitle(app->window, title)" in update_title
    ):
        errors.append("status setter is not wired to the window title")

    if not (
        'static const uint8_t types[] = {0x06u, 0x1Bu, 0x1Eu};' in session_test
        and "identity.battery_unsupported" in session_test
        and "player_session_load_battery" in session_test
        and "player_session_save_battery" in session_test
        and "player_session_lock_battery" in session_test
        and "directory_is_empty(saves)" in session_test
        and 'test_name MATCHES "^player_session_[a-z0-9_]+$"' in player_cmake
    ):
        errors.append("boundary session test does not exercise unsupported types and empty-save-directory behavior")

    if not (
        LIMITATION_CLAUSE in limitations
        and LIMITATION_CLAUSE in limitation_test
        and "strcmp(GBB_PLAYER_LIMITATIONS_TEXT, expected) != 0" in limitation_test
    ):
        errors.append("limitations clause is not pinned byte-for-byte by its test")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run the contract and fail-first controls")
    parser.add_argument(
        "--boundary",
        default=DEFAULT_BOUNDARY,
        help="revision of the Phase 8 verification commit (default: %(default)s)",
    )
    args = parser.parse_args()
    boundary = resolve_boundary(args.boundary)
    if boundary is None:
        print(f"phase8-player-contract: FAIL: boundary unreadable: {args.boundary}", file=sys.stderr)
        return 1

    paths = (
        "src/player/main.c",
        "src/player/session.c",
        "tests/player/test_session.c",
        "src/player/limitations.h",
        "tests/player/test_limitations.c",
        "tests/player/CMakeLists.txt",
    )
    try:
        files = {path: read_boundary(boundary, path) for path in paths}
    except RuntimeError as error:
        print(f"phase8-player-contract: FAIL: {error}", file=sys.stderr)
        return 1

    errors = verify_contract(files)
    if errors:
        for error in errors:
            print(f"phase8-player-contract: FAIL: {error}", file=sys.stderr)
        return 1
    print(f"phase8-player-contract: PASS boundary={boundary} startup=replacement=stderr=copy=save-guard")

    if not args.self_test:
        return 0

    # An unreadable boundary is its own failure class: empty, option-shaped and missing revisions fail closed.
    for bad in ("", "--help", "refs/tags/does-not-exist-phase8"):
        if resolve_boundary(bad) is not None:
            print(f"phase8-player-contract self-test: unreadable boundary {bad!r} was accepted", file=sys.stderr)
            return 1

    original_main = files["src/player/main.c"]
    mutated_main = original_main.replace(WARNING, "", 1)
    if mutated_main == original_main:
        print("phase8-player-contract self-test: failed to mutate stderr warning", file=sys.stderr)
        return 1
    mutated_files = dict(files)
    mutated_files["src/player/main.c"] = mutated_main
    if not verify_contract(mutated_files):
        print("phase8-player-contract self-test: removed stderr warning was not rejected", file=sys.stderr)
        return 1

    mutated_files = dict(files)
    mutated_files["tests/player/test_limitations.c"] = files[
        "tests/player/test_limitations.c"
    ].replace(LIMITATION_CLAUSE, "Battery copy changed", 1)
    if not verify_contract(mutated_files):
        print("phase8-player-contract self-test: changed pinned copy was not rejected", file=sys.stderr)
        return 1

    # A missing runtime branch must also fail even when the status string is
    # still present in the sibling startup path and documentation.
    marker = "else if (app->save_identity.battery_unsupported)"
    replacement_pos = original_main.find("static bool replace_session_rom(player *app, const char *path) {")
    branch_pos = original_main.find(marker, replacement_pos)
    if replacement_pos < 0 or branch_pos < 0:
        print("phase8-player-contract self-test: replacement branch was not found", file=sys.stderr)
        return 1
    mutation = original_main[:branch_pos] + original_main[branch_pos:].replace(marker, "else if (false)", 1)
    mutated_files = dict(files)
    mutated_files["src/player/main.c"] = mutation
    if not verify_contract(mutated_files):
        print("phase8-player-contract self-test: removed replacement warning branch was not rejected", file=sys.stderr)
        return 1

    for label, statement in (
        ("status-call-removed", f'set_status(app, "{STATUS}");'),
        ("stderr-call-removed", f'fputs("{WARNING}", stderr);'),
    ):
        mutated_files = dict(files)
        mutated_files["src/player/main.c"] = original_main.replace(statement, "", 1)
        if mutated_files["src/player/main.c"] == original_main or not verify_contract(mutated_files):
            print(f"phase8-player-contract self-test: {label} was not rejected", file=sys.stderr)
            return 1

    print("phase8-player-contract self-test: PASS controls=unreadable-boundary,warning-removed,pinned-copy-changed,branch-removed,status-call-removed,stderr-call-removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
