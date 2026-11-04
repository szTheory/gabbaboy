#!/usr/bin/env python3
"""Check the v0.2.0 adoption, limitation, notice and release-note claims.

Every public claim surface is parsed as prose (HTML comments and fenced code are
removed first, so a comment-only occurrence never satisfies a requirement),
public symbols are resolved against the installed header, third-party notices
are bound to the actual fixture bytes, and rendered release notes are checked
for the exact version, the absence sentence and the ledger link.  The
self-tests run the real command line against isolated mutated copies.
"""
from __future__ import annotations

import argparse
from array import array
from bisect import bisect_right
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import string
import subprocess
import sys
import tempfile
from typing import Callable
import unicodedata
from html import unescape


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
CLAIMS_SCRIPT = SCRIPT.parent / "verify-cgb-corpus-claims.py"
SUPPORT_LEDGER_SCRIPT = SCRIPT.parent / "verify-support-ledger.py"
MAX_DOCUMENT_BYTES = 1_048_576
MAX_SOURCE_BYTES = 1_048_576
MAX_NOTES_BYTES = 262_144

GAME_GUIDE = "docs/game-acceptance.md"
README = "README.md"
NATIVE = "docs/native-integration.md"
SAVES = "docs/cartridge-and-saves.md"
PROFILE = "docs/cgb-profile.md"
AUDIO = "docs/audio-and-playback.md"
PREVIEW = "docs/preview.md"
RELEASE = "docs/release.md"
UNRELEASED = "docs/support/unreleased.md"
NOTICES = "THIRD_PARTY_NOTICES.md"
HEADER = "include/gabbaboy/gabbaboy.h"

PERF_ATTRIBUTION = "tests/baseline/perf-attribution-v1.json"
RAW_HTML_CONSTRUCT = re.compile(
    r"(?<!\\)(?:\\\\)*(?:"
    r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?\s*/?>|"
    r"<![A-Z][\s\S]*?(?:>|$)|<\?[A-Za-z][\s\S]*?(?:\?>|$)|"
    r"<!\[CDATA\[|<(?:script|pre|style)(?=[ \t\r\n>]|$))",
    re.DOTALL | re.IGNORECASE)


def tree_identity(root: Path) -> tuple[str, str]:
    """(release version, bound ledger path) of a tree (D-28).

    The version is CMakeLists.txt's project VERSION and must equal the release-please manifest entry; the ledger is
    the newest docs/support/vX.Y.Z.md in the same major.minor that is not above that version.
    """
    try:
        cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")
        manifest = json.loads((root / ".release-please-manifest.json").read_text(encoding="utf-8"))
        names = sorted(entry.name for entry in (root / "docs/support").iterdir())
    except (OSError, ValueError) as error:
        raise SystemExit(f"verify-v02-adoption fail: version-unreadable:{error}")
    return identity_from_sources(cmake, manifest, names)


def identity_from_sources(cmake: str, manifest: object, names: list[str]) -> tuple[str, str]:
    """Select the version and newest matching support ledger from one source identity."""
    match = re.search(r"^project\(\s*\w+\s+VERSION\s+(\d+)\.(\d+)\.(\d+)[\s)]", cmake, re.M)
    if not match:
        raise SystemExit("verify-v02-adoption fail: version-missing:CMakeLists.txt")
    version = ".".join(match.groups())
    if not isinstance(manifest, dict) or manifest.get(".") != version:
        raise SystemExit(f"verify-v02-adoption fail: version-mismatch:{version}:{manifest!r}")
    release = tuple(int(part) for part in match.groups())
    candidates = []
    for name in names:
        ledger = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)\.md", name)
        if ledger:
            numbers = tuple(int(part) for part in ledger.groups())
            if numbers[:2] == release[:2] and numbers <= release:
                candidates.append((numbers, name))
    if not candidates:
        raise SystemExit(f"verify-v02-adoption fail: support-ledger-missing:{version}")
    return version, "docs/support/" + max(candidates)[1]


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({"GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1",
                        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"})
    return environment


def identity_at_revision(repo: Path, rev: str) -> tuple[str, str]:
    """Derive release identity from Git objects at the judged revision, never the live checkout."""
    if re.fullmatch(r"[0-9a-f]{40}", rev) is None:
        raise ContractError("release-notes-revision-invalid")
    git_env = git_environment()
    commit = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}^{{commit}}"],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, check=False, timeout=10, env=git_env)
    if commit.returncode != 0:
        raise ContractError("release-notes-revision-invalid")
    try:
        cmake = subprocess.check_output(["git", "-C", str(repo), "show", f"{rev}:CMakeLists.txt"],
                                        stderr=subprocess.DEVNULL, timeout=10,
                                        env=git_env).decode("utf-8", "strict")
        manifest = json.loads(subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{rev}:.release-please-manifest.json"],
            stderr=subprocess.DEVNULL, timeout=10, env=git_env).decode("utf-8", "strict"))
        names_raw = subprocess.check_output(["git", "-C", str(repo), "ls-tree", "--name-only",
                                             f"{rev}:docs/support"],
                                            stderr=subprocess.DEVNULL, timeout=10,
                                            env=git_env).decode("utf-8", "strict")
    except (OSError, UnicodeError, subprocess.SubprocessError, ValueError) as error:
        raise ContractError("release-notes-revision-input-unavailable") from error
    names = [name for name in names_raw.splitlines() if name]
    try:
        return identity_from_sources(cmake, manifest, names)
    except SystemExit as error:
        raise ContractError("release-notes-revision-identity-invalid") from error


RELEASE_VERSION, LEDGER = tree_identity(DEFAULT_ROOT)
LEDGER_VERSION = LEDGER.rsplit("/v", 1)[1].removesuffix(".md")
ABSENCE_STATEMENT = "No CGB game-level evidence exists"
ABSENCE_SENTENCE = "No CGB game-level evidence exists."

# Surfaces whose symbols must resolve and whose claims must stay qualified.
PUBLIC_SURFACES = (
    README, NATIVE, SAVES, GAME_GUIDE, PROFILE, AUDIO, PREVIEW, RELEASE,
    LEDGER, UNRELEASED, NOTICES,
)
# Internal constants that public prose names for explanation.  Each must still
# exist in the named source file, so the allowance cannot outlive the symbol.
INTERNAL_SYMBOLS = {
    "GBB_LEGACY_MAX_ROM_SIZE": "src/core/gabbaboy.c",
    "GBB_MAX_ROM_SIZE": "src/core/gabbaboy.c",
    "GBB_DMA_BYTE_PERIOD_HALF_DOTS": "src/core/gabbaboy.c",
    "GBB_DOTS_PER_LINE": "src/core/gabbaboy.c",
    "GBB_HALF_DOTS_PER_DOT": "src/core/gabbaboy.c",
    "GBB_HALF_DOTS_PER_T_DOUBLE": "src/core/gabbaboy.c",
    "GBB_HALF_DOTS_PER_T_NORMAL": "src/core/gabbaboy.c",
    "GBB_LINES_PER_FRAME": "src/core/gabbaboy.c",
    "GBB_MASTER_HALF_DOTS_PER_SECOND": "src/core/gabbaboy.c",
    "GBB_SPEED_SWITCH_STALL_T": "src/core/gabbaboy.c",
    "GBB_STOP_SWITCH_COST_HALF_DOTS": "src/core/gabbaboy.c",
    "GBB_T_PER_M": "src/core/gabbaboy.c",
    "GBB_AUDIO_MEASURE_TIMEOUT_SECONDS": "tests/scripts/measure-audio-playback.sh",
}
SYMBOL_TOKEN = re.compile(r"\b(?:gbb|GBB)_[A-Za-z0-9_]*[A-Za-z0-9]")

UNSUPPORTED_GAME_CLAIM = re.compile(
    r"\bCGB\s+game(?:-level)?\s+(?:acceptance\s+)?"
    r"(?:passes?|passed|is\s+(?:qualified|verified|accepted)|"
    r"has\s+(?:passed|qualified|verified|evidence))\b",
    re.IGNORECASE,
)


# Frozen from Unicode 18.0 DerivedCoreProperties.txt, which defines this property.
DEFAULT_IGNORABLE_CODEPOINT_RANGES_UCD_18_0 = (
    (0x00AD, 0x00AD), (0x034F, 0x034F), (0x061C, 0x061C),
    (0x115F, 0x1160), (0x17B4, 0x17B5), (0x180B, 0x180D),
    (0x180E, 0x180E), (0x180F, 0x180F), (0x200B, 0x200F),
    (0x202A, 0x202E), (0x2060, 0x206F), (0x3164, 0x3164),
    (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF), (0xFFA0, 0xFFA0),
    (0xFFF0, 0xFFF8), (0x1BCA0, 0x1BCA3), (0x1D173, 0x1D17A),
    (0xE0000, 0xE0FFF),
)
DEFAULT_IGNORABLE_CODEPOINT_STARTS_UCD_18_0 = tuple(
    start for start, _ in DEFAULT_IGNORABLE_CODEPOINT_RANGES_UCD_18_0
)
DEFAULT_IGNORABLE_CLAIM_SEPARATORS = (
    ("combining-grapheme-joiner", "\u034f"),
    ("hangul-filler", "\u3164"),
    ("variation-selector-16", "\ufe0f"),
    ("reserved-default-ignorable", "\u2065"),
)
COMMONMARK_REFERENCED_GAME_CLAIMS = (
    ("hex-zero-width-space", "CGB&#x200b; game passes all acceptance checks."),
    ("decimal-zero-width-space", "CGB&#8203; game passes all acceptance checks."),
    ("named-zero-width-space", "CGB&ZeroWidthSpace; game passes all acceptance checks."),
    ("hex-combining-grapheme-joiner", "CGB&#x34f; game passes all acceptance checks."),
    ("hex-visible-space", "CGB&#x20; game passes all acceptance checks."),
    ("encoded-cgb-letter", "&#67;GB game passes all acceptance checks."),
)
COMMONMARK_CHARACTER_REFERENCE = re.compile(
    r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]*);"
)
# Match odd runs of backslashes immediately before a CommonMark line ending.
COMMONMARK_HARD_LINE_BREAK = re.compile(r"(?<!\\)(?:\\\\)*\\(?=\r\n|\r|\n)")
COMMONMARK_HARD_BREAK_GAME_CLAIMS = (
    ("backslash-lf", "CGB\\\ngame passes all acceptance checks."),
    ("backslash-cr", "CGB\\\rgame passes all acceptance checks."),
    ("backslash-crlf", "CGB\\\r\ngame passes all acceptance checks."),
    ("backslash-lf-encoded-space", "CGB\\\n&#x20;game passes all acceptance checks."),
    ("soft-break-lf-encoded-space", "CGB\n&#x20;game passes all acceptance checks."),
)


def is_default_ignorable_codepoint(codepoint: int) -> bool:
    """Check the frozen Unicode 18.0 Default_Ignorable_Code_Point ranges."""
    index = bisect_right(DEFAULT_IGNORABLE_CODEPOINT_STARTS_UCD_18_0, codepoint) - 1
    return (index >= 0
            and codepoint <= DEFAULT_IGNORABLE_CODEPOINT_RANGES_UCD_18_0[index][1])


def is_invisible_claim_separator(char: str) -> bool:
    return (unicodedata.category(char) == "Cf"
            or is_default_ignorable_codepoint(ord(char)))


def decode_commonmark_character_references(text: str) -> str:
    """Decode valid CommonMark references in prose before claim matching."""
    return COMMONMARK_CHARACTER_REFERENCE.sub(
        lambda match: unescape(match.group(0)), text)


def unsupported_game_claim_match(text: str) -> re.Match[str] | None:
    """Match visible claims after Markdown break/reference and invisible-char normalization."""
    text = COMMONMARK_HARD_LINE_BREAK.sub(" ", text)
    text = decode_commonmark_character_references(text)
    claim_text = "".join(
        char for char in text
        if not is_invisible_claim_separator(char)
    )
    return UNSUPPORTED_GAME_CLAIM.search(claim_text)


# A signing or notarization claim is allowed only in its negated form.
FALSE_SIGNING_CLAIM = re.compile(
    r"(?:(?<!un)(?<!not )signed\s+and\s+notarized|"
    r"(?<!not )notarized\s+and\s+signed|"
    r"\b(?:player|package|archive|binary|artifact|release|build)s?\s+"
    r"(?:is|are|was|were)\s+(?:both\s+)?(?:code[- ]?)?(?:signed|notarized)\b)",
    re.IGNORECASE,
)
def publication_claim_pattern(version: str) -> re.Pattern[str]:
    return re.compile(
        r"\bv?" + re.escape(version) + r"\s+(?:is|has\s+been|was)\s+(?:now\s+)?"
        r"(?:published|released|available|shipped|live)\b",
        re.IGNORECASE,
    )


FALSE_PUBLICATION_CLAIM = publication_claim_pattern(RELEASE_VERSION)
FALSE_RETRY_TAMPER_CLAIM = re.compile(
    r"\bretry(?:\s+check)?\b.{0,120}\b(?:"
    r"(?:detects?|detecting|proves?)\s+(?:tampering|a\s+(?:swap|replacement))|"
    r"(?:provides?|offers?|performs?)\s+tamper[- ]detection|"
    r"tamper[- ]proof)\b",
    re.IGNORECASE,
)
PENDING_V030_SECTION = re.compile(
    r"(?im)^#{1,6}\s+[^\n]*\bpending\s+v0\.3\.0\b"
)
FALSE_PLATFORM_CLAIM = re.compile(
    r"(?:\bsupports?\s+(?:all|every|any)\s+(?:architectures?|platforms?|operating\s+systems?)\b|"
    r"\bminimum\s+(?:supported\s+)?(?:OS|operating\s+system)\s+(?:version\s+)?is\b)",
    re.IGNORECASE,
)
FALSE_PERCEPTUAL_CLAIM = re.compile(
    r"\b(?:perceptual|listening)\s+(?:audio|color|colour|quality)\s+"
    r"(?:is|are)\s+(?:qualified|verified|proven|measured)\b",
    re.IGNORECASE,
)
FALSE_FUZZ_CLAIM = re.compile(
    r"\b(?:fuzz(?:ing)?\s+campaign|bounded\s+fuzz\s+campaign)\s+"
    r"(?:has\s+)?(?:passed|passes|is\s+green|succeeded)\b",
    re.IGNORECASE,
)
FALSE_CROSS_VERSION_STATE_CLAIM = re.compile(
    r"\b(?:save\s+)?states?\b.{0,60}\b(?:load|loads|loaded|loadable)\b"
    r".{0,60}\b(?:across|between|in|to)\s+(?:(?:any|another|different)\s+)?"
    r"(?:gabbaBoy\s+)?(?:releases?|versions?|builds?)\b|"
    r"\b(?:across|between|in|to)\s+(?:(?:any|another|different)\s+)?"
    r"(?:gabbaBoy\s+)?(?:releases?|versions?|builds?)\b.{0,60}"
    r"\b(?:save\s+)?states?\b.{0,60}\b(?:load|loads|loaded|loadable)\b",
    re.IGNORECASE,
)
FALSE_DURABILITY_CLAIM = re.compile(
    r"\b(?:power[- ]loss|crash|process\s+death)\b.{0,60}"
    r"\b(?:durab\w*|surviv\w*|guarantee\w*|preserv\w*|saf\w*)\b|"
    r"\b(?:durab\w*|surviv\w*|guarantee\w*|preserv\w*|saf\w*)\b.{0,60}"
    r"\b(?:power[- ]loss|crash|process\s+death)\b",
    re.IGNORECASE,
)
FALSE_WINDOWS_HOST_CLAIM = re.compile(
    r"\b(?:windows|win32)\b.{0,60}\b(?:host\s+mode|--save-dir)\b.{0,30}"
    r"\b(?:supported|available|enabled|works?|accepted|runs?)\b|"
    r"\b(?:host\s+mode|--save-dir)\b.{0,30}"
    r"\b(?:supported|available|enabled|works?|accepted|runs?)\b.{0,60}"
    r"\b(?:windows|win32)\b",
    re.IGNORECASE,
)
UNSCOPED_STATE_CLAIM = re.compile(
    r"\b(?:state|save)\s+(?:api|support|loading|files?|format|states?)\b.{0,50}"
    r"\b(?:portable|compatible|supported|available|loadable|works?)\b"
    r"(?!\s+only\s+(?:(?:in|by)\s+)?(?:the\s+)?exact\s+(?:GabbaBoy\s+)?release)|"
    r"\b(?:portable|compatible|supported|supports?|available|loadable|works?)\b"
    r"(?![^\n]{0,50}\bonly\s+(?:(?:in|by)\s+)?(?:the\s+)?exact\s+(?:GabbaBoy\s+)?release)"
    r".{0,50}\b(?:state\s+(?:api|support|loading|files?|format)|save\s+states?)\b|"
    r"\b(?:supports?|has)\b.{0,40}\b(?:save\s+states?|state\s+(?:api|files?|format))\b"
    r".{0,40}\b(?:all|every|any|cross[- ]platform)\b",
    re.IGNORECASE,
)
CLAIM_BOUNDARY_RULES = (
    (FALSE_CROSS_VERSION_STATE_CLAIM, "false-cross-version-state-claim"),
    (FALSE_DURABILITY_CLAIM, "false-durability-claim"),
    (FALSE_WINDOWS_HOST_CLAIM, "false-windows-host-claim"),
    (UNSCOPED_STATE_CLAIM, "unscoped-state-claim"),
)
CLAIM_BOUNDARY_TWINS = (
    "Save states load only in the exact GabbaBoy release that wrote them.",
    "No power-loss guarantee is made for a saved state.",
    "Host mode is POSIX-only; Windows refuses `--save-dir`.",
    "State loading is supported only by the exact release that wrote the state.",
)
REBOUND_ATTRIBUTION = re.compile(r"\bRebound\b")

STATE_VERSION_SENTENCE = "Save states load only in the exact GabbaBoy release that wrote them."
HOST_POSIX_SENTENCE = "Host mode is POSIX-only; Windows refuses `--save-dir`."
HOST_POSIX_VISIBLE = "Host mode is POSIX-only; Windows refuses"
PERF_HEAD_LIMITATION = (
    "The Ir attribution figure was measured at @HEAD@ on main before the release commit; "
    "the release-binding Ir check is the perf-gate receipt verified at the tagged source."
)

HISTORICAL_PERFORMANCE_REQUIRED = (
    ("historical evidence", "historical-performance-disclosure-missing"),
    ("candidate source `ab301aa69b1f085050fd66bf7b1378863a0821f2`",
     "historical-performance-disclosure-missing"),
    ("baseline source `e30d168f7fc61de8db0a3801e7b1736362912cb7`",
     "historical-performance-disclosure-missing"),
    ("`original-wram-tracer-1m-half-dots-v1`", "historical-performance-disclosure-missing"),
    ("DMG-CPU-B", "historical-performance-disclosure-missing"),
    ("`fixtures/tracer/tracer.gb`", "historical-performance-disclosure-missing"),
    ("`ded6a499118b57539710892d58b4d7ced2269f08d447eed1451201d8ad65ec8d`",
     "historical-performance-disclosure-missing"),
    ("1,000,000 half-dot budget", "historical-performance-disclosure-missing"),
    ("correctness digest `4c7a57ff3d50d228`", "historical-performance-disclosure-missing"),
    ("Linux x86_64", "historical-performance-disclosure-missing"),
    ("30 paired samples after 3 warmups", "historical-performance-disclosure-missing"),
    ("+14.86% slower", "historical-performance-disclosure-missing"),
    ("±1.62%", "historical-performance-disclosure-missing"),
    ("`accepted-with-disclosed-regression`", "historical-performance-disclosure-missing"),
    ("not a current approval, fresh result, or equivalent-speed claim",
     "historical-performance-disclosure-missing"),
)

# (phrase, failure reason) pairs.  Phrases match whitespace-normalized prose.
REQUIRED: dict[str, tuple[tuple[str, str], ...]] = {
    README: (
        ("opaque `gbb_instance`", "api-instance-missing"),
        ("`gbb_queue_events`", "api-queue-events-missing"),
        ("MBC30 is rejected", "mbc30-rejection-missing"),
        ("emulated-time real-time clock and explicit host catch-up",
         "rtc-host-catchup-missing"),
        ("host-owned battery persistence", "host-save-ownership-missing"),
        (f"[versioned support ledger]({LEDGER})",
         "support-ledger-link-missing"),
        ("General game compatibility is not claimed", "general-game-limit-missing"),
        ("Playstead remains a future integration", "playstead-limit-missing"),
        ("`GabbaBoy::core`", "package-target-missing"),
    ),
    NATIVE: (
        ("`GBB_NO_RTC`", "rtc-error-missing"),
        ("`GBB_RTC_BLOCK_SIZE`", "rtc-block-size-missing"),
        ("RGB555", "rgb555-contract-missing"),
        ("not the SDL player's versioned/checksummed save envelope",
         "raw-save-boundary-missing"),
        ("it is not a live GabbaBoy/Playstead integration", "playstead-limit-missing"),
        ("caller-owned", "caller-ownership-missing"),
    ),
    SAVES: (
        ("21-byte `GBB_RTC_BLOCK_SIZE` clock block", "rtc-block-contract-missing"),
        ("MBC30", "mbc30-rejection-missing"),
        ("`GBB_NO_RTC`", "rtc-error-missing"),
        ("The player does not auto-detect raw `.sav` files", "raw-save-boundary-missing"),
        ("caller-owned buffers", "caller-ownership-missing"),
    ),
    LEDGER: (
        *HISTORICAL_PERFORMANCE_REQUIRED,
        (ABSENCE_STATEMENT, "absence-statement-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("Boot ROMs are skipped", "boot-path-limit-missing"),
        ("no CGB mode-3 timing qualification", "mode3-limit-missing"),
        ("no general game compatibility percentage", "general-game-limit-missing"),
        ("software model", "model-applicability-missing"),
    ),
    PROFILE: (
        ("CGB-CPU-E software model", "cgb-model-missing"),
        ("DMG compatibility mode", "compat-mode-missing"),
        ("raw RGB555", "rgb555-contract-missing"),
        ("digital PCM", "digital-pcm-missing"),
        ("`$FF`", "compat-pcm-read-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("CGB mode-3 timing is not claimed", "mode3-limit-missing"),
        (ABSENCE_STATEMENT, "absence-statement-missing"),
        ("No physical or perceptual audio/color qualification is claimed",
         "perceptual-output-limit-missing"),
    ),
    AUDIO: (
        ("digital DAC inputs", "digital-pcm-missing"),
        ("`$FF`", "compat-pcm-read-missing"),
        ("`SDL_AUDIO_DRIVER=dummy`", "dummy-sdl-limit-missing"),
        ("SDL dummy driver", "dummy-sdl-limit-missing"),
        ("no physical CGB-E timing or waveform", "physical-cgb-limit-missing"),
        ("48,000 signed 16-bit interleaved stereo frames", "pcm-format-missing"),
        ("no physical or perceptual audio qualification is claimed",
         "perceptual-output-limit-missing"),
    ),
    PREVIEW: (
        ("The package is unsigned and not notarized", "unsigned-limit-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("SDL dummy audio path", "dummy-sdl-limit-missing"),
        ("raw RGB555", "rgb555-contract-missing"),
        (f"[v{LEDGER_VERSION} support ledger](support/v{LEDGER_VERSION}.md)", "support-ledger-link-missing"),
        ("No CGB game-level evidence exists", "absence-statement-missing"),
        ("[native integration guide](native-integration.md)", "native-guide-link-missing"),
    ),
    RELEASE: (
        *HISTORICAL_PERFORMANCE_REQUIRED,
        ("**+14.86% slower than v0.1.0 with a ±1.62% margin**",
         "historical-performance-disclosure-missing"),
        ("tested runner/configuration combinations, not minimum OS versions, "
         "all-architecture promises, or general platform support floors",
         "runner-label-limit-missing"),
        ("GitHub generated source archives retain the admitted licensed fixtures "
         "and their notices", "source-archive-distinction-missing"),
        ("installed and downloaded product packages remain fixture-free",
         "product-package-distinction-missing"),
        ("unsigned and not notarized", "unsigned-limit-missing"),
        ("`support-ledger.json`", "ledger-sidecar-missing"),
        ("`v02-performance-receipt.json`", "performance-sidecar-missing"),
        ("`v02-fuzz-receipt.json`", "fuzz-sidecar-missing"),
        ("identity and consistency check", "retry-identity-wording-missing"),
        ("The `v02-*` evidence names are the evidence-schema family",
         "evidence-name-note-missing"),
        ("back up the preference directory", "upgrade-guidance-missing"),
        ("slots and the undo file do not survive an upgrade",
         "upgrade-guidance-missing"),
        ("`version-pr-gate` is not a required check",
         "pre-tag-gate-enforcement-missing"),
        ("no fuzz campaign result is claimed by this document", "fuzz-limit-missing"),
        ("installed-prefix check", "installed-proof-missing"),
        ("downloaded-asset check", "downloaded-proof-missing"),
        (f"[support ledger](support/v{LEDGER_VERSION}.md)", "support-ledger-link-missing"),
        (ABSENCE_STATEMENT, "absence-statement-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("does not establish physical-device, perceptual, or hardware equivalence",
         "perceptual-output-limit-missing"),
        ("this page makes no publication claim for the version in this tree",
         "publication-limit-missing"),
        ("The last qualified release is v0.3.0. Phase 23 prepares v0.4.0 through the existing release-please path.",
         "v04-preparation-scope-missing"),
        ("generated `docs/support/v0.4.0.md` ledger, and rendered release notes must all identify exactly v0.4.0",
         "v04-version-agreement-missing"),
        ("The release-notes preface and support ledger share the validated immutable `tests/data/support-claims-v0.4.json` profile",
         "v04-shared-copy-missing"),
        ("Potion Panic stopped before a source identity was returned: its creator-linked Codeberg source could not be reached, and exact component grants plus repository/public-CI scope remain unestablished",
         "v04-potion-panic-outcome-missing"),
        ("µCity 1.3 stopped at the required `source/engine/hardware.inc` component, which has no identified grant or notice establishing repository/public-CI scope",
         "v04-ucity-outcome-missing"),
        ("Neither candidate was built or run; no CGB game was admitted. These source/rights-scope outcomes do not establish a license prohibition",
         "v04-game-admission-boundary-missing"),
        ("The CGB-CPU-E native-mode RGB555/PCM result is original-harness-only; its digests establish repeatability only",
         "v04-harness-boundary-missing"),
        ("Phase 22 is a synthetic composition tracer and metadata-only assessment: 513 named entries, seven unresolved real-fixture gates, zero real fixtures admitted, and zero real fixtures executed",
         "v04-diagnostic-accounting-missing"),
        ("FIXT-01, RIGHTS-01, DIAG-01, DIAG-02, and REL-01 remain Pending until their separate release evidence is accepted",
         "v04-pending-status-missing"),
        ("The established product matrix remains Linux x64, macOS arm64, and Windows x64 core archives, plus the macOS arm64 player",
         "v04-product-matrix-missing"),
        ("No Linux or Windows packaged-player game smoke is claimed; the player is macOS arm64 only",
         "v04-player-platform-limit-missing"),
        ("macOS 15.0 is the minimum deployment target and the build used the macOS 15.5 SDK",
         "v04-macos-deployment-caveat-missing"),
        ("Save states load only in the exact GabbaBoy release that wrote them. Host mode is POSIX-only, and Windows refuses `--save-dir`",
         "v04-host-state-compatibility-missing"),
        ("The deterministic instruction-count gate and native realtime floor remain blocking; paired wall-clock timing is advisory and cannot approve a release",
         "v04-performance-boundary-missing"),
        ("H → R1 → W → R2 → nightly → pre-tag gate",
         "v04-operator-sequence-missing"),
        ("A note or body regeneration, moved tag, or changed source invalidates the window and keeps the release on hold",
         "v04-window-recovery-hold-missing"),
        ("After tagging, the existing trusted release path must still build, attach, download, and verify the real core and player archive bytes, installed consumers, notices, and fixture exclusion before the draft can be published",
         "v04-downloaded-byte-gate-missing"),
        ("If v0.4.0 notes omit a required disclosure, keep the draft unpublished",
         "v04-recovery-hold-missing"),
    ),
    UNRELEASED: (
        ("Reconciled into v0.3.0: the save-state and host-contract entries are scoped claims",
         "unreleased-reconciliation-missing"),
    ),
}
# Claim markers parsed with the production CGB claim parser.
MARKED_SECTIONS: dict[str, tuple[tuple[str, tuple[tuple[str, str], ...]], ...]] = {
    PROFILE: (
        ("profile", (
            ("digital DAC inputs", "marked-profile-pcm-missing"),
            ("physical CGB-E audio measurements", "marked-profile-limit-missing"),
        )),
    ),
    AUDIO: (
        ("audio", (
            ("compatibility mode reads `$FF`", "marked-audio-compat-missing"),
            ("no physical CGB-E timing or waveform", "marked-audio-limit-missing"),
        )),
    ),
}
NOTICE_REQUIRED = (
    ("GitHub generated source archives retain the admitted licensed fixtures and "
     "their notices", "source-archive-distinction-missing"),
    ("Installed core packages carry exactly the original project-authored tracer, visible demo, "
     "and MBC1 continuation fixtures with their pinned notices. The optional player carries only its listed demo "
     "and continuation fixtures with their notices.",
     "product-package-distinction-missing"),
    ("Controlled game and diagnostic bytes remain repository-test inputs and are excluded from binary products.",
     "product-package-distinction-missing"),
    ("per-asset rights rest on single-author history plus the repository-wide zlib licence, not a per-asset upstream grant",
     "libbet-rights-disclosure-missing"),
    ("Mooneye mbc2/mbc5 derivative test ROMs (15) | Mooneye Test Suite revision `31510e12eea6286d36eea060a6adde755e1067aa` (Gekkio), MIT; headless-report derivatives with a zero-filled font replacement (see `fixtures/mooneye-mbc/FONT-LICENSE.txt`); WLA-DX is a GPL-2.0-or-later build tool that is not bundled or linked; ROM digests are a local rebuild until the hosted match in Plan 08-07; repository test fixtures only, not installed or packaged",
     "mooneye-mbc-rights-disclosure-missing"),
    ("MagenTests out-of-bounds SRAM ROMs (3) | MagenTests release 0.5.0 at pinned commit `3f9c090f16e5a721db776febb9ba7d773e1c819c` (alloncm), MIT; build-time `hardware.inc` (gbdev, commit `21ef22d`) is CC0-1.0; hardware-derived, author-attested; repository test fixtures only, not installed or packaged",
     "magentests-rights-disclosure-missing"),
    ("AGE CGB speed-switch ROMs | AGE test ROMs by Christoph Sprenger, MIT (Copyright (c) 2021); the Cellphone Font by domsson is CC0; `hardware.inc` is an equates-only CC0 copy with no code bytes; author-attested hardware, repository test fixtures only, not installed or packaged",
     "age-rights-disclosure-missing"),
    ("rtc3test MBC3 real-time-clock ROM and `tests.md` | rtc3test release v004 at pinned commit `80ae792bf1b3c3387929b912e6df001af3511e24` (aaaaaa123456789), Unlicense; build-time RGBDS v0.4.2 only; hardware-derived, author-attested; repository test fixture only, not installed or packaged",
     "rtc3test-rights-disclosure-missing"),
    ("Mooneye DMG and CGB test ROMs (3 and 9) | Mooneye Test Suite revision `31510e12eea6286d36eea060a6adde755e1067aa` (Gekkio), MIT; headless-report derivatives with a zero-filled font replacement (see `FONT-LICENSE.txt` in each directory); WLA-DX is a GPL-2.0-or-later build tool that is not bundled or linked; repository test fixtures only, not installed or packaged",
     "mooneye-dmg-cgb-rights-disclosure-missing"),
    ("SameSuite CGB DMA and APU test ROMs (4 and 70) | SameSuite revision `f15645fb049a47ea235f6d2c9a033e72d8087901` (Lior Halphon), X11 licence; the build-time `hardware.inc` is CC0-1.0 and `hexdigits.2bpp` is covered by the repository X11 licence; RGBDS 1.0.1 is build-time only; repository test fixtures only, not installed or packaged",
     "samesuite-rights-missing"),
    ("X11", "samesuite-rights-missing"),
    ("MIT License in [`LICENSE`](LICENSE)", "root-license-missing"),
    ("not installed or packaged", "fixture-package-exclusion-missing"),
)
NOTICE_ROW = re.compile(
    r"^\| `(?P<name>[a-z0-9][a-z0-9-]*)` \| `(?P<manifest>[0-9a-f]{64})` "
    r"\| `(?P<notice>[0-9a-f]{64})` \|$",
    re.MULTILINE,
)
NOTICE_INLINE_DIGEST = re.compile(
    r"`(?P<path>fixtures/[A-Za-z0-9_./-]+)`: `(?P<digest>[0-9a-f]{64})`"
)
class ContractError(Exception):
    """A named failure in the adoption contract."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ContractError(reason)


def read_bounded(root: Path, relative: str, limit: int = MAX_DOCUMENT_BYTES) -> str:
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if resolved.stat().st_size > limit:
            raise ContractError(f"document-too-large:{relative}")
        raw = resolved.read_bytes()
    except ContractError:
        raise
    except (OSError, ValueError) as error:
        raise ContractError(f"document-unavailable:{relative}") from error
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ContractError(f"document-encoding-invalid:{relative}") from error
    if text.encode("utf-8", errors="strict") != raw:
        raise ContractError(f"document-utf8-byte-roundtrip-failed:{relative}")
    return text


# The ledger embeds the full historical corpus receipt, so it is larger.
DOCUMENT_LIMITS = {LEDGER: 8 * 1_048_576}


def write_lf(path: Path, text: str) -> None:
    """Write text with LF endings on every platform; the digest-bound documents are LF by attribute and
    Path.write_text would turn each newline into CRLF on Windows, which no row pattern or digest expects."""
    path.write_bytes(text.encode("utf-8"))


def read_document(root: Path, relative: str) -> str:
    return read_bounded(root, relative, DOCUMENT_LIMITS.get(relative, MAX_DOCUMENT_BYTES))


def prose(text: str, scope: str = "markdown", *, collapse: bool = True) -> str:
    """Whitespace-normalized body prose without comments or non-rendered Markdown."""
    text = mask_fenced_code_blocks(text)
    text = mask_indented_code_blocks(text)
    label_source = text
    text, comment_positions = protect_html_comments(text)
    text = mask_markdown_nonrendered(text, label_source=label_source)
    visible = list(mask_inline_code_spans(text))
    text_chars = list(text)
    for position, is_comment in enumerate(comment_positions):
        if is_comment and text_chars[position] not in ("\n", "\r"):
            text_chars[position] = " "
        if is_comment and visible[position] not in ("\n", "\r"):
            visible[position] = " "
    text = "".join(text_chars)
    visible = "".join(visible)
    require(RAW_HTML_CONSTRUCT.search(visible) is None, f"{scope}-raw-html-unsupported")
    require("\t" not in visible, f"{scope}-tab-unsupported")
    return " ".join(text.split()) if collapse else text


def protect_html_comments(text: str) -> tuple[str, bytearray]:
    """Keep comments opaque to Markdown parsing without joining their neighbors."""
    chars = list(text)
    comment_positions = bytearray(len(text))
    sentinel = "\ufdd0"
    search_from = 0
    while True:
        start = text.find("<!--", search_from)
        if start < 0:
            break
        closing = text.find("-->", start + 4)
        end = len(text) if closing < 0 else closing + 3
        line_start = start
        first_line = True
        while line_start < end:
            segment_start = start if first_line else line_start
            line_end = text.find("\n", segment_start, end)
            segment_end = end if line_end < 0 else line_end + 1
            for position in range(segment_start, segment_end):
                comment_positions[position] = 1
                chars[position] = text[position] if text[position] in "\r\n" else " "
            if segment_start < end and text[segment_start] not in "\r\n":
                chars[segment_start] = sentinel
            if line_end < 0:
                break
            line_start = line_end + 1
            first_line = False
        search_from = end
    return "".join(chars), comment_positions


def mask_markdown_nonrendered(text: str, *, label_source: str | None = None) -> str:
    """Mask link titles, image markup and reference definitions while preserving link labels."""
    if label_source is None:
        label_source = text
    require(len(label_source) == len(text), "markdown-label-source-length-mismatch")
    chars = list(text)
    label_chars = list(label_source)
    source_chars = list(mask_inline_code_spans(text))

    def blank(start: int, end: int) -> None:
        for offset in range(start, end):
            if chars[offset] not in ("\n", "\r"):
                chars[offset] = " "
                source_chars[offset] = " "

    escaped_positions = bytearray(len(source_chars))
    bracket_ends = array("i", [-1]) * len(source_chars)

    def escaped(position: int) -> bool:
        return escaped_positions[position] == 1

    def ascii_control(char: str) -> bool:
        codepoint = ord(char)
        return codepoint < 0x20 or codepoint == 0x7F

    def closing_bracket(opening: int) -> int | None:
        end = bracket_ends[opening]
        return None if end < 0 else end

    def skip_inline_whitespace(cursor: int) -> int | None:
        line_endings = 0
        while cursor < len(source_chars):
            char = source_chars[cursor]
            if char in " \t":
                cursor += 1
            elif char == "\r":
                line_endings += 1
                cursor += 2 if cursor + 1 < len(source_chars) and source_chars[cursor + 1] == "\n" else 1
            elif char == "\n":
                line_endings += 1
                cursor += 1
            else:
                break
            if line_endings > 1:
                return None
        return cursor

    def has_blank_line(start: int, end: int) -> bool:
        cursor = start
        while cursor < end:
            if source_chars[cursor] not in "\r\n":
                cursor += 1
                continue
            cursor += 2 if (source_chars[cursor] == "\r" and cursor + 1 < end
                            and source_chars[cursor + 1] == "\n") else 1
            while cursor < end and source_chars[cursor] in " \t":
                cursor += 1
            if cursor < end and source_chars[cursor] in "\r\n":
                return True
        return False

    def inline_link(opening: int) -> tuple[int, tuple[int, int] | None] | None:
        cursor = skip_inline_whitespace(opening + 1)
        if cursor is None:
            return None
        if cursor >= len(source_chars):
            return None
        if source_chars[cursor] == "<":
            cursor += 1
            while cursor < len(source_chars):
                char = source_chars[cursor]
                if char == "\\":
                    if (cursor + 1 >= len(source_chars)
                            or source_chars[cursor + 1] not in string.punctuation):
                        return None
                    cursor += 2
                elif char == ">":
                    cursor += 1
                    break
                elif char.isspace() or char == "<" or ascii_control(char):
                    return None
                else:
                    cursor += 1
            else:
                return None
        else:
            depth = 0
            while cursor < len(source_chars):
                char = source_chars[cursor]
                if ascii_control(char) and char not in "\t\r\n":
                    return None
                if char == "\\":
                    if (cursor + 1 >= len(source_chars)
                            or source_chars[cursor + 1] not in string.punctuation):
                        return None
                    cursor += 2
                    continue
                if char == "(":
                    depth += 1
                    if depth > 32:
                        return None
                elif char == ")":
                    if depth == 0:
                        return cursor + 1, None
                    depth -= 1
                elif char.isspace():
                    if depth == 0:
                        break
                    return None
                elif char in "<>":
                    return None
                cursor += 1

        separator_start = cursor
        cursor = skip_inline_whitespace(cursor)
        if cursor is None:
            return None
        if cursor >= len(source_chars):
            return None
        if source_chars[cursor] == ")":
            return cursor + 1, None
        if cursor == separator_start:
            return None
        if source_chars[cursor] in ('"', "'"):
            quote = source_chars[cursor]
            title_start = cursor + 1
            cursor = title_start
            while cursor < len(source_chars):
                if source_chars[cursor] == "\\":
                    if (cursor + 1 >= len(source_chars)
                            or source_chars[cursor + 1] not in string.punctuation):
                        return None
                    cursor += 2
                elif source_chars[cursor] == quote:
                    title_end = cursor
                    cursor += 1
                    break
                else:
                    cursor += 1
            else:
                return None
            title = (title_start, title_end)
        elif source_chars[cursor] == "(":
            title_start = cursor + 1
            cursor = title_start
            while cursor < len(source_chars):
                char = source_chars[cursor]
                if char == "\\":
                    if (cursor + 1 >= len(source_chars)
                            or source_chars[cursor + 1] not in string.punctuation):
                        return None
                    cursor += 2
                elif char == "(":
                    return None
                elif char == ")":
                    break
                else:
                    cursor += 1
            if cursor >= len(source_chars):
                return None
            title_end = cursor
            cursor += 1
            title = (title_start, title_end)
        else:
            return None
        if has_blank_line(title[0], title[1]):
            return None
        cursor = skip_inline_whitespace(cursor)
        if cursor is None:
            return None
        if cursor >= len(source_chars) or source_chars[cursor] != ")":
            return None
        return cursor + 1, title

    # Reference definitions are metadata, not body copy, even when no link uses them.
    reference_labels: set[str] = set()

    def normalize_reference_label(value: str) -> str:
        return re.sub(r"[ \t\r\n]+", " ", value.strip(" \t\r\n")).casefold()

    def container_content_start(
            line: str) -> tuple[int, int, tuple[int, ...], int] | None:
        cursor = 0
        visual_column = 0
        quote_depth = 0
        list_content_columns: list[int] = []
        while cursor < len(line):
            marker_column = visual_column
            while cursor < len(line) and line[cursor] in " \t":
                if line[cursor] == " ":
                    visual_column += 1
                else:
                    visual_column += 4 - visual_column % 4
                cursor += 1
                if visual_column - marker_column > 3:
                    return None
            if cursor < len(line) and line[cursor] == ">":
                quote_depth += 1
                cursor += 1
                visual_column += 1
                if cursor < len(line) and line[cursor] in " \t":
                    if line[cursor] == " ":
                        visual_column += 1
                    else:
                        visual_column += 4 - visual_column % 4
                    cursor += 1
                continue

            marker_end = cursor
            if cursor < len(line) and line[cursor] in "-+*":
                marker_end += 1
            else:
                digits_start = cursor
                while (marker_end < len(line) and line[marker_end] in "0123456789"
                       and marker_end - digits_start < 10):
                    marker_end += 1
                if (marker_end - digits_start > 9 or marker_end == digits_start
                        or marker_end >= len(line) or line[marker_end] not in ".)"):
                    marker_end = cursor
                else:
                    marker_end += 1
            if marker_end > cursor:
                marker_width = marker_end - cursor
                candidate_cursor = marker_end
                candidate_column = visual_column + marker_width
                whitespace_width = 0
                while candidate_cursor < len(line) and line[candidate_cursor] in " \t":
                    next_column = (candidate_column + 1 if line[candidate_cursor] == " " else
                                   candidate_column + 4 - candidate_column % 4)
                    if next_column - (visual_column + marker_width) > 4:
                        break
                    whitespace_width = next_column - (visual_column + marker_width)
                    candidate_column = next_column
                    candidate_cursor += 1
                if 1 <= whitespace_width <= 4:
                    cursor = candidate_cursor
                    visual_column = candidate_column
                    list_content_columns.append(visual_column)
                    continue
            return cursor, quote_depth, tuple(list_content_columns), visual_column
        return cursor, quote_depth, tuple(list_content_columns), visual_column

    def line_content_end(line: str) -> int:
        end = len(line)
        while end > 0 and line[end - 1] in "\r\n":
            end -= 1
        return end

    def reference_definition_label(
            line: str, raw_line: str) -> tuple[str, int, tuple[int, tuple[int, ...]]] | None:
        end = line_content_end(line)
        prefix = container_content_start(line)
        if prefix is None:
            return None
        cursor, quote_depth, list_content_columns, _visual_column = prefix
        if cursor >= end or line[cursor] != "[":
            return None
        start = cursor + 1
        cursor = start
        while cursor < end and cursor - start <= 999:
            char = line[cursor]
            if ascii_control(char):
                return None
            if char == "\\":
                if cursor + 1 >= end or line[cursor + 1] not in string.punctuation:
                    return None
                cursor += 2
            elif char == "[":
                return None
            elif char == "]":
                if cursor <= start or cursor + 1 >= end or line[cursor + 1] != ":":
                    return None
                label = raw_line[start:cursor]
                if not label.strip(" \t\r\n"):
                    return None
                cursor += 2
                break
            elif char in "\r\n":
                return None
            else:
                cursor += 1
        else:
            return None

        return label, cursor, (quote_depth, list_content_columns)

    def reference_destination(line: str, cursor: int, end: int) -> int | None:
        if line[cursor] == "<":
            cursor += 1
            while cursor < end:
                char = line[cursor]
                if ascii_control(char):
                    return None
                if char == "\\":
                    if cursor + 1 >= end or line[cursor + 1] not in string.punctuation:
                        return None
                    cursor += 2
                elif char == ">":
                    cursor += 1
                    break
                elif char.isspace() or char == "<":
                    return None
                else:
                    cursor += 1
            else:
                return None
        else:
            destination_start = cursor
            depth = 0
            while cursor < end and not line[cursor].isspace():
                char = line[cursor]
                if ascii_control(char):
                    return None
                if char == "\\":
                    if cursor + 1 >= end or line[cursor + 1] not in string.punctuation:
                        return None
                    cursor += 2
                elif char == "(":
                    depth += 1
                    if depth > 32:
                        return None
                    cursor += 1
                elif char == ")":
                    if depth == 0:
                        return None
                    depth -= 1
                    cursor += 1
                elif char in "<>":
                    return None
                else:
                    cursor += 1
            if cursor == destination_start or depth != 0:
                return None
        return cursor

    source = "".join(source_chars)
    line_spans: list[tuple[str, int, int]] = []
    offset = 0
    for line in source.splitlines(keepends=True):
        line_spans.append((line, offset, offset + len(line)))
        offset += len(line)

    def reference_title_context_matches(
            expected: tuple[int, tuple[int, ...]],
            actual: tuple[int, int, tuple[int, ...], int]) -> bool:
        _content_cursor, quote_depth, list_content_columns, content_column = actual
        expected_quote_depth, expected_list_columns = expected
        if quote_depth != expected_quote_depth or list_content_columns:
            return False
        if expected_list_columns:
            list_content_column = expected_list_columns[-1]
            return list_content_column <= content_column <= list_content_column + 3
        return True

    def reference_title_extent(
            line_index: int, cursor: int,
            expected_context: tuple[int, tuple[int, ...]]) -> tuple[int, int] | None:
        if cursor >= line_content_end(line_spans[line_index][0]):
            return None
        delimiter = line_spans[line_index][0][cursor]
        if delimiter not in ('"', "'", "("):
            return None
        cursor += 1
        while line_index < len(line_spans):
            line = line_spans[line_index][0]
            end = line_content_end(line)
            while cursor < end:
                char = line[cursor]
                if char == "\\":
                    if cursor + 1 >= end or line[cursor + 1] not in string.punctuation:
                        return None
                    cursor += 2
                elif (char == ")" if delimiter == "(" else char == delimiter):
                    if any(rest not in " \t" for rest in line[cursor + 1:end]):
                        return None
                    return line_index, cursor + 1
                elif delimiter == "(" and char == "(":
                    return None
                else:
                    cursor += 1
            line_index += 1
            if line_index >= len(line_spans):
                return None
            prefix = container_content_start(line_spans[line_index][0])
            if prefix is None or not reference_title_context_matches(expected_context, prefix):
                return None
            cursor = prefix[0]
            if cursor >= line_content_end(line_spans[line_index][0]):
                return None
        return None

    def reference_title_after_destination(
            line_index: int, destination_end: int,
            expected_context: tuple[int, tuple[int, ...]]) -> tuple[int, int] | None:
        line = line_spans[line_index][0]
        cursor = destination_end
        end = line_content_end(line)
        separator_start = cursor
        while cursor < end and line[cursor] in " \t":
            cursor += 1
        if cursor < end:
            if cursor == separator_start:
                return None
            return reference_title_extent(line_index, cursor, expected_context)
        next_index = line_index + 1
        if next_index >= len(line_spans):
            return None
        prefix = container_content_start(line_spans[next_index][0])
        if prefix is None or not reference_title_context_matches(expected_context, prefix):
            return None
        cursor = prefix[0]
        if cursor >= line_content_end(line_spans[next_index][0]):
            return None
        return reference_title_extent(next_index, cursor, expected_context)

    label_lines = label_source.splitlines(keepends=True)
    require(len(label_lines) == len(line_spans), "markdown-label-source-lines-mismatch")
    for index, (line, start, end) in enumerate(line_spans):
        parsed = reference_definition_label(line, label_lines[index])
        if parsed is None:
            continue
        label, cursor, container_context = parsed
        destination_line = index
        destination_source = line
        destination_source_end = line_content_end(line)
        while cursor < destination_source_end and destination_source[cursor] in " \t":
            cursor += 1
        if cursor >= destination_source_end:
            destination_line += 1
            if destination_line >= len(line_spans):
                continue
            prefix = container_content_start(line_spans[destination_line][0])
            if prefix is None or not reference_title_context_matches(container_context, prefix):
                continue
            cursor = prefix[0]
            destination_source = line_spans[destination_line][0]
            destination_source_end = line_content_end(destination_source)
            while cursor < destination_source_end and destination_source[cursor] in " \t":
                cursor += 1
        if cursor >= destination_source_end:
            continue
        destination_end = reference_destination(destination_source, cursor, destination_source_end)
        if destination_end is None:
            continue
        title_extent = reference_title_after_destination(
            destination_line, destination_end, container_context)
        if title_extent is None:
            tail = destination_source[destination_end:destination_source_end]
            if any(char not in " \t" for char in tail):
                continue
            final_end = line_spans[destination_line][2]
        else:
            title_line, _title_end = title_extent
            final_end = line_spans[title_line][2]
        reference_labels.add(normalize_reference_label(label))
        blank(start, final_end)

    def angle_autolink_end(opening: int) -> int | None:
        if source_chars[opening] != "<":
            return None
        cursor = opening + 1
        while cursor < len(source_chars):
            char = source_chars[cursor]
            if char == ">":
                inner = "".join(source_chars[opening + 1:cursor])
                scheme, separator, _target = inner.partition(":")
                if (separator and re.fullmatch(r"[A-Za-z][A-Za-z0-9.+-]{1,31}", scheme)
                        and all(not char.isspace() and not ascii_control(char)
                                and char not in "<>" for char in inner)):
                    return cursor + 1
                return None
            if char.isspace() or ascii_control(char) or char == "<":
                return None
            cursor += 1
        return None

    openings = array("I")
    backslashes = 0
    position = 0
    while position < len(source_chars):
        char = source_chars[position]
        if char == "\\":
            backslashes += 1
            position += 1
            continue
        is_escaped = backslashes % 2 == 1
        escaped_positions[position] = is_escaped
        backslashes = 0
        if is_escaped:
            position += 1
            continue
        if char == "<":
            autolink_end = angle_autolink_end(position)
            if autolink_end is not None:
                position = autolink_end
                continue
        if char == "[":
            openings.append(position)
        elif char == "]" and openings:
            bracket_ends[openings.pop()] = position
        position += 1

    # Mask image alt text before link labels so images nested in links cannot
    # contribute prose through their alt attribute.
    cursor = 0
    while cursor < len(source_chars):
        if (source_chars[cursor] != "!" or cursor + 1 >= len(source_chars)
                or source_chars[cursor + 1] != "[" or escaped(cursor)):
            cursor += 1
            continue
        opening = cursor + 1
        close = closing_bracket(opening)
        if close is None:
            cursor += 1
            continue
        following = close + 1
        if following < len(source_chars) and source_chars[following] == "(":
            parsed = inline_link(following)
            require(parsed is not None, "markdown-inline-link-malformed")
            end, _title = parsed
            blank(opening + 1, close)
            blank(following, end)
            cursor = end
            continue
        elif following < len(source_chars) and source_chars[following] == "[":
            reference_close = closing_bracket(following)
            if reference_close is not None:
                image_label = "".join(label_chars[opening + 1:close])
                reference_label = "".join(label_chars[following + 1:reference_close])
                target_label = image_label if reference_label == "" else reference_label
                if normalize_reference_label(target_label) in reference_labels:
                    blank(opening + 1, close)
                    blank(following, reference_close + 1)
                    cursor = reference_close + 1
                    continue
        elif normalize_reference_label("".join(label_chars[opening + 1:close])) in reference_labels:
            blank(opening + 1, close)
        cursor += 1

    cursor = 0
    while cursor < len(source_chars):
        if source_chars[cursor] != "[" or escaped(cursor):
            cursor += 1
            continue
        close = closing_bracket(cursor)
        if close is None:
            cursor += 1
            continue
        following = close + 1
        if following < len(source_chars) and source_chars[following] == "(":
            parsed = inline_link(following)
            require(parsed is not None, "markdown-inline-link-malformed")
            end, title = parsed
            if title is not None:
                blank(title[0], title[1])
            cursor = end
            continue
        elif following < len(source_chars) and source_chars[following] == "[":
            reference_close = closing_bracket(following)
            if reference_close is not None:
                link_text = "".join(label_chars[cursor + 1:close])
                reference_label = "".join(label_chars[following + 1:reference_close])
                target_label = link_text if reference_label == "" else reference_label
                if normalize_reference_label(target_label) in reference_labels:
                    blank(following, reference_close + 1)
                    cursor = reference_close + 1
                    continue
        cursor += 1

    return "".join(chars)


def mask_fenced_code_blocks(text: str) -> str:
    """Mask CommonMark fenced blocks, including blockquote containers."""
    output: list[str] = []
    tick = chr(96)
    fence_char: str | None = None
    fence_length = 0
    fence_containers: list[tuple[str, int]] = []
    comment_open = False

    def next_comment_state(content: str, is_open: bool, start: int = 0) -> bool:
        if not is_open:
            cursor = start
            spaces = 0
            while cursor < len(content) and content[cursor] == " " and spaces < 4:
                cursor += 1
                spaces += 1
            if spaces > 3 or not content.startswith("<!--", cursor):
                return False
            cursor += 4
        else:
            cursor = 0
        closing = content.find("-->", cursor)
        return closing < 0

    def parse_containers(content: str) -> tuple[list[tuple[str, int]], int]:
        containers: list[tuple[str, int]] = []
        list_marker = re.compile(r"([-+*]|[0-9]{1,9}[.)])([ ]{1,4})")
        position = 0
        while True:
            start = position
            spaces = 0
            while position < len(content) and content[position] == " " and spaces < 4:
                position += 1
                spaces += 1
            if spaces > 3:
                return containers, start
            if position < len(content) and content[position] == ">":
                containers.append(("quote", 0))
                position += 1
                if position < len(content) and content[position] in " \t":
                    position += 1
                continue
            marker = list_marker.match(content, position)
            if marker is not None:
                containers.append(("list", spaces + len(marker.group(1)) + len(marker.group(2))))
                position += len(marker.group(0))
                continue
            return containers, start

    def strip_containers(content: str, containers: list[tuple[str, int]]) -> tuple[bool, int]:
        position = 0
        for kind, indent in containers:
            if kind == "quote":
                start = position
                spaces = 0
                while position < len(content) and content[position] == " " and spaces < 4:
                    position += 1
                    spaces += 1
                if spaces > 3 or position >= len(content) or content[position] != ">":
                    return False, start
                position += 1
                if position < len(content) and content[position] in " \t":
                    position += 1
            else:
                remainder = position
                while remainder < len(content) and content[remainder] in " \t":
                    remainder += 1
                if remainder == len(content):
                    return True, remainder
                spaces = 0
                while position + spaces < len(content) and content[position + spaces] == " ":
                    spaces += 1
                if spaces < indent:
                    return False, position
                position += indent
        return True, position

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        ending = line[len(content):]
        if fence_char is not None:
            matched, position = strip_containers(content, fence_containers)
            if matched:
                candidate = content[position:]
                closing = re.match(r"^ {0,3}([" + re.escape(tick) + r"~]+)[ \t]*$", candidate)
                closes = (closing is not None and closing.group(1)[0] == fence_char
                          and len(closing.group(1)) >= fence_length
                          and all(char == fence_char for char in closing.group(1)))
                output.append(" " * len(content) + ending)
                if closes:
                    fence_char = None
                    fence_length = 0
                    fence_containers = []
                continue
            fence_char = None
            fence_length = 0
            fence_containers = []

        if comment_open:
            output.append(line)
            comment_open = next_comment_state(content, True)
            continue

        containers, position = parse_containers(content)
        candidate = content[position:]
        opening = re.match(r"^ {0,3}(" + re.escape(tick) + r"{3,}|~{3,})(.*)$", candidate)
        if opening and not (opening.group(1)[0] == tick and tick in opening.group(2)):
            fence_char = opening.group(1)[0]
            fence_length = len(opening.group(1))
            fence_containers = containers
            output.append(" " * len(content) + ending)
        else:
            output.append(line)
            comment_open = next_comment_state(content, False, position)
    return "".join(output)


def mask_indented_code_blocks(text: str) -> str:
    """Mask indented code after blockquote and list container markers."""
    output: list[str] = []
    list_marker = re.compile(r"([-+*]|[0-9]{1,9}[.)])([ ]+)")
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        ending = line[len(content):]
        position = 0
        while position < len(content):
            start = position
            spaces = 0
            while position < len(content) and content[position] == " " and spaces < 4:
                position += 1
                spaces += 1
            if spaces > 3:
                position = start
                break
            if position < len(content) and content[position] == ">":
                position += 1
                if position < len(content) and content[position] in " \t":
                    position += 1
                continue
            marker = list_marker.match(content, position)
            if marker is not None:
                marker_spaces = len(marker.group(2))
                position += len(marker.group(1)) + (1 if marker_spaces > 4 else marker_spaces)
                continue
            position = start
            break
        candidate = content[position:]
        if candidate.startswith("    ") or candidate.startswith("\t"):
            output.append(" " * len(content) + ending)
        else:
            output.append(line)
    return "".join(output)


def mask_inline_code_spans(text: str) -> str:
    """Mask CommonMark backtick spans, including multiline spans, without moving offsets."""
    chars = list(text)
    for opening, end, _content in inline_code_spans(text):
        for offset in range(opening, end):
            if chars[offset] not in ("\n", "\r"):
                chars[offset] = " "
    return "".join(chars)


def inline_code_spans(text: str) -> list[tuple[int, int, str]]:
    """Return the same bounded CommonMark backtick spans masked by mask_inline_code_spans."""
    tick = chr(96)
    runs: list[tuple[int, int, int, bool]] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] != tick:
            index += 1
            continue
        opening = index
        while index < length and text[index] == tick:
            index += 1
        delimiter = index - opening
        backslashes = 0
        cursor = opening - 1
        while cursor >= 0 and text[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        runs.append((opening, index, delimiter, backslashes % 2 == 1))

    next_same: list[int | None] = [None] * len(runs)
    next_by_length: dict[int, int] = {}
    for run_index in range(len(runs) - 1, -1, -1):
        delimiter = runs[run_index][2]
        next_same[run_index] = next_by_length.get(delimiter)
        next_by_length[delimiter] = run_index

    spans: list[tuple[int, int, str]] = []
    run_index = 0
    while run_index < len(runs):
        opening, content_start, _, escaped = runs[run_index]
        closing_index = next_same[run_index]
        if escaped or closing_index is None:
            run_index += 1
            continue
        closing_start = runs[closing_index][0]
        end = runs[closing_index][1]
        spans.append((opening, end, text[content_start:closing_start]))
        run_index = closing_index + 1
        while run_index < len(runs) and runs[run_index][0] < end:
            run_index += 1
    return spans


def normalized_code_span(content: str) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
    if content.startswith(" ") and content.endswith(" ") and content.strip():
        return content[1:-1]
    return content


def visible_phrase_source(text: str, phrase: str) -> str:
    """Mask inline code except exact code tokens explicitly required inside a visible phrase."""
    required_tokens = {
        normalized_code_span(content)
        for _opening, _end, content in inline_code_spans(phrase)
    }
    if not required_tokens:
        return mask_inline_code_spans(text)

    pieces: list[str] = []
    cursor = 0
    for opening, end, content in inline_code_spans(text):
        pieces.append(text[cursor:opening])
        token = normalized_code_span(content)
        if token in required_tokens:
            pieces.append(token)
        else:
            pieces.append("".join("\n" if char == "\n" else "\r" if char == "\r" else " "
                                  for char in text[opening:end]))
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def visible_phrase_text(phrase: str) -> str:
    """Render expected inline-code tokens as their visible text for prose matching."""
    pieces: list[str] = []
    cursor = 0
    for opening, end, content in inline_code_spans(phrase):
        pieces.append(phrase[cursor:opening])
        pieces.append(normalized_code_span(content))
        cursor = end
    pieces.append(phrase[cursor:])
    return "".join(pieces)

def comment_free(text: str) -> str:
    return re.sub(r"<!--.*?(?:-->|\Z)", " ", text, flags=re.DOTALL)


_CLAIMS_MODULE = None
_SUPPORT_LEDGER_MODULE = None
_V04_PROFILE_CACHE: dict[tuple[str, str], dict] = {}


def claims_module():
    """Load the production CGB claim parser that owns the claim markers."""
    global _CLAIMS_MODULE
    if _CLAIMS_MODULE is None:
        try:
            spec = importlib.util.spec_from_file_location(
                "verify_cgb_corpus_claims", CLAIMS_SCRIPT)
            require(spec is not None and spec.loader is not None,
                    "claims-parser-unavailable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except (OSError, SyntaxError) as error:
            raise ContractError("claims-parser-unavailable") from error
        _CLAIMS_MODULE = module
    return _CLAIMS_MODULE


def support_ledger_module():
    """Load the source-bound support-profile validator and release-copy renderer."""
    global _SUPPORT_LEDGER_MODULE
    if _SUPPORT_LEDGER_MODULE is None:
        try:
            spec = importlib.util.spec_from_file_location("verify_support_ledger", SUPPORT_LEDGER_SCRIPT)
            require(spec is not None and spec.loader is not None,
                    "support-ledger-validator-unavailable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except (OSError, SyntaxError) as error:
            raise ContractError("support-ledger-validator-unavailable") from error
        _SUPPORT_LEDGER_MODULE = module
    return _SUPPORT_LEDGER_MODULE


def v04_profile(repo: Path, rev: str) -> dict:
    """Reuse a profile only within this process, keyed by its immutable Git revision."""
    key = (str(repo.resolve(strict=True)), rev)
    if key not in _V04_PROFILE_CACHE:
        _V04_PROFILE_CACHE[key] = support_ledger_module().load_claims_version(repo, rev, "0.4.0")
    return _V04_PROFILE_CACHE[key]


def unnegated(pattern: re.Pattern[str], text: str) -> bool:
    """True when a match is not directly negated ("no ..." / "not ...")."""
    for match in pattern.finditer(text):
        if re.search(r"\b(?:no|not|never)\s*$", text[max(0, match.start() - 8):match.start()],
                     re.IGNORECASE) is None:
            return True
    return False


def check_unqualified(relative: str, text: str, *, game_claim_text: str | None = None) -> int:
    """Reject qualification claims that no shipped evidence supports."""
    text = mask_inline_code_spans(text)
    claims = claims_module()
    require(not unnegated(claims.UNQUALIFIED_CLAIM, text),
            f"unqualified-hardware-or-game-claim:{relative}")
    checks = (
        (claims.XFAIL_AS_PASS_CLAIM, "xfail-counted-as-pass"),
        (UNSUPPORTED_GAME_CLAIM, "unsupported-cgb-game-qualification"),
        (FALSE_SIGNING_CLAIM, "false-signing-or-notarization-claim"),
        (FALSE_PUBLICATION_CLAIM, "false-publication-claim"),
        (FALSE_PLATFORM_CLAIM, "false-platform-guarantee"),
        (FALSE_PERCEPTUAL_CLAIM, "false-perceptual-claim"),
        (FALSE_FUZZ_CLAIM, "false-fuzz-campaign-claim"),
    )
    for pattern, reason in checks:
        matched = (unsupported_game_claim_match(
            text if game_claim_text is None else game_claim_text)
                   if pattern is UNSUPPORTED_GAME_CLAIM else pattern.search(text))
        require(matched is None, f"{reason}:{relative}")
    return len(checks) + 1


def check_claim_boundaries(relative: str, text: str) -> int:
    text = mask_inline_code_spans(text)
    for pattern, reason in CLAIM_BOUNDARY_RULES:
        require(not unnegated(pattern, text), f"{reason}:{relative}")
    for (pattern, reason), twin in zip(CLAIM_BOUNDARY_RULES, CLAIM_BOUNDARY_TWINS):
        require(not unnegated(pattern, twin),
                f"scope-positive-control-rejected:{reason}:{relative}")
    return len(CLAIM_BOUNDARY_RULES) * 2


def check_phrases(relative: str, text: str,
                  required: tuple[tuple[str, str], ...]) -> int:
    for phrase, reason in required:
        evidence = visible_phrase_source(text, phrase)
        expected = flexible(visible_phrase_text(phrase))
        require(expected.search(evidence) is not None, f"{reason}:{relative}")
    return len(required)


def check_game(root: Path) -> int:
    raw = read_document(root, GAME_GUIDE)
    visible_text = prose(raw, collapse=False)
    game_claim_text = mask_inline_code_spans(visible_text)
    text = " ".join(visible_text.split())
    disclosure_text = mask_inline_code_spans(text)
    checks = 0

    require(ABSENCE_STATEMENT in disclosure_text,
            f"absence-statement-missing:{GAME_GUIDE}")
    checks += 1
    require(unsupported_game_claim_match(game_claim_text) is None,
            f"unsupported-cgb-game-qualification:{GAME_GUIDE}")
    checks += 1

    evidence = (
        ("`cc2966e1643d480d0780fb6cc5b9ef53d5ef6898`", "candidate-source-missing"),
        ("RGBDS v1.0.4", "rgbds-1.0.4-result-missing"),
        ("`2f6f13c6ec984313656c07b08d97dfcd3a471c7d3901d3ff486e5814bb503645`",
         "rgbds-1.0.1-archive-digest-missing"),
        ("494 assembler errors", "rgbds-1.0.1-build-failure-missing"),
        ("No output ROM or ROM digest was produced", "candidate-output-absence-missing"),
        ("asset rights remain unresolved", "candidate-rights-limit-missing"),
        ("`195765b8ca3b0fb7d37b7b92d0242d6c7e01ec71f27f93e565fa081e449cbb92`",
         "historical-candidate-digest-missing"),
        ("unverified historical metadata", "historical-candidate-status-missing"),
        ("Libbet and the Magic Floor v0.08 remains the DMG game acceptance",
         "dmg-game-acceptance-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("No physical or perceptual audio/color qualification is claimed",
         "perceptual-output-limit-missing"),
        ("[CGB corpus contract](cgb-corpus.md)", "cgb-corpus-evidence-link-missing"),
    )
    return checks + check_phrases(GAME_GUIDE, text, evidence)


def check_readme(root: Path) -> int:
    raw = read_document(root, README)
    visible_text = prose(raw, collapse=False)
    game_claim_text = mask_inline_code_spans(visible_text)
    text = " ".join(visible_text.split())
    disclosure_text = mask_inline_code_spans(text)
    checks = 0
    require(ABSENCE_STATEMENT in disclosure_text,
            f"absence-statement-missing:{README}")
    checks += 1
    require(unsupported_game_claim_match(game_claim_text) is None,
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
        require(expected in disclosure_text, f"{reason}:{README}")
        checks += 1
    return checks + check_claim_boundaries(README, disclosure_text)


def header_symbols(root: Path) -> set[str]:
    text = read_bounded(root, HEADER, MAX_SOURCE_BYTES)
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", " ", text)
    return set(SYMBOL_TOKEN.findall(text))


def check_symbols(root: Path) -> int:
    """Every `gbb_*`/`GBB_*` name in public prose must exist in the header."""
    declared = header_symbols(root)
    require(len(declared) > 50, f"header-symbol-inventory-short:{HEADER}")
    internal: dict[str, str] = {}
    for symbol, source in INTERNAL_SYMBOLS.items():
        source_text = comment_free(read_bounded(root, source, MAX_SOURCE_BYTES))
        require(re.search(rf"\b{symbol}\b", source_text) is not None,
                f"internal-symbol-source-missing:{symbol}:{source}")
        internal[symbol] = source
    resolved = 0
    for relative in PUBLIC_SURFACES:
        text = comment_free(read_document(root, relative))
        for token in sorted(set(SYMBOL_TOKEN.findall(text))):
            require(token in declared or token in internal,
                    f"undeclared-public-symbol:{relative}:{token}")
            resolved += 1
    require(resolved > 0, "symbol-inventory-empty")
    return resolved


def check_surface(root: Path, relative: str) -> int:
    raw = read_document(root, relative)
    visible_text = prose(raw, collapse=False)
    game_claim_text = mask_inline_code_spans(visible_text)
    text = " ".join(visible_text.split())
    disclosure_text = mask_inline_code_spans(text)
    checks = check_phrases(relative, text, REQUIRED[relative])
    checks += check_unqualified(relative, disclosure_text, game_claim_text=game_claim_text)
    if relative == UNRELEASED:
        require(PENDING_V030_SECTION.search(disclosure_text) is None,
                f"unreleased-pending-stale:{relative}")
        checks += 1
    if relative == RELEASE:
        require(not unnegated(FALSE_RETRY_TAMPER_CLAIM, disclosure_text),
                f"retry-tamper-overclaim:{relative}")
        checks += 1
        require(publication_claim_pattern("0.4.0").search(disclosure_text) is None,
                f"false-publication-claim:{relative}")
        checks += 1
    if relative == PREVIEW:
        checks += check_claim_boundaries(relative, text)
    return checks


def check_marked(root: Path) -> int:
    claims = claims_module()
    checks = 0
    for relative, sections in MARKED_SECTIONS.items():
        raw = read_document(root, relative)
        for key, required in sections:
            try:
                block = claims.marked_block(raw, key)
            except claims.ContractError as error:
                raise ContractError(f"{error}:{relative}") from error
            checks += check_phrases(relative, prose(block), required)
    return checks


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fixture_directories(root: Path) -> list[str]:
    base = root / "fixtures"
    try:
        names = sorted(path.name for path in base.iterdir()
                       if (path / "manifest.json").is_file())
    except OSError as error:
        raise ContractError("fixture-inventory-unavailable") from error
    require(names, "fixture-inventory-empty")
    return names


def check_notices(root: Path) -> int:
    raw = read_document(root, NOTICES)
    text = prose(raw)
    notice_text = prose(raw, collapse=False)
    checks = check_phrases(NOTICES, text, NOTICE_REQUIRED)
    require(REBOUND_ATTRIBUTION.search(mask_inline_code_spans(raw)) is None,
            f"rebound-attribution-present:{NOTICES}")
    checks += 1
    checks += check_unqualified(NOTICES, text)

    rows = {match["name"]: (match["manifest"], match["notice"])
            for match in visible_notice_matches(NOTICE_ROW, notice_text)}
    actual = fixture_directories(root)
    for name in actual:
        require(name in rows, f"notice-fixture-missing:{name}")
        manifest, notice = rows[name]
        directory = root / "fixtures" / name
        require(sha256_file(directory / "manifest.json") == manifest,
                f"notice-digest-stale:{name}:manifest")
        license_path = directory / "LICENSE.txt"
        require(license_path.is_file(), f"notice-license-file-missing:{name}")
        require(sha256_file(license_path) == notice,
                f"notice-digest-stale:{name}:notice")
        checks += 3
    for name in rows:
        require(name in actual, f"notice-fixture-unknown:{name}")
        checks += 1
    # The prose table digests are bound to bytes too, not only the digest table.
    for match in visible_notice_matches(NOTICE_INLINE_DIGEST, notice_text):
        target = root / match["path"]
        require(target.is_file(), f"notice-path-missing:{match['path']}")
        require(sha256_file(target) == match["digest"],
                f"notice-digest-stale:{match['path']}")
        checks += 1
    return checks


def visible_notice_matches(pattern: re.Pattern[str], text: str) -> list[re.Match[str]]:
    """Find notice rows and digests outside code spans, comments, and code blocks."""
    spans = inline_code_spans(text)
    return [match for match in pattern.finditer(text)
            if not any(opening <= match.start() and match.end() <= end
                       for opening, end, _content in spans)]


def perf_disclosure_bytes(root: Path, repo: Path | None = None, rev: str | None = None) -> bytes:
    if rev is not None:
        require(repo is not None, "release-notes-repository-missing")
        return immutable_blob(repo, rev, PERF_ATTRIBUTION)
    try:
        raw = (root / PERF_ATTRIBUTION).read_bytes()
    except OSError as error:
        raise ContractError("perf-attribution-receipt-unreadable") from error
    require(len(raw) <= 4 * MAX_DOCUMENT_BYTES, "perf-attribution-receipt-unreadable")
    return raw


def perf_disclosure_percent(root: Path, repo: Path | None = None, rev: str | None = None) -> str:
    """The head-versus-v0.2.0 instruction-count increase to disclose, one decimal: the maximum ratio over the
    three attribution ROMs and every repeat in the committed receipt (D-30, D-13)."""
    try:
        receipt = json.loads(perf_disclosure_bytes(root, repo, rev))
        by_revision = {row["revision"]: row["ir"] for row in receipt["measurements"]}
        base, head = by_revision[receipt["selection"]["v020"]], by_revision[receipt["selection"]["head"]]
        ratios = [Fraction(h, b) for rom in head for b, h in zip(base[rom], head[rom])]
    except (ContractError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise ContractError("perf-attribution-receipt-unreadable") from error
    require(bool(ratios), "perf-attribution-receipt-empty")
    return f"{float((max(ratios) - 1) * 100):.1f}"


def perf_disclosure_head(root: Path, repo: Path | None = None, rev: str | None = None) -> str:
    try:
        receipt = json.loads(perf_disclosure_bytes(root, repo, rev))
        head = receipt["selection"]["head"]
    except (ContractError, KeyError, TypeError, ValueError) as error:
        raise ContractError("perf-attribution-receipt-unreadable") from error
    require(type(head) is str and re.fullmatch(r"[0-9a-f]{40}", head) is not None,
            "perf-attribution-head-invalid")
    return head


def ledger_link_pattern(ledger: str) -> re.Pattern[str]:
    version = Path(ledger).name.removeprefix("v").removesuffix(".md")
    canonical = f"https://github.com/szTheory/gabbaboy/blob/v{version}/{ledger}"
    destination = r"(?:" + re.escape(ledger) + r"|" + re.escape(canonical) + r")"
    return re.compile(r"(?<![!\\])\[[^\]\n]*\]\(\s*" + destination + r"\s*\)")


def has_markdown_ledger_link(text: str, ledger: str, version: str) -> bool:
    """Find a real Markdown link with an exact supported ledger destination."""
    canonical = f"https://github.com/szTheory/gabbaboy/blob/v{version}/{ledger}"
    allowed = {ledger, canonical}

    escaped_chars = bytearray(len(text))
    bracket_ends = array("i", [-1]) * len(text)
    openings = array("I")
    backslashes = 0
    for index, char in enumerate(text):
        if char == "\\":
            backslashes += 1
            continue
        escaped_chars[index] = backslashes % 2 == 1
        backslashes = 0
        if escaped_chars[index]:
            continue
        if char == "[":
            openings.append(index)
        elif char == "]" and openings:
            bracket_ends[openings.pop()] = index

    def link_end(closing_bracket: int) -> tuple[str, int] | None:
        position = closing_bracket + 2
        while position < len(text) and text[position].isspace():
            position += 1
        if position >= len(text):
            return None

        if text[position] == "<":
            destination_start = position + 1
            position += 1
            while position < len(text):
                if text[position] == "\\":
                    position += 2
                    continue
                if text[position] == ">":
                    break
                position += 1
            if position >= len(text):
                return None
            destination = text[destination_start:position]
            position += 1
        else:
            destination_start = position
            nested = 0
            while position < len(text):
                char = text[position]
                if char == "\\":
                    position += 2
                    continue
                if char == "(":
                    nested += 1
                elif char == ")":
                    if nested == 0:
                        break
                    nested -= 1
                elif char.isspace() and nested == 0:
                    break
                position += 1
            destination = text[destination_start:position]

        while position < len(text) and text[position].isspace():
            position += 1
        if position < len(text) and text[position] != ")":
            quote = text[position]
            if quote not in "\"'(":
                return None
            closing = ")" if quote == "(" else quote
            title_depth = 1 if quote == "(" else 0
            position += 1
            while position < len(text):
                char = text[position]
                if char == "\\":
                    position += 2
                    continue
                if quote == "(" and char == "(":
                    title_depth += 1
                elif char == closing:
                    if quote != "(" or title_depth == 1:
                        break
                    title_depth -= 1
                position += 1
            if position >= len(text):
                return None
            position += 1
            while position < len(text) and text[position].isspace():
                position += 1
        if position >= len(text) or text[position] != ")":
            return None
        return destination, position + 1

    position = 0
    while position < len(text):
        if text[position] != "[" or escaped_chars[position]:
            position += 1
            continue
        closing_bracket = bracket_ends[position]
        if closing_bracket < 0:
            position += 1
            continue
        if closing_bracket + 1 >= len(text) or text[closing_bracket + 1] != "(":
            position += 1
            continue
        image = position > 0 and text[position - 1] == "!" and not escaped_chars[position - 1]
        parsed = link_end(closing_bracket)
        if parsed is None:
            return False
        destination, end = parsed
        if re.search(r"\n[ \t]*\n", text[position:end]):
            return False
        if not image and destination in allowed:
            return True
        position = end
    return False


def canonical_ledger_url(version: str) -> str:
    return f"https://github.com/szTheory/gabbaboy/blob/v{version}/docs/support/v{version}.md"


def check_v04_release_notes(text: str, raw: str, repo: Path, rev: str,
                            ledger: str, link_text: str) -> int:
    require(not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", raw),
            "release-notes-terminal-control-present")
    support = support_ledger_module()
    claims = v04_profile(repo, rev)
    rendered = support.render_release_notes_preface_v04(claims)
    checks = 0
    if ledger != "docs/support/v0.4.0.md":
        require(False, "release-notes-ledger-version-mismatch")
    require(has_markdown_ledger_link(link_text, ledger, "0.4.0"),
            "release-notes-ledger-version-mismatch")
    checks += 1
    require(ABSENCE_SENTENCE in text, "release-notes-absence-missing")
    checks += 1
    non_claim_reasons = (
        "release-notes-candidate-build-run-status-missing",
        "release-notes-cgb-admission-status-missing",
        "release-notes-license-prohibition-limit-missing",
    )
    for statement, reason in zip(claims["non_claims"], non_claim_reasons, strict=True):
        require(prose(statement) in text, reason)
        checks += 1

    outcomes = claims["candidate_outcomes"]
    known_reasons = [prose(row["reason"]) for row in outcomes]
    for row in outcomes:
        name = prose(row["name"])
        reason = prose(row["reason"])
        require(name in text, f"release-notes-candidate-name-missing:{row['candidate_id']}")
        line = prose(f"- **{row['name']}:** {row['reason']}")
        if line not in text:
            swapped = any(prose(f"- **{row['name']}:** {other}") in text
                          for other in (item for item in known_reasons if item != reason))
            if swapped:
                require(False, f"release-notes-candidate-reason-mismatch:{row['candidate_id']}")
            require(False, f"release-notes-candidate-source-reason-missing:{row['candidate_id']}")
        checks += 1

    harness = claims["harness"]
    harness_statement = prose(
        f"**Harness-only result:** {harness['model']} native-mode {', '.join(harness['observations'])} "
        f"results are {harness['result']}. {harness['interpretation']} This does not establish "
        f"{', '.join(harness['not_claimed'])}."
    )
    require(harness_statement in text, "release-notes-harness-game-conflation")
    checks += 1

    counts = claims["diagnostics"]["expected_counts"]
    diagnostic_statement = prose(
        "**Diagnostics:** Phase 22 is a synthetic composition tracer and metadata-only assessment: "
        f"{counts['named_entries']} named entries, {counts['unresolved_gates']} unresolved real-fixture gates, "
        f"{counts['real_fixtures_admitted']} real fixtures admitted, and "
        f"{counts['real_fixtures_executed']} real fixtures executed."
    )
    require(diagnostic_statement in text, "release-notes-diagnostic-count-mismatch")
    checks += 1
    pending = ", ".join(f"{row['id']} {row['status']}" for row in claims["requirements"]["statuses"])
    require(prose(f"Requirements remain Pending: {pending}.") in text,
            "release-notes-requirement-status-promoted")
    checks += 1
    completion = r"(?:complete(?:d)?|accepted|passed|fulfilled|closed|verified|resolved)"
    for row in claims["requirements"]["statuses"]:
        identifier = re.escape(row["id"])
        direct = re.compile(
            rf"\b{identifier}\b\s*(?:(?:is|are|was|were|has been|have been|now)\s+|[:=]\s*)?"
            rf"{completion}\b", re.IGNORECASE)
        reversed_status = re.compile(
            rf"\b{completion}\b\s*(?:status\s+(?:for|of)\s+)?{identifier}\b", re.IGNORECASE)
        require(direct.search(text) is None and reversed_status.search(text) is None,
                "release-notes-requirement-status-promoted")
        checks += 1
    for limitation in claims["limitations"]:
        require(prose(limitation) in text, "release-notes-support-limits-missing")
        checks += 1

    require(prose(rendered) in text, "release-notes-managed-preface-missing")
    checks += 1

    false_positive_claims = (
        (re.compile(r"\b(?:Potion Panic|µCity\s+1\.3)\b.{0,100}\b(?:was|were|has been|have been)\s+(?:built|run|executed|admitted)\b", re.I),
         "release-notes-candidate-claim-promoted"),
        (re.compile(r"\bCGB\s+game\b.{0,50}\b(?:was|has been)?\s*admitted\b", re.I),
         "release-notes-cgb-admission-promoted"),
        (re.compile(r"\bCGB\s+game-level\s+evidence\s+(?:exists?|was\s+observed|has\s+been\s+established)\b", re.I),
         "release-notes-cgb-evidence-promoted"),
        (re.compile(r"\b(?:sha-?256|digest|hash)\b.{0,80}\b(?:proves?|establishes?|confirms?)\b.{0,60}\b(?:fixture\s+)?admission\b|\b(?:fixture\s+)?admission\b.{0,60}\b(?:sha-?256|digest|hash)\b", re.I),
         "release-notes-digest-as-admission"),
        (re.compile(r"\bCGB-CPU-E\b.{0,100}\b(?:qualifies?|proves?|establishes?)\b.{0,50}\b(?:game|compatibility|physical)\b", re.I),
         "release-notes-harness-claim-promoted"),
        (re.compile(r"\bphysical\s+(?:DMG-CPU-B|CGB-CPU-E)\s+(?:hardware\s+)?(?:behavior|results?)\s+(?:is|are)\s+(?:qualified|verified|established)\b", re.I),
         "release-notes-hardware-claim-promoted"),
        (re.compile(r"\bCGB\s+mode[- ]3\s+timing\s+(?:is|has been)\s+(?:qualified|verified|established)\b", re.I),
         "release-notes-timing-claim-promoted"),
        (re.compile(r"\b(?:general|broad)\s+(?:CGB\s+)?game\s+compatibility\s+(?:is|has been)\s+(?:qualified|verified|established|complete)\b", re.I),
         "release-notes-compatibility-claim-promoted"),
        (re.compile(r"\b(?:\d+\s+)?(?:diagnostic|metadata)\s+(?:micro)?tests?\b.{0,100}\b(?:were|was|are|is|have\s+been|has\s+been)?\s*(?:executed|run|performed|passed|succeeded)\b", re.I),
         "release-notes-metadata-as-diagnostic"),
        (re.compile(r"\b(?:both\s+)?candidates?\b.{0,60}\blicen[cs]es\b.{0,80}\b(?:prohibit|forbid|ban|disallow|restrict)\w*\b.{0,100}\b(?:repository|public[- ]CI|redistribut\w*|use)\b", re.I),
         "release-notes-license-prohibition-unsupported"),
    )
    for pattern, reason in false_positive_claims:
        require(not unnegated(pattern, text), reason)
        checks += 1
    checks += 1
    return checks


def check_release_notes(path: Path, root: Path = DEFAULT_ROOT, rev: str | None = None,
                        repo: Path = DEFAULT_ROOT, version_override: str | None = None) -> int:
    try:
        resolved = path.resolve(strict=True)
        if resolved.stat().st_size > MAX_NOTES_BYTES:
            raise ContractError("release-notes-too-large")
        raw = resolved.read_text(encoding="utf-8")
    except ContractError:
        raise
    except (OSError, UnicodeError) as error:
        raise ContractError("release-notes-unavailable") from error
    visible = prose(raw, "release-notes", collapse=False)
    link_text = mask_inline_code_spans(visible)
    text = " ".join(link_text.split())
    require(text, "release-notes-empty")
    if rev is not None:
        subject_version, subject_ledger = identity_at_revision(repo, rev)
    else:
        subject_version, subject_ledger = tree_identity(root)
    version = version_override or subject_version
    ledger = ("docs/support/v" + version + ".md") if version_override is not None else subject_ledger
    require(re.fullmatch(r"\d+\.\d+\.\d+", version) is not None,
            "release-notes-version-invalid")
    version_token = re.compile(r"(?<![\w.])v?" + re.escape(version) + r"(?![\w.])")
    require(version_token.search(text) is not None,
            f"release-notes-version-missing:{version}")
    checks = 1
    if version == "0.4.0":
        require(re.fullmatch(r"[0-9a-f]{40}", rev or "") is not None,
                "release-notes-revision-required")
        checks += check_v04_release_notes(text, raw, repo, rev, ledger, link_text)
    else:
        require(ABSENCE_SENTENCE in text, "release-notes-absence-missing")
        checks += 1
        require(has_markdown_ledger_link(link_text, ledger, version),
                "release-notes-ledger-link-missing")
        checks += 1
    require(STATE_VERSION_SENTENCE in text, "release-notes-state-version-missing")
    checks += 1
    require(HOST_POSIX_SENTENCE in raw and HOST_POSIX_VISIBLE in text,
            "release-notes-host-posix-missing")
    checks += 1
    require(re.search(r"unsigned and not notarized", text, re.IGNORECASE) is not None,
            "release-notes-unsigned-limit-missing")
    checks += 1
    percent = perf_disclosure_percent(root, repo if rev is not None else None, rev)
    head = perf_disclosure_head(root, repo if rev is not None else None, rev)
    short_head = head[:12]
    if rev is not None:
        require(re.fullmatch(r"[0-9a-f]{40}", rev) is not None,
                "release-notes-revision-invalid")
    limitation_required = rev is None or head != rev
    require(re.search(r"(?<![\d.])\+" + re.escape(percent) + r"%", text) is not None and PERF_ATTRIBUTION in text,
            f"release-notes-perf-disclosure-missing:+{percent}%:{PERF_ATTRIBUTION}")
    checks += 1
    require(f"measured at {short_head}" in text,
            "release-notes-perf-head-mismatch")
    checks += 1
    limitation = PERF_HEAD_LIMITATION.replace("@HEAD@", short_head)
    limitation_marker = "The Ir attribution figure was measured at "
    if limitation_required:
        require(limitation in text,
                "release-notes-perf-head-limitation-missing")
        checks += 1
    elif limitation_marker in text:
        require(limitation in text, "release-notes-perf-head-mismatch")
        checks += 1
    publication_claim = publication_claim_pattern(version)
    require(publication_claim.search(text) is None,
            "release-notes-false-publication-claim")
    checks += 1
    checks += check_claim_boundaries("release-notes", text)
    claims = claims_module()
    for pattern, reason in (
        (UNSUPPORTED_GAME_CLAIM, "unsupported-cgb-game-qualification"),
        (FALSE_SIGNING_CLAIM, "false-signing-or-notarization-claim"),
        (FALSE_FUZZ_CLAIM, "false-fuzz-campaign-claim"),
        (FALSE_PLATFORM_CLAIM, "false-platform-guarantee"),
        (FALSE_PERCEPTUAL_CLAIM, "false-perceptual-claim"),
    ):
        matched = (unsupported_game_claim_match(link_text)
                   if pattern is UNSUPPORTED_GAME_CLAIM else pattern.search(text))
        require(matched is None, f"release-notes-{reason}")
        checks += 1
    require(not unnegated(claims.UNQUALIFIED_CLAIM, text),
            "release-notes-unqualified-hardware-or-game-claim")
    return checks + 1


def check_docs(root: Path) -> int:
    checks = check_game(root) + check_readme(root)
    for relative in REQUIRED:
        checks += check_surface(root, relative)
    checks += check_marked(root)
    checks += check_symbols(root)
    checks += check_notices(root)
    return checks


def run_cli(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *arguments],
        cwd=DEFAULT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def expect_pass(arguments: list[str]) -> None:
    result = run_cli(arguments)
    require(result.returncode == 0,
            "self-test-positive-check-failed:" + result.stderr.strip())
    try:
        summary = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ContractError("self-test-positive-summary-invalid") from error
    require(summary.get("positive_success") is True,
            "self-test-positive-summary-missing")
    require(summary.get("checks", 0) > 0, "self-test-positive-checks-empty")


def expect_reject(arguments: list[str], reason: str) -> None:
    result = run_cli(arguments)
    require(result.returncode != 0, f"negative-control-not-rejected:{reason}")
    require(reason in result.stderr,
            f"negative-control-wrong-reason:{reason}:{result.stderr.strip()}")


def child_result(root: Path, mode: str, reason: str | None = None) -> None:
    arguments = ["--check", mode, "--root", str(root)]
    if reason is None:
        expect_pass(arguments)
    else:
        expect_reject(arguments, reason)


def run_self_test_game(root: Path) -> tuple[int, int]:
    baseline = read_document(root, GAME_GUIDE)
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-game-") as temp:
        test_root = Path(temp)
        guide_path = test_root / GAME_GUIDE
        guide_path.parent.mkdir(parents=True, exist_ok=True)
        write_lf(guide_path, baseline)
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
            write_lf(guide_path, changed)
            child_result(test_root, "game", reason)
        write_lf(guide_path, baseline)
        child_result(test_root, "game")
    return 2, 2


def copy_inputs(root: Path, target: Path) -> None:
    """Copy exactly the bytes the docs checker reads into an isolated root."""
    relatives = set(PUBLIC_SURFACES) | {HEADER} | set(INTERNAL_SYMBOLS.values())
    for name in fixture_directories(root):
        relatives.add(f"fixtures/{name}/manifest.json")
        relatives.add(f"fixtures/{name}/LICENSE.txt")
    notice_text = prose(read_document(root, NOTICES), collapse=False)
    for match in visible_notice_matches(NOTICE_INLINE_DIGEST, notice_text):
        relatives.add(match["path"])
    for relative in sorted(relatives):
        source = root / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


VALID_RELEASE_NOTES_TEMPLATE = """\
## v@VERSION@

GabbaBoy v@VERSION@ adds the selected CGB-CPU-E software model beside DMG-CPU-B.

- @STATE_VERSION_SENTENCE@
- @HOST_POSIX_SENTENCE@
- No CGB game-level evidence exists. The CGB test-ROM corpus is software-model
  evidence, not game acceptance. Physical CGB-E remains UNKNOWN/POLICY.
- The macOS player archive is unsigned and not notarized.
- Support scope and known limits: [support ledger](@LEDGER_LINK@).
- Instruction count: +@PERCENT@% versus v0.2.0 (receipt: tests/baseline/perf-attribution-v1.json; measured at @HEAD@).
- @PERF_HEAD_LIMITATION@
"""


def run_self_test_release_notes(root: Path = DEFAULT_ROOT,
                                rev: str | None = None) -> tuple[int, int]:
    percent = perf_disclosure_percent(root)
    head = perf_disclosure_head(root)
    VALID_RELEASE_NOTES = (VALID_RELEASE_NOTES_TEMPLATE.replace("@VERSION@", RELEASE_VERSION)
                           .replace("@LEDGER_LINK@", canonical_ledger_url(RELEASE_VERSION))
                           .replace("@PERCENT@", percent)
                           .replace("@STATE_VERSION_SENTENCE@", STATE_VERSION_SENTENCE)
                           .replace("@HOST_POSIX_SENTENCE@", HOST_POSIX_SENTENCE)
                           .replace("@HEAD@", head[:12])
                           .replace("@PERF_HEAD_LIMITATION@",
                                    PERF_HEAD_LIMITATION.replace("@HEAD@", head[:12])))
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-notes-") as temp:
        notes = Path(temp) / "release-notes.md"
        write_lf(notes, VALID_RELEASE_NOTES)
        cli_args = ["--release-notes", str(notes), "--root", str(root)]
        if rev is not None:
            cli_args.extend(("--rev", rev))
        expect_pass(cli_args)
        mutations = (
            ("wrong-version", (RELEASE_VERSION, "0.1.0"),
             "release-notes-version-missing"),
            ("missing-absence", (ABSENCE_SENTENCE, ""),
             "release-notes-absence-missing"),
            ("missing-state-version", (STATE_VERSION_SENTENCE, ""),
             "release-notes-state-version-missing"),
            ("missing-host-posix", (HOST_POSIX_SENTENCE, ""),
             "release-notes-host-posix-missing"),
            ("comment-only-absence",
             (ABSENCE_SENTENCE, f"<!-- {ABSENCE_SENTENCE} -->"),
             "release-notes-absence-missing"),
            ("missing-ledger-link",
             (f"({canonical_ledger_url(RELEASE_VERSION)})",
              "(https://github.com/szTheory/gabbaboy/blob/v0.1.0/docs/support/v0.1.0.md)"),
             "release-notes-ledger-link-missing"),
            ("missing-unsigned-limit", ("unsigned and not notarized", "ready"),
             "release-notes-unsigned-limit-missing"),
            ("stale-perf-percentage", (f"+{percent}%", "+8.3%"),
             "release-notes-perf-disclosure-missing"),
            ("missing-perf-receipt-path", (PERF_ATTRIBUTION, "the receipt"),
             "release-notes-perf-disclosure-missing"),
            ("wrong-perf-head", (f"measured at {head[:12]}", "measured at 711f4fd"),
             "release-notes-perf-head-mismatch"),
            ("missing-perf-head-limitation",
             (PERF_HEAD_LIMITATION.replace("@HEAD@", head[:12]), ""),
             "release-notes-perf-head-limitation-missing"),
            ("wrong-perf-head-limitation",
             (PERF_HEAD_LIMITATION.replace("@HEAD@", head[:12]),
              PERF_HEAD_LIMITATION.replace("@HEAD@", "711f4fd")),
             "release-notes-perf-head-limitation-missing"),
            ("comment-only-perf-disclosure",
             (f"- Instruction count: +{percent}% versus v0.2.0 (receipt: {PERF_ATTRIBUTION}; measured at {head[:12]}).",
              f"<!-- Instruction count: +{percent}% ({PERF_ATTRIBUTION}) -->"),
             "release-notes-perf-disclosure-missing"),
            ("contrary-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification"),
            ("zero-width-space-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification"),
            ("word-joiner-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification"),
            ("zero-width-non-joiner-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification"),
            ("false-signing-claim", None,
             "release-notes-false-signing-or-notarization-claim"),
            ("false-publication-claim", None,
             "release-notes-false-publication-claim"),
            ("cross-version-state-claim", None,
             "false-cross-version-state-claim:release-notes"),
            ("durability-claim", None,
             "false-durability-claim:release-notes"),
            ("windows-host-claim", None,
             "false-windows-host-claim:release-notes"),
            ("unscoped-state-claim", None,
             "unscoped-state-claim:release-notes"),
        )
        mutations += tuple(
            (f"default-ignorable-{name}-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification")
            for name, _ in DEFAULT_IGNORABLE_CLAIM_SEPARATORS
        )
        mutations += tuple(
            (f"commonmark-reference-{name}-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification")
            for name, _ in COMMONMARK_REFERENCED_GAME_CLAIMS
        )
        mutations += tuple(
            (f"commonmark-hard-break-{name}-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification")
            for name, _ in COMMONMARK_HARD_BREAK_GAME_CLAIMS
        )
        for safe_suffix in (
                "\nCGB&#x20; test-ROM results remain software-model evidence only.\n",
                "\n`CGB&#x200b; game passes all acceptance checks.`\n",
                "\nCGB\\\ntest-ROM results remain software-model evidence only.\n",
                "\n`CGB\\\ngame passes all acceptance checks.`\n"):
            write_lf(notes, VALID_RELEASE_NOTES + safe_suffix)
            expect_pass(cli_args)
        write_lf(notes, VALID_RELEASE_NOTES)
        for name, edit, reason in mutations:
            if name == "contrary-game-claim":
                changed = VALID_RELEASE_NOTES + "\nCGB game passes acceptance.\n"
            elif name in ("zero-width-space-game-claim", "word-joiner-game-claim",
                          "zero-width-non-joiner-game-claim"):
                separator = {
                    "zero-width-space-game-claim": "\u200b",
                    "word-joiner-game-claim": "\u2060",
                    "zero-width-non-joiner-game-claim": "\u200c",
                }[name]
                changed = VALID_RELEASE_NOTES + "\nCGB" + separator + " game passes acceptance.\n"
            elif name.startswith("default-ignorable-"):
                separator_name = name.removeprefix("default-ignorable-").removesuffix(
                    "-game-claim")
                separator = dict(DEFAULT_IGNORABLE_CLAIM_SEPARATORS)[separator_name]
                changed = VALID_RELEASE_NOTES + "\nCGB" + separator + " game passes acceptance.\n"
            elif name.startswith("commonmark-reference-"):
                claim_name = name.removeprefix("commonmark-reference-").removesuffix(
                    "-game-claim")
                claim = dict(COMMONMARK_REFERENCED_GAME_CLAIMS)[claim_name]
                changed = VALID_RELEASE_NOTES + "\n" + claim + "\n"
            elif name.startswith("commonmark-hard-break-"):
                claim_name = name.removeprefix("commonmark-hard-break-").removesuffix(
                    "-game-claim")
                claim = dict(COMMONMARK_HARD_BREAK_GAME_CLAIMS)[claim_name]
                changed = VALID_RELEASE_NOTES + "\n" + claim + "\n"
            elif name == "false-signing-claim":
                changed = VALID_RELEASE_NOTES + "\nThe player is signed and notarized.\n"
            elif name == "false-publication-claim":
                changed = VALID_RELEASE_NOTES + f"\n{RELEASE_VERSION} has been released.\n"
            elif name == "cross-version-state-claim":
                changed = VALID_RELEASE_NOTES + "\nSave states load across GabbaBoy versions.\n"
            elif name == "durability-claim":
                changed = VALID_RELEASE_NOTES + "\nSaves are power-loss safe.\n"
            elif name == "windows-host-claim":
                changed = VALID_RELEASE_NOTES + "\nHost mode runs on Windows.\n"
            elif name == "unscoped-state-claim":
                changed = VALID_RELEASE_NOTES + "\nGabbaBoy supports save states on every platform.\n"
            else:
                changed = VALID_RELEASE_NOTES.replace(edit[0], edit[1])
            require(changed != VALID_RELEASE_NOTES,
                    f"self-test-mutation-no-op:{name}")
            write_lf(notes, changed)
            cli_args = ["--release-notes", str(notes), "--root", str(root)]
            if rev is not None:
                cli_args.extend(("--rev", rev))
            expect_reject(cli_args, reason)
        write_lf(notes, VALID_RELEASE_NOTES)
        cli_args = ["--release-notes", str(notes), "--root", str(root)]
        if rev is not None:
            cli_args.extend(("--rev", rev))
        expect_pass(cli_args)
    return len(mutations), len(mutations)


def run_self_test_release_notes_v04(root: Path = DEFAULT_ROOT) -> tuple[int, int]:
    """Prove that the existing release-notes gate rejects an omitted v0.4 fact."""
    global RAW_HTML_CONSTRUCT
    rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                  stderr=subprocess.DEVNULL, text=True).strip()
    support = support_ledger_module()
    profile = v04_profile(root, rev)
    percent = perf_disclosure_percent(root, root, rev)
    head = perf_disclosure_head(root, root, rev)
    base = (VALID_RELEASE_NOTES_TEMPLATE.replace("@VERSION@", "0.4.0")
            .replace("@LEDGER_LINK@", canonical_ledger_url("0.4.0"))
            .replace("@PERCENT@", percent)
            .replace("@STATE_VERSION_SENTENCE@", STATE_VERSION_SENTENCE)
            .replace("@HOST_POSIX_SENTENCE@", HOST_POSIX_SENTENCE)
            .replace("@HEAD@", head[:12])
            .replace("@PERF_HEAD_LIMITATION@",
                     PERF_HEAD_LIMITATION.replace("@HEAD@", head[:12])))
    valid = base
    valid += "\n" + support.render_release_notes_preface_v04(profile)
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v04-notes-") as temp:
        notes = Path(temp) / "release-notes.md"
        controls = 0
        def accepts(value: str) -> None:
            write_lf(notes, value)
            try:
                checks = check_release_notes(notes, root, rev, root, "0.4.0")
            except ContractError as error:
                raise ContractError(f"release-notes-v04-positive-refused:{error}") from error
            require(checks > 0, "release-notes-v04-positive-checks-empty")

        def reject(name: str, changed: str, reason: str) -> None:
            nonlocal controls
            require(changed != valid, f"self-test-mutation-no-op:{name}")
            accepts(valid)
            write_lf(notes, changed)
            try:
                check_release_notes(notes, root, rev, root, "0.4.0")
            except ContractError as error:
                require(reason in str(error),
                        f"release-notes-v04-control-wrong-reason:{name}:{error}")
            else:
                raise ContractError(f"negative-control-not-rejected:{name}:{reason}")
            controls += 1

        def replace_ledger_targets(destination: str) -> str:
            pattern = ledger_link_pattern("docs/support/v0.4.0.md")
            return pattern.sub(
                lambda match: match.group(0).split("](", 1)[0] + f"]({destination})",
                valid,
            )

        def replace_ledger_construct(replacement: str) -> str:
            pattern = ledger_link_pattern("docs/support/v0.4.0.md")
            return pattern.sub(lambda _match: replacement, valid)

        def image_ledger_links() -> str:
            pattern = ledger_link_pattern("docs/support/v0.4.0.md")
            return pattern.sub(lambda match: "!" + match.group(0), valid)

        incomplete_html_openers = (
            ("script-newline", "<script\n"),
            ("script-space-newline", "<script \n"),
            ("pre-newline", "<pre\n"),
            ("pre-space-newline", "<pre \n"),
            ("style-newline", "<style\n"),
            ("style-space-newline", "<style \n"),
            ("script-mixed-case", "<ScRiPt\n"),
            ("doctype-html", "<!DOCTYPE html\n"),
            ("xml-processing-instruction", '<?xml version="1.0"\n'),
        )

        accepts(valid)
        accepts(valid + "\n```html\n<div hidden>sample</div>\n\t[ledger](docs/support/v0.4.0.md)\n```\n")
        accepts(valid + "\n<!-- <script\n -->\n\n```html\n<pre \n```\n\n    <style\n\n`<!DOCTYPE html` `<?xml version=\"1.0\"`\n")
        accepts(valid + "\n\\<script\n<scripture\n")
        with tempfile.TemporaryDirectory(prefix="gabbaboy-release-revision-identity-") as temp:
            other_tree = Path(temp)
            cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")
            cmake = cmake.replace(f"VERSION {RELEASE_VERSION} LANGUAGES", "VERSION 0.4.0 LANGUAGES", 1)
            (other_tree / "CMakeLists.txt").write_text(cmake, encoding="utf-8")
            manifest = json.loads((root / ".release-please-manifest.json").read_text(encoding="utf-8"))
            manifest["."] = "0.4.0"
            (other_tree / ".release-please-manifest.json").write_text(
                json.dumps(manifest) + "\n", encoding="utf-8")
            (other_tree / "docs/support").mkdir(parents=True)
            (other_tree / "docs/support/v0.4.0.md").touch()
            legacy_notes = other_tree / "legacy-release-notes.md"
            legacy_base = (VALID_RELEASE_NOTES_TEMPLATE.replace("@VERSION@", RELEASE_VERSION)
                           .replace("@LEDGER_LINK@", canonical_ledger_url(RELEASE_VERSION))
                           .replace("@PERCENT@", percent)
                           .replace("@STATE_VERSION_SENTENCE@", STATE_VERSION_SENTENCE)
                           .replace("@HOST_POSIX_SENTENCE@", HOST_POSIX_SENTENCE)
                           .replace("@HEAD@", head[:12])
                           .replace("@PERF_HEAD_LIMITATION@",
                                    PERF_HEAD_LIMITATION.replace("@HEAD@", head[:12])))
            write_lf(legacy_notes, legacy_base)
            require(check_release_notes(legacy_notes, other_tree, rev, root) > 0,
                    "release-notes-revision-identity-not-pinned")
        potion, ucity = profile["candidate_outcomes"]
        p_line = f"- **{potion['name']}:** {potion['reason']}"
        u_line = f"- **{ucity['name']}:** {ucity['reason']}"
        p_swapped = p_line.replace(potion["reason"], ucity["reason"])
        u_swapped = u_line.replace(ucity["reason"], potion["reason"])
        reject("candidate-reason-omission", valid.replace(p_line, f"- **{potion['name']}:** source review stopped."),
               "release-notes-candidate-source-reason-missing")
        reject("candidate-reasons-swapped", valid.replace(p_line, p_swapped).replace(u_line, u_swapped),
               "release-notes-candidate-reason-mismatch")
        reject("candidate-built-after-negative",
               valid + "\nPotion Panic was built and run after the source review.\n",
               "release-notes-candidate-claim-promoted")
        reject("game-admitted-after-negative",
               valid + "\nOne CGB game was admitted after the Phase 21 review.\n",
               "release-notes-cgb-admission-promoted")
        reject("game-evidence-after-negative",
               valid + "\nCGB game-level evidence exists for this release.\n",
               "release-notes-cgb-evidence-promoted")
        reject("candidate-status-omission",
               valid.replace(profile["non_claims"][0], "Candidate build and run status is unstated."),
               "release-notes-candidate-build-run-status-missing")
        reject("game-admission-omission",
               valid.replace(profile["non_claims"][1], "Game admission status is unstated."),
               "release-notes-cgb-admission-status-missing")
        reject("harness-game-conflation", valid + "\nCGB-CPU-E qualifies game progress.\n",
               "release-notes-harness-claim-promoted")
        reject("diagnostic-count-mismatch", valid.replace("513 named entries", "512 named entries"),
               "release-notes-diagnostic-count-mismatch")
        reject("pending-status-promoted", valid.replace("DIAG-01 Pending", "DIAG-01 Complete"),
               "release-notes-requirement-status-promoted")
        reject("contradictory-pending-status",
               valid + "\nDIAG-01 is complete.\n",
               "release-notes-requirement-status-promoted")
        reject("metadata-presented-as-diagnostic-results",
               valid + "\nAll 513 diagnostic microtests were executed and passed.\n",
               "release-notes-metadata-as-diagnostic")
        reject("rights-scope-presented-as-license-prohibition",
               valid + "\nBoth candidates' licenses prohibit repository and public-CI use.\n",
               "release-notes-license-prohibition-unsupported")
        reject("missing-hardware-limit",
               valid.replace(profile["limitations"][0], "Physical hardware status is unstated."),
               "release-notes-support-limits-missing")
        reject("html-comment-hides-reason", valid.replace(p_line, f"<!-- {p_line} -->"),
               "release-notes-candidate-name-missing")
        reject("unclosed-html-comment-hides-following-clauses",
               valid.replace(p_line, f"<!--\n{p_line}"),
               "release-notes-candidate-build-run-status-missing")
        marker = chr(96) * 3
        quoted_fence = f"> {marker}text\n> {p_line}\n> {marker}"
        reject("blockquote-fenced-code-hides-reason", valid.replace(p_line, quoted_fence),
               "release-notes-candidate-name-missing")
        list_fence = f"- code:\n  {marker}text\n  {p_line}\n  {marker}"
        reject("list-fenced-code-hides-reason", valid.replace(p_line, list_fence),
               "release-notes-candidate-name-missing")
        same_line_list_fence = f"- {marker}text\n  {p_line}\n  {marker}"
        reject("same-line-list-fence-hides-reason",
               valid.replace(p_line, same_line_list_fence),
               "release-notes-candidate-name-missing")
        list_quote_fence = f"- > {marker}text\n  > {p_line}\n  > {marker}"
        reject("list-blockquote-fence-hides-reason",
               valid.replace(p_line, list_quote_fence),
               "release-notes-candidate-name-missing")
        quote_list_fence = f"> - {marker}text\n>   {p_line}\n>   {marker}"
        reject("blockquote-list-fence-hides-reason",
               valid.replace(p_line, quote_list_fence),
               "release-notes-candidate-name-missing")
        reject("blockquote-indented-code-hides-reason",
               valid.replace(p_line, ">     " + p_line),
               "release-notes-candidate-name-missing")
        reject("blockquote-list-indented-code-hides-reason",
               valid.replace(p_line, "> -     " + p_line),
               "release-notes-candidate-name-missing")
        reject("list-blockquote-indented-code-hides-reason",
               valid.replace(p_line, "- >     " + p_line),
               "release-notes-candidate-name-missing")
        reject("fenced-code-hides-reason", valid.replace(p_line, f"```text\n{p_line}\n```"),
               "release-notes-candidate-name-missing")
        tick = chr(96)
        reject("inline-code-hides-reason", valid.replace(p_line, f"{tick}{p_line}{tick}"),
               "release-notes-candidate-name-missing")
        reject("inline-code-hides-host-limit", valid.replace(
            HOST_POSIX_SENTENCE, f"{tick}{HOST_POSIX_SENTENCE}{tick}"),
            "release-notes-host-posix-missing")
        indented = "\n".join(("    " + line if line else "") for line in valid.splitlines())
        reject("indented-code-hides-entire-preface", indented, "release-notes-empty")
        inline = "\n".join((f"{tick}{line}{tick}" if line else "") for line in valid.splitlines())
        reject("inline-code-hides-entire-preface", inline,
               "release-notes-version-missing:0.4.0")
        image_link = image_ledger_links()
        require(image_link != valid, "release-notes-self-test-link-anchor-missing")
        reject("image-is-not-a-ledger-link", image_link, "release-notes-ledger-version-mismatch")
        external_link = replace_ledger_targets("https://evil.invalid/?next=docs/support/v0.4.0.md")
        require(external_link != valid, "release-notes-self-test-external-link-anchor-missing")
        reject("external-query-is-not-a-ledger-link", external_link,
               "release-notes-ledger-version-mismatch")
        title_link = replace_ledger_targets("https://evil.invalid/ \"docs/support/v0.4.0.md\"")
        reject("ledger-path-in-link-title-is-not-a-link", title_link,
               "release-notes-ledger-version-mismatch")
        nested_title_link = replace_ledger_construct(
            '[outer](https://evil.invalid/ "[ledger](docs/support/v0.4.0.md)")')
        reject("nested-ledger-link-in-external-title-is-not-a-link", nested_title_link,
               "release-notes-ledger-version-mismatch")
        whitespace_link = replace_ledger_construct("[ledger] (docs/support/v0.4.0.md)")
        reject("whitespace-before-link-destination-is-not-a-link", whitespace_link,
               "release-notes-ledger-version-mismatch")
        newline_link = replace_ledger_construct("[ledger]\n(docs/support/v0.4.0.md)")
        reject("newline-before-link-destination-is-not-a-link", newline_link,
               "release-notes-ledger-version-mismatch")
        blank_label_link = replace_ledger_construct("[ledger\n\n](docs/support/v0.4.0.md)")
        reject("blank-line-in-link-label-is-not-a-link", blank_label_link,
               "release-notes-ledger-version-mismatch")
        blank_title_link = replace_ledger_construct(
            "[ledger](docs/support/v0.4.0.md\n\n\"title\")")
        reject("blank-line-in-link-title-is-not-a-link", blank_title_link,
               "markdown-inline-link-malformed")
        unmatched_brackets = replace_ledger_construct("[" * 5000)
        reject("unmatched-brackets-do-not-create-a-link", unmatched_brackets,
               "release-notes-ledger-version-mismatch")
        tab_indented_link = replace_ledger_construct("-\t    [ledger](docs/support/v0.4.0.md)")
        reject("tab-indented-list-code-is-not-a-ledger-link", tab_indented_link,
               "release-notes-tab-unsupported")
        reject("raw-html-pre-rejected",
               replace_ledger_construct("<pre>[ledger](docs/support/v0.4.0.md)</pre>"),
               "release-notes-raw-html-unsupported")
        reject("hidden-html-div-rejected",
               replace_ledger_construct('<div hidden>[ledger](docs/support/v0.4.0.md)</div>'),
               "release-notes-raw-html-unsupported")
        reject("hidden-html-link-attribute-rejected",
               replace_ledger_construct(
                   '<span hidden title="[ledger](docs/support/v0.4.0.md)">notes</span>'),
               "release-notes-raw-html-unsupported")
        reject("html-declaration-rejected",
               replace_ledger_construct('<!DOCTYPE html>[ledger](docs/support/v0.4.0.md)'),
               "release-notes-raw-html-unsupported")
        reject("html-processing-instruction-rejected",
               replace_ledger_construct('<?xml version="1.0"?>[ledger](docs/support/v0.4.0.md)'),
               "release-notes-raw-html-unsupported")
        reject("html-cdata-rejected",
               replace_ledger_construct('<![CDATA[[ledger](docs/support/v0.4.0.md)]]>'),
               "release-notes-raw-html-unsupported")
        legacy_reproducer = "<script\n" + valid
        legacy_raw_html_construct = re.compile(
            r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s[^<>]*)?\s*/?>|<![A-Z][^>]*>|"
            r"<\?[A-Za-z][^>]*\?>|<!\[CDATA\[", re.DOTALL | re.IGNORECASE)
        current_raw_html_construct = RAW_HTML_CONSTRUCT
        try:
            RAW_HTML_CONSTRUCT = legacy_raw_html_construct
            write_lf(notes, legacy_reproducer)
            try:
                require(check_release_notes(notes, root, rev, root, "0.4.0") > 0,
                        "legacy-incomplete-html-raw-html-causal-checks-empty")
            except ContractError as error:
                raise ContractError(f"legacy-incomplete-html-raw-html-causal-reproducer-rejected:{error}") from error
        finally:
            RAW_HTML_CONSTRUCT = current_raw_html_construct
        for opener_name, opener in incomplete_html_openers:
            reject(f"incomplete-{opener_name}-hides-release-notes", opener + valid,
                   "release-notes-raw-html-unsupported")
            reject(f"incomplete-{opener_name}-hides-ledger-link",
                   replace_ledger_construct(opener + "[ledger](docs/support/v0.4.0.md)"),
                   "release-notes-raw-html-unsupported")
        malformed_link = replace_ledger_targets("not a valid destination docs/support/v0.4.0.md")
        reject("malformed-destination-is-not-a-ledger-link", malformed_link,
               "markdown-inline-link-malformed")
        reject("terminal-control-hides-reason", valid.replace("Potion Panic", "Potion \x1b[2KPanic", 1),
               "release-notes-terminal-control-present")
        reject("wrong-version-ledger-link", valid.replace(
            "docs/support/v0.4.0.md", "docs/support/v0.3.0.md"),
               "release-notes-ledger-version-mismatch")
        reject("digest-does-not-prove-admission", valid +
               "\nThe SHA-256 digest proves fixture admission.\n",
               "release-notes-digest-as-admission")
        reject("signed-artifact-promotion", valid + "\nRelease artifacts are signed.\n",
               "release-notes-false-signing-or-notarization-claim")
        reject("notarized-artifact-promotion", valid + "\nRelease artifacts are notarized.\n",
               "release-notes-false-signing-or-notarization-claim")
        reject("false-publication-claim", valid + "\nv0.4.0 has been published.\n",
               "release-notes-false-publication-claim")
        reject("all-platform-promotion", valid + "\nGabbaBoy supports all platforms.\n",
               "release-notes-false-platform-guarantee")
        reject("perceptual-qualification", valid + "\nPerceptual audio is verified.\n",
               "release-notes-false-perceptual-claim")
        return 2, controls


def immutable_blob(repo: Path, rev: str, relative: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{relative}"],
                            capture_output=True, check=False, env=git_environment())
    require(result.returncode == 0, f"revision-input-missing:{relative}")
    require(len(result.stdout) <= MAX_DOCUMENT_BYTES * 4,
            f"revision-input-too-large:{relative}")
    return result.stdout


def run_self_test_claim_boundaries(repo: Path, rev: str) -> tuple[int, int]:
    require(re.fullmatch(r"[0-9a-f]{40}", rev) is not None,
            "revision-invalid:full-commit-id-required")
    resolved = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{rev}^{{commit}}"],
                              capture_output=True, check=False, env=git_environment())
    require(resolved.returncode == 0, "revision-invalid:commit-not-found")
    # Bind the version and ledger identity used for generated release notes to the same commit.
    with tempfile.TemporaryDirectory(prefix="gabbaboy-claims-rev-") as temp:
        snapshot = Path(temp).resolve(strict=True)
        (snapshot / "docs/support").mkdir(parents=True)
        for relative in ("CMakeLists.txt", ".release-please-manifest.json"):
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(immutable_blob(repo, rev, relative))
        listing = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "--name-only", f"{rev}:docs/support"],
            capture_output=True, check=False, text=True, env=git_environment())
        require(listing.returncode == 0, "revision-support-ledger-list-unavailable")
        names = [line for line in listing.stdout.splitlines() if line]
        require(names, "revision-support-ledger-list-empty")
        for name in names:
            (snapshot / "docs/support" / name).touch()
        pinned_identity = tree_identity(snapshot)
        require(pinned_identity == (RELEASE_VERSION, LEDGER),
                "revision-tree-identity-mismatch")

        receipt = immutable_blob(repo, rev, PERF_ATTRIBUTION)
        receipt_path = snapshot / PERF_ATTRIBUTION
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_bytes(receipt)
        positive = 0
        for relative in (README, PREVIEW):
            text = immutable_blob(repo, rev, relative).decode("utf-8", errors="strict")
            positive += check_claim_boundaries(relative, prose(text))

        controls = (
            (README, "Save states load across GabbaBoy versions.",
             "false-cross-version-state-claim"),
            (PREVIEW, "Saves are power-loss safe.", "false-durability-claim"),
            (README, "Host mode runs on Windows.",
             "false-windows-host-claim"),
            (PREVIEW, "GabbaBoy supports save states on every platform.", "unscoped-state-claim"),
        )
        rejected = 0
        for relative, claim, reason in controls:
            original = immutable_blob(repo, rev, relative).decode("utf-8", errors="strict")
            try:
                check_claim_boundaries(relative, prose(original + "\n" + claim))
            except ContractError as error:
                require(str(error) == f"{reason}:{relative}",
                        f"claim-boundary-control-wrong-reason:{reason}:{error}")
                rejected += 1
            else:
                raise ContractError(f"claim-boundary-control-accepted:{reason}:{relative}")
        notes_controls, notes_rejected = run_self_test_release_notes(snapshot, rev)
        require(notes_controls == notes_rejected,
                "release-notes-control-count-mismatch")
        positives = positive + notes_controls
        all_controls = len(controls) + notes_controls
        require(rejected + notes_rejected == all_controls,
                "claim-boundary-control-count-mismatch")
        return positives, all_controls


def flexible(phrase: str) -> re.Pattern[str]:
    """Match a phrase across line wraps, as the prose parser sees it."""
    return re.compile(r"\s+".join(re.escape(word) for word in phrase.split()))


def replace_all(text: str, old: str, new: str, name: str) -> str:
    pattern = flexible(old)
    require(pattern.search(text) is not None,
            f"self-test-mutation-target-missing:{name}")
    return pattern.sub(lambda _match: new, text)


def comment_all(text: str, old: str, name: str) -> str:
    pattern = flexible(old)
    require(pattern.search(text) is not None,
            f"self-test-mutation-target-missing:{name}")
    return pattern.sub(lambda match: f"<!-- {match.group(0)} -->", text)


def run_self_test_docs(root: Path) -> tuple[int, int]:
    quote_prefix_probe = "> " * 256 + "plain body text\n"
    require(mask_markdown_nonrendered(quote_prefix_probe) == quote_prefix_probe,
            "markdown-container-prefix-control-failed")
    originals = {relative: read_document(root, relative)
                 for relative in PUBLIC_SURFACES}
    rejected = 0
    rejected_reasons: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-docs-") as temp:
        test_root = Path(temp)
        copy_inputs(root, test_root)
        child_result(test_root, "docs")

        readme_path = test_root / README
        readme_original = originals[README]
        write_lf(readme_path, readme_original +
                 "\n```html\n<div hidden>example</div>\n\t[ledger](docs/support/v0.4.0.md)\n```\n")
        child_result(test_root, "docs")
        write_lf(readme_path, readme_original)

        masked_incomplete_openers = (
            "\n<!-- <script\n -->\n\n"
            "```html\n<pre \n```\n\n"
            "    <style\n    [ledger](docs/support/v0.4.0.md)\n\n"
            "`<!DOCTYPE html` `<?xml version=\"1.0\"`\n"
        )
        write_lf(readme_path, readme_original + masked_incomplete_openers)
        child_result(test_root, "docs")
        write_lf(readme_path, readme_original)

        incomplete_html_openers = (
            ("script-newline", "<script\n"),
            ("script-space-newline", "<script \n"),
            ("pre-newline", "<pre\n"),
            ("pre-space-newline", "<pre \n"),
            ("style-newline", "<style\n"),
            ("style-space-newline", "<style \n"),
            ("script-mixed-case", "<ScRiPt\n"),
            ("doctype-html", "<!DOCTYPE html\n"),
            ("xml-processing-instruction", '<?xml version="1.0"\n'),
        )
        for opener_name, opener in incomplete_html_openers:
            child_result(test_root, "docs")
            incomplete_disclosure = replace_all(
                readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
                opener + "Physical CGB-E remains UNKNOWN/POLICY",
                f"incomplete-html-{opener_name}-hides-hardware-disclosure")
            write_lf(readme_path, incomplete_disclosure)
            child_result(test_root, "docs", "markdown-raw-html-unsupported")
            rejected_reasons.append(f"incomplete-html-{opener_name}-hides-hardware-disclosure")
            rejected += 1
            write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        inline_code_disclosure = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "`Physical CGB-E remains UNKNOWN/POLICY`", "inline-code-hides-hardware-disclosure")
        write_lf(readme_path, inline_code_disclosure)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        for name, definition in (
            ("blockquote-reference-title-hides-hardware-disclosure",
             "> [Physical CGB-E remains UNKNOWN/POLICY]: assets/info.png"),
            ("list-reference-title-hides-hardware-disclosure",
             "- [Physical CGB-E remains UNKNOWN/POLICY]: assets/info.png"),
            ("ordered-list-reference-title-hides-hardware-disclosure",
             "1. [Physical CGB-E remains UNKNOWN/POLICY]: assets/info.png"),
        ):
            child_result(test_root, "docs")
            changed = replace_all(
                readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "", name)
            changed = changed.rstrip() + "\n\n" + definition + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
            rejected_reasons.append("physical-cgb-limit-missing")
            rejected += 1
            write_lf(readme_path, readme_original)

        explicit_image_reference_disclosures = (
            ("full-image-reference-hides-hardware-disclosure",
             "![Physical CGB-E remains UNKNOWN/POLICY][disclosure]\n\n"
             "[disclosure]: assets/info.png"),
            ("collapsed-image-reference-hides-hardware-disclosure",
             "![Physical CGB-E remains UNKNOWN/POLICY][]\n\n"
             "[Physical CGB-E remains UNKNOWN/POLICY]: assets/info.png"),
        )
        for name, definition in explicit_image_reference_disclosures:
            child_result(test_root, "docs")
            changed = replace_all(
                readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "", name)
            changed = changed.rstrip() + "\n\n" + definition + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
            rejected_reasons.append(name)
            rejected += 1
            write_lf(readme_path, readme_original)

        for name, definition in (
            ("multiline-reference-title-hides-hardware-disclosure",
             '[unused-physical]: https://example.invalid\n  "Physical CGB-E remains UNKNOWN/POLICY"'),
            ("blockquote-multiline-reference-title-hides-hardware-disclosure",
             '> [unused-physical]: https://example.invalid\n>   "Physical CGB-E remains UNKNOWN/POLICY"'),
            ("list-multiline-reference-title-hides-hardware-disclosure",
             '- [unused-physical]: https://example.invalid\n  "Physical CGB-E remains UNKNOWN/POLICY"'),
        ):
            child_result(test_root, "docs")
            changed = replace_all(
                readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "", name)
            changed = changed.rstrip() + "\n\n" + definition + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
            rejected_reasons.append("physical-cgb-limit-missing")
            rejected += 1
            write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        malformed_link_prefix = "[x](" * 2048
        malformed_link_document = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "",
            "unclosed-link-prefix-hides-hardware-disclosure")
        malformed_link_document = (
            malformed_link_prefix + "\n" + malformed_link_document
            + "\nPhysical CGB-E remains UNKNOWN/POLICY\n")
        write_lf(readme_path, malformed_link_document)
        child_result(test_root, "docs", "markdown-inline-link-malformed")
        rejected_reasons.append("markdown-inline-link-malformed")
        rejected += 1
        write_lf(readme_path, readme_original)

        for name, extra in (
            ("malformed-link-cannot-hide-game-claim",
             "[x](unfinished\nCGB game passes all acceptance checks."),
            ("malformed-link-cannot-hide-raw-html",
             "[x](unfinished\n<div hidden>Physical CGB-E remains UNKNOWN/POLICY</div>"),
            ("nested-parentheses-inline-title-cannot-hide-game-claim",
             "[ordinary](/url (CGB game passes all acceptance checks. (inner)))"),
            ("nested-parentheses-image-title-cannot-hide-game-claim",
             "![CGB game passes all acceptance checks.](/url (outer (inner) title))"),
            ("nested-parentheses-inline-title-cannot-hide-raw-html",
             "[ordinary](/url (</span><div hidden>text</div> (inner)))"),
            ("inline-title-without-destination-separator-cannot-hide-game-claim",
             '[ordinary](<url>"CGB game passes all acceptance checks.")'),
            ("nul-inline-bare-destination-cannot-hide-game-claim",
             '[ordinary](/url\x00 "CGB game passes all acceptance checks.")'),
            ("nul-inline-angle-destination-cannot-hide-game-claim",
             '[ordinary](<url\x00> "CGB game passes all acceptance checks.")'),
            ("inline-title-with-blank-line-cannot-hide-game-claim",
             '[ordinary](/url "title starts here\n\nCGB game passes all acceptance checks.")'),
        ):
            child_result(test_root, "docs")
            changed = readme_original + "\n" + extra + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", "markdown-inline-link-malformed")
            rejected_reasons.append(name)
            rejected += 1
            write_lf(readme_path, readme_original)

        invalid_reference_claims = (
            ("invalid-reference-destination-hides-game-claim",
             "[CGB game passes all acceptance checks.]: invalid destination with spaces"),
            ("empty-reference-destination-hides-game-claim",
             "[CGB game passes all acceptance checks.]:"),
            ("unterminated-reference-title-hides-game-claim",
             '[CGB game passes all acceptance checks.]: /url "unterminated'),
            ("invalid-reference-destination-escape-hides-game-claim",
             "[CGB game passes all acceptance checks.]: /url\\q"),
            ("invalid-reference-title-escape-hides-game-claim",
             '[CGB game passes all acceptance checks.]: /url "bad\\q"'),
            ("over-nested-reference-destination-hides-game-claim",
             "[CGB game passes all acceptance checks.]: " + "(" * 33 + "target" + ")" * 33),
            ("nested-reference-title-hides-game-claim",
             "[CGB game passes all acceptance checks.]: /url (outer (inner) title)"),
            ("blank-line-reference-title-hides-game-claim",
             '[CGB game passes all acceptance checks.]: /url "title\n\ncontinues"'),
            ("reference-title-without-destination-separator-hides-game-claim",
             '[CGB game passes all acceptance checks.]: '
             '<https://example.invalid/>"title"'),
            ("nul-reference-destination-hides-game-claim",
             '[CGB game passes all acceptance checks.]: /url\x00 "title"'),
            ("invalid-reference-image-hides-game-claim",
             "![CGB game passes all acceptance checks.]\n\n"
             "[CGB game passes all acceptance checks.]: invalid destination with spaces"),
        )
        for name, extra in invalid_reference_claims:
            child_result(test_root, "docs")
            changed = readme_original + "\n" + extra + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"unsupported-cgb-game-qualification:{README}")
            rejected_reasons.append(name)
            rejected += 1
            write_lf(readme_path, readme_original)

        mismatched_reference_titles = (
            ("root-reference-definition-blockquote-title",
             '[unused]: /url\n> "CGB game passes all acceptance checks."'),
            ("root-reference-definition-list-title",
             '[unused]: /url\n- "CGB game passes all acceptance checks."'),
            ("blockquote-reference-definition-list-title",
             '> [unused]: /url\n- "CGB game passes all acceptance checks."'),
            ("list-reference-definition-blockquote-title",
             '- [unused]: /url\n> "CGB game passes all acceptance checks."'),
            ("arabic-indic-prefix-is-not-an-ordered-list-marker",
             '١. [CGB game passes all acceptance checks.]: /url'),
            ("superscript-prefix-is-not-an-ordered-list-marker",
             '¹. [CGB game passes all acceptance checks.]: /url'),
            ("nbsp-reference-label-does-not-match-shortcut-image",
             '![CGB game passes all acceptance checks.]\n\n'
             '[CGB\u00a0game passes all acceptance checks.]: /url'),
            ("thin-space-reference-label-does-not-match-shortcut-image",
             '![CGB game passes all acceptance checks.]\n\n'
             '[CGB\u2009game passes all acceptance checks.]: /url'),
            ("escaped-punctuation-reference-label-does-not-match-shortcut-image",
             '![CGB game passes all acceptance checks.]\n\n'
             '[CGB game passes all acceptance checks\\.]: /url'),
            ("unresolved-full-image-reference-cannot-hide-game-claim",
             '![CGB game passes all acceptance checks.][missing-label]'),
            ("unresolved-collapsed-image-reference-cannot-hide-game-claim",
             '![CGB game passes all acceptance checks.][]'),
            ("invalid-explicit-image-reference-cannot-hide-game-claim",
             '![CGB game passes all acceptance checks.][other]\n\n'
             '[other]: invalid destination with spaces'),
            ("unresolved-link-label-cannot-hide-game-claim",
             '[ordinary][CGB game passes all acceptance checks.]'),
        )
        for name, extra in mismatched_reference_titles:
            child_result(test_root, "docs")
            changed = readme_original + "\n" + extra + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"unsupported-cgb-game-qualification:{README}")
            rejected_reasons.append(name)
            rejected += 1
            write_lf(readme_path, readme_original)

        def readme_parser_control(name: str, extra: str,
                                  reason: str | None = None,
                                  *, remove_hardware_disclosure: bool = False) -> None:
            nonlocal rejected
            child_result(test_root, "docs")
            base = readme_original
            if remove_hardware_disclosure:
                base = replace_all(
                    base, "Physical CGB-E remains UNKNOWN/POLICY", "", name)
            changed = base.rstrip() + "\n\n" + extra + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", reason)
            if reason is not None:
                rejected_reasons.append(name)
                rejected += 1
            write_lf(readme_path, readme_original)

        for name, reference in (
            ("whitespace-reference-label-cannot-hide-game-claim", "[ ]"),
        ):
            readme_parser_control(
                name,
                "![CGB game passes all acceptance checks.]" + reference + "\n\n"
                "[CGB game passes all acceptance checks.]: /url",
                f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "tab-reference-label-cannot-hide-game-claim",
            "![CGB game passes all acceptance checks.][\t]\n\n"
            "[CGB game passes all acceptance checks.]: /url",
            "markdown-tab-unsupported")

        readme_parser_control(
            "empty-reference-label-remains-collapsed-image-syntax",
            "![CGB game passes all acceptance checks.][]\n\n"
            "[CGB game passes all acceptance checks.]: /url")

        readme_parser_control(
            "tab-list-marker-cannot-hide-reference-title-game-claim",
            '> -\t[unused]: /url\n>  "CGB game passes all acceptance checks."',
            f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "tab-expanded-list-continuation-at-column-four-masks-reference-title",
            '> -\t[unused]: /url\n>   "CGB game passes all acceptance checks."')

        readme_parser_control(
            "commented-explicit-reference-label-cannot-hide-game-claim",
            "![ordinary][CGB<!-- gap --> game passes all acceptance checks.]\n\n"
            "[CGB game passes all acceptance checks.]: /url",
            f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "commented-shortcut-image-label-cannot-hide-game-claim",
            "![CGB<!-- gap --> game passes all acceptance checks.]\n\n"
            "[CGB game passes all acceptance checks.]: /url",
            f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "matching-comments-in-reference-labels-still-resolve",
            "![ordinary][CGB<!-- gap --> game passes all acceptance checks.]\n\n"
            "[CGB<!-- gap --> game passes all acceptance checks.]: /url")
        readme_parser_control(
            "different-comment-payloads-cannot-match-reference-labels",
            "![CGB<!-- alt --> game passes all acceptance checks.]\n\n"
            "[CGB<!-- def --> game passes all acceptance checks.]: /url",
            f"unsupported-cgb-game-qualification:{README}")

        readme_parser_control(
            "comment-prefix-cannot-create-fence-hiding-game-claim",
            "<!-- -->```markdown\nCGB game passes all acceptance checks.",
            f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "standalone-comment-before-real-fence-still-masks-game-claim",
            "<!-- note -->\n\n```markdown\n"
            "CGB game passes all acceptance checks.\n```")

        readme_parser_control(
            "autolink-close-bracket-cannot-hide-hardware-disclosure",
            '[<https://example.invalid/]>](https://example.invalid/ '
            '"Physical CGB-E remains UNKNOWN/POLICY")',
            f"physical-cgb-limit-missing:{README}",
            remove_hardware_disclosure=True)
        readme_parser_control(
            "autolink-close-bracket-title-remains-nonrendered",
            '[<https://example.invalid/]>](https://example.invalid/ '
            '"<script>not prose</script>")')

        invisible_format_separators = (
            ("zero-width-space-game-claim-cannot-pass", "\u200b"),
            ("word-joiner-game-claim-cannot-pass", "\u2060"),
            ("zero-width-non-joiner-game-claim-cannot-pass", "\u200c"),
        )
        for name, separator in invisible_format_separators:
            readme_parser_control(
                name, "CGB" + separator + " game passes all acceptance checks.",
                f"unsupported-cgb-game-qualification:{README}")
        for name, separator in DEFAULT_IGNORABLE_CLAIM_SEPARATORS:
            readme_parser_control(
                "default-ignorable-" + name + "-game-claim-cannot-pass",
                "CGB" + separator + " game passes all acceptance checks.",
                f"unsupported-cgb-game-qualification:{README}")
        for name, claim in COMMONMARK_REFERENCED_GAME_CLAIMS:
            readme_parser_control(
                "commonmark-reference-" + name + "-game-claim-cannot-pass",
                claim, f"unsupported-cgb-game-qualification:{README}")
        for name, claim in COMMONMARK_HARD_BREAK_GAME_CLAIMS:
            readme_parser_control(
                "commonmark-hard-break-" + name + "-game-claim-cannot-pass",
                claim, f"unsupported-cgb-game-qualification:{README}")
        readme_parser_control(
            "invisible-format-safe-game-evidence-prose-remains-valid",
            "CGB\u200b test-ROM results remain software-model evidence only.")
        readme_parser_control(
            "default-ignorable-safe-game-evidence-prose-remains-valid",
            "CGB\u034f test-ROM results remain software-model evidence only.")
        readme_parser_control(
            "commonmark-visible-reference-safe-evidence-prose-remains-valid",
            "CGB&#x20; test-ROM results remain software-model evidence only.")
        readme_parser_control(
            "commonmark-reference-claim-in-code-span-remains-masked",
            "`CGB&#x200b; game passes all acceptance checks.`")
        readme_parser_control(
            "commonmark-hard-break-safe-game-evidence-prose-remains-valid",
            "CGB\\\ntest-ROM results remain software-model evidence only.")
        readme_parser_control(
            "commonmark-hard-break-claim-in-code-span-remains-masked",
            "`CGB\\\ngame passes all acceptance checks.`")
        readme_parser_control(
            "commonmark-hard-break-claim-in-fenced-code-remains-masked",
            "```\nCGB\\\ngame passes all acceptance checks.\n```")

        multiline_reference_titles = (
            ("inline-multiline-reference-title-hides-hardware-disclosure",
             '[unused]: /url "title continues\n  Physical CGB-E remains UNKNOWN/POLICY"'),
            ("next-line-multiline-reference-title-hides-hardware-disclosure",
             '[unused]: /url\n  "title starts here\n  Physical CGB-E remains UNKNOWN/POLICY"'),
            ("next-line-reference-destination-and-title-hide-hardware-disclosure",
             '[unused]:\n  /url "Physical CGB-E remains UNKNOWN/POLICY"'),
        )
        for name, definition in multiline_reference_titles:
            child_result(test_root, "docs")
            changed = replace_all(
                readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "", name)
            changed = changed.rstrip() + "\n\n" + definition + "\n"
            write_lf(readme_path, changed)
            child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
            rejected_reasons.append(name)
            rejected += 1
            write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        shortcut_image_alt_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "![Physical CGB-E remains UNKNOWN/POLICY]",
            "shortcut-image-alt-hides-hardware-disclosure")
        shortcut_image_alt_only = shortcut_image_alt_only.rstrip() + (
            "\n\n[Physical CGB-E remains UNKNOWN/POLICY]: assets/info.png\n")
        write_lf(readme_path, shortcut_image_alt_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        escaped_parenthesized_title_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "",
            "escaped-parentheses-in-reference-title-hides-hardware-disclosure")
        escaped_parenthesized_title_only = escaped_parenthesized_title_only.rstrip() + (
            "\n\n[unused-escaped-title]: https://example.invalid/ "
            "(escaped \\(title\\) Physical CGB-E remains UNKNOWN/POLICY)\n")
        write_lf(readme_path, escaped_parenthesized_title_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        nested_image_alt_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "[![Physical CGB-E remains UNKNOWN/POLICY](assets/info.png)]"
            "(https://example.invalid/)",
            "nested-image-alt-hides-hardware-disclosure")
        write_lf(readme_path, nested_image_alt_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        for name, relative, phrase, reason in (
            ("inline-code-hides-game-absence", GAME_GUIDE, ABSENCE_SENTENCE,
             f"absence-statement-missing:{GAME_GUIDE}"),
            ("inline-code-hides-release-limit", RELEASE, "unsigned and not notarized",
             f"unsigned-limit-missing:{RELEASE}"),
            ("inline-code-hides-release-evidence-name", RELEASE,
             "The `v02-*` evidence names are the evidence-schema family",
             f"evidence-name-note-missing:{RELEASE}"),
            ("inline-code-hides-release-rights-reason", RELEASE,
             "µCity 1.3 stopped at the required `source/engine/hardware.inc` component, which has no identified grant or notice establishing repository/public-CI scope",
             f"v04-ucity-outcome-missing:{RELEASE}"),
        ):
            child_result(test_root, "docs")
            original = originals[relative]
            delimiter = "``" if "`" in phrase else "`"
            inline_code_disclosure = replace_all(
                original, phrase, f"{delimiter}{phrase}{delimiter}", name)
            target = test_root / relative
            write_lf(target, inline_code_disclosure)
            child_result(test_root, "docs", reason)
            rejected_reasons.append(reason.split(":", 1)[0])
            rejected += 1
            write_lf(target, original)

        link_title_controls = (
            ("link-title-hides-hardware-disclosure", README,
             "Physical CGB-E remains UNKNOWN/POLICY",
             f"physical-cgb-limit-missing:{README}"),
            ("link-title-hides-game-absence", GAME_GUIDE, ABSENCE_SENTENCE,
             f"absence-statement-missing:{GAME_GUIDE}"),
            ("link-title-hides-release-limit", RELEASE, "unsigned and not notarized",
             f"unsigned-limit-missing:{RELEASE}"),
            ("multiline-link-title-hides-hardware-disclosure", README,
             "Physical CGB-E remains UNKNOWN/POLICY",
             f"physical-cgb-limit-missing:{README}"),
        )
        for name, relative, phrase, reason in link_title_controls:
            child_result(test_root, "docs")
            original = originals[relative]
            changed = replace_all(
                original, phrase,
                (f'[details](https://example.invalid/ "title continues\n{phrase}")'
                 if "multiline" in name else
                 f'[details](https://example.invalid/ "{phrase}")'), name)
            target = test_root / relative
            write_lf(target, changed)
            child_result(test_root, "docs", reason)
            rejected_reasons.append(reason.split(":", 1)[0])
            rejected += 1
            write_lf(target, original)

        child_result(test_root, "docs")
        escaped_inline_title_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "",
            "escaped-parentheses-in-inline-title-hides-hardware-disclosure")
        escaped_inline_title_only = escaped_inline_title_only.rstrip() + (
            "\n\n[details](/url (escaped \\(title\\) "
            "Physical CGB-E remains UNKNOWN/POLICY))\n")
        write_lf(readme_path, escaped_inline_title_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        readme_title_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY", "",
            "unused-reference-title-hides-hardware-disclosure")
        readme_title_only = readme_title_only.rstrip() + (
            '\n\n[unused-release-disclosure]: https://example.invalid/ '
            '"Physical CGB-E remains UNKNOWN/POLICY"\n')
        write_lf(readme_path, readme_title_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        child_result(test_root, "docs")
        image_alt_only = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "![Physical CGB-E remains UNKNOWN/POLICY](assets/info.png)",
            "image-alt-hides-hardware-disclosure")
        write_lf(readme_path, image_alt_only)
        child_result(test_root, "docs", f"physical-cgb-limit-missing:{README}")
        rejected_reasons.append("physical-cgb-limit-missing")
        rejected += 1
        write_lf(readme_path, readme_original)

        notice_original = originals[NOTICES]
        notice_path = test_root / NOTICES
        hidden_notice_rows = (
            ("libbet", "Libbet and the Magic Floor v0.08 test fixture",
             "libbet-rights-disclosure-missing"),
            ("mooneye-mbc", "Mooneye mbc2/mbc5 derivative test ROMs (15)",
             "mooneye-mbc-rights-disclosure-missing"),
            ("magentests", "MagenTests out-of-bounds SRAM ROMs (3)",
             "magentests-rights-disclosure-missing"),
            ("age", "AGE CGB speed-switch ROMs", "age-rights-disclosure-missing"),
            ("rtc3test", "rtc3test MBC3 real-time-clock ROM and `tests.md`",
             "rtc3test-rights-disclosure-missing"),
            ("mooneye-dmg-cgb", "Mooneye DMG and CGB test ROMs (3 and 9)",
             "mooneye-dmg-cgb-rights-disclosure-missing"),
            ("samesuite", "SameSuite CGB DMA and APU test ROMs (4 and 70)",
             "samesuite-rights-missing"),
        )
        for name, label, reason in hidden_notice_rows:
            child_result(test_root, "docs")
            row = next((line for line in notice_original.splitlines()
                        if line.startswith(f"| {label} |")), None)
            require(row is not None,
                    f"self-test-mutation-target-missing:inline-code-hides-{name}-notice-row")
            changed = notice_original.replace(row, f"```markdown\n{row}\n```", 1)
            require(changed != notice_original,
                    f"self-test-mutation-no-op:inline-code-hides-{name}-notice-row")
            write_lf(notice_path, changed)
            child_result(test_root, "docs", reason)
            rejected_reasons.append(reason.split(":", 1)[0])
            rejected += 1
            write_lf(notice_path, notice_original)

        hidden_disclosure = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "<div hidden>Physical CGB-E remains UNKNOWN/POLICY</div>", "hidden-html-disclosure")
        write_lf(readme_path, hidden_disclosure)
        child_result(test_root, "docs", "markdown-raw-html-unsupported")
        rejected_reasons.append("markdown-raw-html-unsupported")
        rejected += 1
        write_lf(readme_path, readme_original)
        hidden_details = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "<details><summary>More</summary>Physical CGB-E remains UNKNOWN/POLICY</details>",
            "details-html-disclosure")
        write_lf(readme_path, hidden_details)
        child_result(test_root, "docs", "markdown-raw-html-unsupported")
        rejected_reasons.append("markdown-raw-html-unsupported")
        rejected += 1
        write_lf(readme_path, readme_original)
        declared_html = replace_all(
            readme_original, "Physical CGB-E remains UNKNOWN/POLICY",
            "<!DOCTYPE html>Physical CGB-E remains UNKNOWN/POLICY", "declared-html-disclosure")
        write_lf(readme_path, declared_html)
        child_result(test_root, "docs", "markdown-raw-html-unsupported")
        rejected_reasons.append("markdown-raw-html-unsupported")
        rejected += 1
        write_lf(readme_path, readme_original)
        tabbed_link = readme_original + "\n-\t    [ledger](docs/support/v0.4.0.md)\n"
        write_lf(readme_path, tabbed_link)
        child_result(test_root, "docs", "markdown-tab-unsupported")
        rejected_reasons.append("markdown-tab-unsupported")
        rejected += 1
        write_lf(readme_path, readme_original)

        component_notice = test_root / "fixtures/visible-demo/LICENSE.txt"
        component_notice_bytes = component_notice.read_bytes()
        component_notice.unlink()
        child_result(test_root, "docs", "notice-license-file-missing:visible-demo")
        component_notice.write_bytes(component_notice_bytes)
        rejected_reasons.append("notice-license-file-missing")
        rejected += 1
        release_copy = test_root / RELEASE
        release_bytes = release_copy.read_bytes()
        release_copy.write_bytes(b"\xff")
        child_result(test_root, "docs", f"document-encoding-invalid:{RELEASE}")
        release_copy.write_bytes(release_bytes)
        rejected += 1
        child_result(test_root, "docs")

        def comment_out(phrase: str) -> Callable[[str], str]:
            return lambda text: comment_all(text, phrase, "comment-only")

        def drop(phrase: str, name: str) -> Callable[[str], str]:
            return lambda text: replace_all(text, phrase, "", name)

        def append(extra: str) -> Callable[[str], str]:
            return lambda text: text + "\n" + extra + "\n"

        def swap(old: str, new: str, name: str) -> Callable[[str], str]:
            return lambda text: replace_all(text, old, new, name)

        mutations: tuple[tuple[str, str, Callable[[str], str], str], ...] = (
            ("missing-readme-absence", README, drop(ABSENCE_STATEMENT, "a"),
             f"absence-statement-missing:{README}"),
            ("missing-guide-absence", GAME_GUIDE, drop(ABSENCE_STATEMENT, "b"),
             f"absence-statement-missing:{GAME_GUIDE}"),
            ("readme-positive-claim", README,
             append("CGB game passes all acceptance checks."),
             f"unsupported-cgb-game-qualification:{README}"),
            ("guide-positive-claim", GAME_GUIDE,
             append("CGB game passes all acceptance checks."),
             f"unsupported-cgb-game-qualification:{GAME_GUIDE}"),
            ("missing-readme-corpus-link", README,
             drop("[CGB corpus contract](docs/cgb-corpus.md)", "c"),
             f"cgb-corpus-evidence-link-missing:{README}"),
            ("missing-readme-game-link", README,
             drop("[game acceptance evidence](docs/game-acceptance.md)", "d"),
             f"game-evidence-link-missing:{README}"),
            ("missing-guide-corpus-link", GAME_GUIDE,
             drop("[CGB corpus contract](cgb-corpus.md)", "e"),
             f"cgb-corpus-evidence-link-missing:{GAME_GUIDE}"),
            ("missing-api-phrase", README, drop("opaque `gbb_instance`", "f"),
             f"api-instance-missing:{README}"),
            ("missing-rtc-phrase", SAVES,
             drop("21-byte `GBB_RTC_BLOCK_SIZE` clock block", "g"),
             f"rtc-block-contract-missing:{SAVES}"),
            ("missing-save-phrase", NATIVE,
             drop("not the SDL player's versioned/checksummed save envelope", "h"),
             f"raw-save-boundary-missing:{NATIVE}"),
            ("missing-model-phrase", PROFILE,
             drop("CGB-CPU-E software model", "i"),
             f"cgb-model-missing:{PROFILE}"),
            ("comment-only-limit", PREVIEW,
             comment_out("The package is unsigned and not notarized"),
             f"unsigned-limit-missing:{PREVIEW}"),
            ("comment-only-release-absence", RELEASE,
             comment_out(ABSENCE_STATEMENT),
             f"absence-statement-missing:{RELEASE}"),
            ("missing-unreleased-reconciliation", UNRELEASED,
             drop("Reconciled into v0.3.0: the save-state and host-contract entries are scoped claims",
                  "unreleased-reconciliation"),
             f"unreleased-reconciliation-missing:{UNRELEASED}"),
            ("stale-unreleased-pending", UNRELEASED,
             append("## Host mode (HOST-01..03, pending v0.3.0)"),
             f"unreleased-pending-stale:{UNRELEASED}"),
            ("missing-publication-limit", RELEASE,
             drop("this page makes no publication claim for the version in this tree",
                  "publication-limit"),
             f"publication-limit-missing:{RELEASE}"),
            ("missing-retry-identity-wording", RELEASE,
             drop("identity and consistency check", "retry-identity"),
             f"retry-identity-wording-missing:{RELEASE}"),
            ("missing-evidence-family-note", RELEASE,
             drop("The `v02-*` evidence names are the evidence-schema family",
                  "evidence-family"),
             f"evidence-name-note-missing:{RELEASE}"),
            ("missing-upgrade-preference-backup", RELEASE,
             drop("back up the preference directory", "preference-backup"),
             f"upgrade-guidance-missing:{RELEASE}"),
            ("missing-upgrade-state-limit", RELEASE,
             drop("slots and the undo file do not survive an upgrade", "state-upgrade"),
             f"upgrade-guidance-missing:{RELEASE}"),
            ("missing-pretag-gate-guidance", RELEASE,
             drop("`version-pr-gate` is not a required check", "pretag-gate"),
             f"pre-tag-gate-enforcement-missing:{RELEASE}"),
            ("false-v04-publication-claim", RELEASE,
             append("v0.4.0 has been published."),
             f"false-publication-claim:{RELEASE}"),
            ("missing-v04-preparation-scope", RELEASE,
             drop("The last qualified release is v0.3.0. Phase 23 prepares v0.4.0 through the existing release-please path",
                  "preparation-scope"),
             f"v04-preparation-scope-missing:{RELEASE}"),
            ("missing-v04-version-agreement", RELEASE,
             drop("generated `docs/support/v0.4.0.md` ledger, and rendered release notes must all identify exactly v0.4.0",
                  "version-agreement"),
             f"v04-version-agreement-missing:{RELEASE}"),
            ("missing-v04-shared-profile", RELEASE,
             drop("The release-notes preface and support ledger share the validated immutable "
                  "`tests/data/support-claims-v0.4.json` profile", "shared-profile"),
             f"v04-shared-copy-missing:{RELEASE}"),
            ("missing-v04-potion-panic-reason", RELEASE,
             drop("Potion Panic stopped before a source identity was returned: its creator-linked Codeberg source could not be reached, "
                  "and exact component grants plus repository/public-CI scope remain unestablished", "potion-panic"),
             f"v04-potion-panic-outcome-missing:{RELEASE}"),
            ("missing-v04-ucity-reason", RELEASE,
             drop("µCity 1.3 stopped at the required `source/engine/hardware.inc` component, which has no identified grant "
                  "or notice establishing repository/public-CI scope", "ucity"),
             f"v04-ucity-outcome-missing:{RELEASE}"),
            ("missing-v04-game-boundary", RELEASE,
             drop("Neither candidate was built or run; no CGB game was admitted. These source/rights-scope outcomes "
                  "do not establish a license prohibition", "game-boundary"),
             f"v04-game-admission-boundary-missing:{RELEASE}"),
            ("missing-v04-harness-boundary", RELEASE,
             drop("The CGB-CPU-E native-mode RGB555/PCM result is original-harness-only; its digests establish repeatability only",
                  "harness-boundary"),
             f"v04-harness-boundary-missing:{RELEASE}"),
            ("missing-v04-diagnostic-accounting", RELEASE,
             drop("Phase 22 is a synthetic composition tracer and metadata-only assessment: 513 named entries, seven "
                  "unresolved real-fixture gates, zero real fixtures admitted, and zero real fixtures executed",
                  "diagnostic-accounting"),
             f"v04-diagnostic-accounting-missing:{RELEASE}"),
            ("missing-v04-pending-status", RELEASE,
             drop("FIXT-01, RIGHTS-01, DIAG-01, DIAG-02, and REL-01 remain Pending until their separate release evidence is accepted",
                  "pending-status"),
             f"v04-pending-status-missing:{RELEASE}"),
            ("missing-v04-platform-matrix", RELEASE,
             drop("The established product matrix remains Linux x64, macOS arm64, and Windows x64 core archives, "
                  "plus the macOS arm64 player", "product-matrix"),
             f"v04-product-matrix-missing:{RELEASE}"),
            ("missing-v04-player-platform-limit", RELEASE,
             drop("No Linux or Windows packaged-player game smoke is claimed; the player is macOS arm64 only",
                  "player-platform-limit"),
             f"v04-player-platform-limit-missing:{RELEASE}"),
            ("missing-v04-macos-deployment-caveat", RELEASE,
             drop("macOS 15.0 is the minimum deployment target and the build used the macOS 15.5 SDK",
                  "macos-deployment-caveat"),
             f"v04-macos-deployment-caveat-missing:{RELEASE}"),
            ("missing-v04-host-state-boundary", RELEASE,
             drop("Save states load only in the exact GabbaBoy release that wrote them. Host mode is POSIX-only, "
                  "and Windows refuses `--save-dir`", "host-state"),
             f"v04-host-state-compatibility-missing:{RELEASE}"),
            ("missing-v04-deterministic-performance-boundary", RELEASE,
             drop("The deterministic instruction-count gate and native realtime floor remain blocking; "
                  "paired wall-clock timing is advisory and cannot approve a release", "deterministic-performance"),
             f"v04-performance-boundary-missing:{RELEASE}"),
            ("missing-v04-operator-sequence", RELEASE,
             drop("H → R1 → W → R2 → nightly → pre-tag gate", "operator-sequence"),
             f"v04-operator-sequence-missing:{RELEASE}"),
            ("missing-v04-window-recovery-hold", RELEASE,
             drop("A note or body regeneration, moved tag, or changed source invalidates the window and keeps the release on hold",
                  "window-recovery"),
             f"v04-window-recovery-hold-missing:{RELEASE}"),
            ("missing-v04-downloaded-byte-gate", RELEASE,
             drop("After tagging, the existing trusted release path must still build, attach, download, and verify the real "
                  "core and player archive bytes, installed consumers, notices, and fixture exclusion before the draft can be published",
                  "downloaded-byte-gate"),
             f"v04-downloaded-byte-gate-missing:{RELEASE}"),
            ("missing-v04-specific-recovery-hold", RELEASE,
             drop("If v0.4.0 notes omit a required disclosure, keep the draft unpublished",
                  "v04-recovery-hold"),
             f"v04-recovery-hold-missing:{RELEASE}"),
            ("retry-tamper-overclaim", RELEASE,
             append("The retry check provides tamper detection for attached assets."),
             f"retry-tamper-overclaim:{RELEASE}"),
            ("cross-version-state-claim", README,
             append("Save states load across GabbaBoy versions."),
             f"false-cross-version-state-claim:{README}"),
            ("durability-claim", PREVIEW,
             append("Saves are power-loss safe."),
             f"false-durability-claim:{PREVIEW}"),
            ("windows-host-claim", PREVIEW,
             append("Host mode runs on Windows."),
             f"false-windows-host-claim:{PREVIEW}"),
            ("unscoped-state-claim", README,
             append("GabbaBoy supports save states on every platform."),
             f"unscoped-state-claim:{README}"),
            ("undeclared-symbol", README,
             swap("`gbb_run_ex`", "`gbb_run_nonexistent`", "j"),
             f"undeclared-public-symbol:{README}:gbb_run_nonexistent"),
            ("undeclared-symbol-in-prose", AUDIO,
             append("Call GBB_INVENTED_CAPABILITY to enable it."),
             f"undeclared-public-symbol:{AUDIO}:GBB_INVENTED_CAPABILITY"),
            ("false-hardware-qualification", PROFILE,
             append("Physical CGB-E hardware is qualified."),
             f"unqualified-hardware-or-game-claim:{PROFILE}"),
            ("false-game-qualification", LEDGER,
             append("CGB game acceptance has passed."),
             f"unsupported-cgb-game-qualification:{LEDGER}"),
            ("false-signing-claim", RELEASE,
             append("The macOS player is signed and notarized."),
             f"false-signing-or-notarization-claim:{RELEASE}"),
            ("false-publication-claim", RELEASE,
             append(f"v{RELEASE_VERSION} has been published."),
             f"false-publication-claim:{RELEASE}"),
            ("false-platform-guarantee", RELEASE,
             append("GabbaBoy supports all architectures."),
             f"false-platform-guarantee:{RELEASE}"),
            ("false-fuzz-claim", RELEASE,
             append("The fuzz campaign passed."),
             f"false-fuzz-campaign-claim:{RELEASE}"),
            ("removed-source-archive-distinction", RELEASE,
             drop("GitHub generated source archives retain the admitted licensed "
                  "fixtures and their notices", "k"),
             f"source-archive-distinction-missing:{RELEASE}"),
            ("removed-runner-label-limit", RELEASE,
             swap("not minimum OS versions", "and minimum OS versions", "l"),
             f"runner-label-limit-missing:{RELEASE}"),
            ("missing-notice-source-archive", NOTICES,
             drop("GitHub generated source archives retain the admitted licensed "
                  "fixtures and their notices", "m"),
             f"source-archive-distinction-missing:{NOTICES}"),
            ("missing-notice-product-distinction", NOTICES,
             drop("Installed core packages carry exactly the\noriginal project-authored tracer, visible demo, and MBC1 continuation fixtures\nwith their pinned notices.", "product"),
             f"product-package-distinction-missing:{NOTICES}"),
            ("contradictory-notice-product-distinction", NOTICES,
             swap("Controlled game and diagnostic bytes\nremain repository-test inputs and are excluded from binary products.",
                  "Controlled game and diagnostic bytes are included in binary products.", "product-contradiction"),
             f"product-package-distinction-missing:{NOTICES}"),
            ("rebound-attribution", NOTICES,
             append("Rebound assets are attributed to the admitted fixtures."),
             f"rebound-attribution-present:{NOTICES}"),
            ("stale-notice-digest", NOTICES,
             lambda text: re.sub(
                 r"(\| `age` \| `)[0-9a-f]{64}", r"\g<1>" + "0" * 64, text, count=1),
             "notice-digest-stale:age:manifest"),
            ("missing-notice-fixture", NOTICES,
             lambda text: re.sub(r"^\| `samesuite` \|.*\n", "", text, flags=re.MULTILINE),
             "notice-fixture-missing:samesuite"),
            ("unknown-notice-fixture", NOTICES,
             append("| `ghost-rom` | `" + "1" * 64 + "` | `" + "2" * 64 + "` |"),
             "notice-fixture-unknown:ghost-rom"),
            ("missing-ledger-absence", LEDGER, drop(ABSENCE_STATEMENT, "n"),
             f"absence-statement-missing:{LEDGER}"),
            ("missing-historical-slowdown", RELEASE,
             drop("**+14.86% slower than v0.1.0 with a ±1.62% margin**", "slowdown"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("changed-historical-margin", RELEASE,
             swap("±1.62%", "±1.63%", "margin"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("changed-historical-slowdown", RELEASE,
             swap("+14.86% slower", "+14.85% slower", "slowdown-number"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("removed-historical-qualification", RELEASE,
             swap("historical evidence", "fresh evidence", "history"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("misattributed-performance-source", RELEASE,
             swap("ab301aa69b1f085050fd66bf7b1378863a0821f2",
                  "e30d168f7fc61de8db0a3801e7b1736362912cb7", "source"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("changed-performance-workload", RELEASE,
             swap("original-wram-tracer-1m-half-dots-v1",
                  "original-wram-tracer-2m-half-dots-v1", "workload"),
             f"historical-performance-disclosure-missing:{RELEASE}"),
            ("removed-ledger-slowdown", LEDGER,
             drop("**+14.86% slower**", "ledger-slowdown"),
             f"historical-performance-disclosure-missing:{LEDGER}"),
            ("changed-ledger-fixture-bytes", LEDGER,
             swap("ded6a499118b57539710892d58b4d7ced2269f08d447eed1451201d8ad65ec8d",
                  "0" * 64, "fixture"),
             f"historical-performance-disclosure-missing:{LEDGER}"),
        )
        for name, relative, edit, reason in mutations:
            original = originals[relative]
            changed = edit(original)
            require(changed != original, f"self-test-mutation-no-op:{name}")
            target = test_root / relative
            write_lf(target, changed)
            child_result(test_root, "docs", reason)
            rejected_reasons.append(reason.split(":", 1)[0])
            write_lf(target, original)
            rejected += 1
        child_result(test_root, "docs")

        # A claim marker removed from the production-parsed block must fail.
        for relative, key_phrase, reason in (
            (AUDIO, "<!-- cgb-apu-audio-claims-begin -->",
             "missing-claim-markers:audio:" + AUDIO),
            (PROFILE, "<!-- cgb-apu-claims-begin -->",
             "missing-claim-markers:profile:" + PROFILE),
        ):
            original = originals[relative]
            changed = replace_all(original, key_phrase, "", "marker")
            target = test_root / relative
            write_lf(target, changed)
            child_result(test_root, "docs", reason)
            write_lf(target, original)
            rejected += 1

        # A header symbol removed must make dependent prose fail to resolve.
        header = test_root / HEADER
        header_text = read_document(root, HEADER)
        changed = re.sub(r"\bgbb_queue_events\b", "gbb_queue_removed", header_text)
        require(changed != header_text, "self-test-mutation-no-op:header-symbol")
        write_lf(header, changed)
        child_result(test_root, "docs",
                     f"undeclared-public-symbol:{README}:gbb_queue_events")
        write_lf(header, header_text)
        rejected += 1
        child_result(test_root, "docs")
    controls = len(mutations) + 102 + len(incomplete_html_openers)
    require(rejected == controls, "self-test-control-count-mismatch")
    notes_controls, notes_rejected = run_self_test_release_notes()
    print("adoption-doc-controls rejected=" + ",".join(sorted(set(rejected_reasons))))
    return controls + notes_controls, rejected + notes_rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", choices=("game", "docs"))
    group.add_argument("--self-test", choices=("game", "docs"))
    group.add_argument("--release-notes", type=Path, metavar="PATH")
    group.add_argument("--self-test-release-notes-v04", action="store_true")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--repo", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--rev", help="full immutable commit id for claim-boundary evidence")
    group.add_argument("--self-test-claim-boundaries", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test_release_notes_v04:
            positives, controls = run_self_test_release_notes_v04(args.repo.resolve(strict=True))
            require(positives > 0 and controls > 0, "release-notes-v04-self-test-empty")
            print(f"release-notes-v04 controls pass positives={positives} controls={controls}")
            return 0
        if args.self_test_claim_boundaries:
            require(args.rev is not None, "revision-required")
            positives, controls = run_self_test_claim_boundaries(
                args.repo.resolve(strict=True), args.rev)
            require(positives > 0 and controls > 0,
                    "claim-boundary-self-test-empty")
            print(f"adoption-claim-boundaries pass positives={positives} "
                  f"controls={controls} rev={args.rev}")
            return 0
        if args.release_notes is not None:
            root = args.root.resolve(strict=True)
            repo = args.repo.resolve(strict=True)
            checks = check_release_notes(args.release_notes, root, args.rev, repo)
            target_version = identity_at_revision(repo, args.rev)[0] if args.rev is not None else tree_identity(root)[0]
            print(json.dumps({
                "mode": "release-notes",
                "target": target_version,
                "checks": checks,
                "negative_controls": 0,
                "rejected_controls": 0,
                "positive_success": True,
            }, sort_keys=True))
            return 0
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
        require(negative_controls > 0 and negative_controls == rejected_controls,
                "self-test-control-inventory-invalid")
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
