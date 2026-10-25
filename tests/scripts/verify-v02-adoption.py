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
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
CLAIMS_SCRIPT = SCRIPT.parent / "verify-cgb-corpus-claims.py"
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
NOTICES = "THIRD_PARTY_NOTICES.md"
HEADER = "include/gabbaboy/gabbaboy.h"

PERF_ATTRIBUTION = "tests/baseline/perf-attribution-v1.json"


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


RELEASE_VERSION, LEDGER = tree_identity(DEFAULT_ROOT)
LEDGER_VERSION = LEDGER.rsplit("/v", 1)[1].removesuffix(".md")
ABSENCE_STATEMENT = "No CGB game-level evidence exists"
ABSENCE_SENTENCE = "No CGB game-level evidence exists."

# Surfaces whose symbols must resolve and whose claims must stay qualified.
PUBLIC_SURFACES = (
    README, NATIVE, SAVES, GAME_GUIDE, PROFILE, AUDIO, PREVIEW, RELEASE,
    LEDGER, NOTICES,
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
# A signing or notarization claim is allowed only in its negated form.
FALSE_SIGNING_CLAIM = re.compile(
    r"(?:(?<!un)(?<!not )signed\s+and\s+notarized|"
    r"(?<!not )notarized\s+and\s+signed|"
    r"\b(?:player|package|archive|binary|artifact|release|build)s?\s+"
    r"(?:is|are|was|were)\s+(?:both\s+)?(?:code[- ]?)?(?:signed|notarized)\b)",
    re.IGNORECASE,
)
FALSE_PUBLICATION_CLAIM = re.compile(
    r"\bv?0\.2\.0\s+(?:is|has\s+been|was)\s+(?:now\s+)?"
    r"(?:published|released|available|shipped|live)\b",
    re.IGNORECASE,
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
REBOUND_ATTRIBUTION = re.compile(r"\bRebound\b")

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
        ("`release-performance-receipt.json`", "performance-sidecar-missing"),
        ("`v02-fuzz-receipt.json`", "fuzz-sidecar-missing"),
        ("no fuzz campaign result is claimed by this document", "fuzz-limit-missing"),
        ("installed-prefix check", "installed-proof-missing"),
        ("downloaded-asset check", "downloaded-proof-missing"),
        (f"[support ledger](support/v{LEDGER_VERSION}.md)", "support-ledger-link-missing"),
        (ABSENCE_STATEMENT, "absence-statement-missing"),
        ("Physical CGB-E remains UNKNOWN/POLICY", "physical-cgb-limit-missing"),
        ("does not establish physical-device, perceptual, or hardware equivalence",
         "perceptual-output-limit-missing"),
        ("makes no publication claim for v0.2.0", "publication-limit-missing"),
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
    ("installed and downloaded product packages remain fixture-free",
     "product-package-distinction-missing"),
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
LEDGER_LINK = re.compile(r"\]\([^)\s]*docs/support/v" + re.escape(LEDGER_VERSION) + r"\.md[^)]*\)")
VERSION_TOKEN = re.compile(r"(?<![\w.])v?" + re.escape(RELEASE_VERSION) + r"(?![\w.])")


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


def prose(text: str) -> str:
    """Whitespace-normalized text without HTML comments or fenced code."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", " ", text,
                  flags=re.DOTALL | re.MULTILINE)
    return " ".join(text.split())


def comment_free(text: str) -> str:
    return re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)


_CLAIMS_MODULE = None


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


def unnegated(pattern: re.Pattern[str], text: str) -> bool:
    """True when a match is not directly negated ("no ..." / "not ...")."""
    for match in pattern.finditer(text):
        if re.search(r"\b(?:no|not|never)\s*$", text[max(0, match.start() - 8):match.start()],
                     re.IGNORECASE) is None:
            return True
    return False


def check_unqualified(relative: str, text: str) -> int:
    """Reject qualification claims that no shipped evidence supports."""
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
        require(pattern.search(text) is None, f"{reason}:{relative}")
    return len(checks) + 1


def check_phrases(relative: str, text: str,
                  required: tuple[tuple[str, str], ...]) -> int:
    for phrase, reason in required:
        require(phrase in text, f"{reason}:{relative}")
    return len(required)


def check_game(root: Path) -> int:
    text = prose(read_document(root, GAME_GUIDE))
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
    text = prose(read_document(root, README))
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
    text = prose(read_document(root, relative))
    checks = check_phrases(relative, text, REQUIRED[relative])
    return checks + check_unqualified(relative, text)


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
    checks = check_phrases(NOTICES, text, NOTICE_REQUIRED)
    require(REBOUND_ATTRIBUTION.search(raw) is None,
            f"rebound-attribution-present:{NOTICES}")
    checks += 1
    checks += check_unqualified(NOTICES, text)

    rows = {match["name"]: (match["manifest"], match["notice"])
            for match in NOTICE_ROW.finditer(comment_free(raw))}
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
    for match in NOTICE_INLINE_DIGEST.finditer(comment_free(raw)):
        target = root / match["path"]
        require(target.is_file(), f"notice-path-missing:{match['path']}")
        require(sha256_file(target) == match["digest"],
                f"notice-digest-stale:{match['path']}")
        checks += 1
    return checks


def perf_disclosure_percent(root: Path) -> str:
    """The head-versus-v0.2.0 instruction-count increase to disclose, one decimal: the maximum ratio over the
    three attribution ROMs and every repeat in the committed receipt (D-30, D-13)."""
    try:
        receipt = json.loads(read_bounded(root, PERF_ATTRIBUTION, 4 * MAX_DOCUMENT_BYTES))
        by_revision = {row["revision"]: row["ir"] for row in receipt["measurements"]}
        base, head = by_revision[receipt["selection"]["v020"]], by_revision[receipt["selection"]["head"]]
        ratios = [Fraction(h, b) for rom in head for b, h in zip(base[rom], head[rom])]
    except (ContractError, KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise ContractError("perf-attribution-receipt-unreadable") from error
    require(bool(ratios), "perf-attribution-receipt-empty")
    return f"{float((max(ratios) - 1) * 100):.1f}"


def check_release_notes(path: Path, root: Path = DEFAULT_ROOT) -> int:
    try:
        resolved = path.resolve(strict=True)
        if resolved.stat().st_size > MAX_NOTES_BYTES:
            raise ContractError("release-notes-too-large")
        raw = resolved.read_text(encoding="utf-8")
    except ContractError:
        raise
    except (OSError, UnicodeError) as error:
        raise ContractError("release-notes-unavailable") from error
    text = prose(raw)
    require(text, "release-notes-empty")
    checks = 0
    require(VERSION_TOKEN.search(text) is not None,
            f"release-notes-version-missing:{RELEASE_VERSION}")
    checks += 1
    require(ABSENCE_SENTENCE in text, "release-notes-absence-missing")
    checks += 1
    require(LEDGER_LINK.search(comment_free(raw)) is not None,
            "release-notes-ledger-link-missing")
    checks += 1
    require(re.search(r"unsigned and not notarized", text, re.IGNORECASE) is not None,
            "release-notes-unsigned-limit-missing")
    checks += 1
    percent = perf_disclosure_percent(root)
    require(re.search(r"(?<![\d.])\+" + re.escape(percent) + r"%", text) is not None and PERF_ATTRIBUTION in text,
            f"release-notes-perf-disclosure-missing:+{percent}%:{PERF_ATTRIBUTION}")
    checks += 1
    claims = claims_module()
    for pattern, reason in (
        (UNSUPPORTED_GAME_CLAIM, "unsupported-cgb-game-qualification"),
        (FALSE_SIGNING_CLAIM, "false-signing-or-notarization-claim"),
        (FALSE_FUZZ_CLAIM, "false-fuzz-campaign-claim"),
    ):
        require(pattern.search(text) is None, f"release-notes-{reason}")
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
    for match in NOTICE_INLINE_DIGEST.finditer(read_document(root, NOTICES)):
        relatives.add(match["path"])
    for relative in sorted(relatives):
        source = root / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


VALID_RELEASE_NOTES_TEMPLATE = """\
## v@VERSION@

GabbaBoy v@VERSION@ adds the selected CGB-CPU-E software model beside DMG-CPU-B.

- No CGB game-level evidence exists. The CGB test-ROM corpus is software-model
  evidence, not game acceptance. Physical CGB-E remains UNKNOWN/POLICY.
- The macOS player archive is unsigned and not notarized.
- Support scope and known limits: [support ledger](https://example.invalid/@LEDGER@).
- Instruction count: +@PERCENT@% versus v0.2.0 (receipt: tests/baseline/perf-attribution-v1.json).
"""


def run_self_test_release_notes() -> tuple[int, int]:
    percent = perf_disclosure_percent(DEFAULT_ROOT)
    VALID_RELEASE_NOTES = (VALID_RELEASE_NOTES_TEMPLATE.replace("@VERSION@", RELEASE_VERSION)
                           .replace("@LEDGER@", LEDGER).replace("@PERCENT@", percent))
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-notes-") as temp:
        notes = Path(temp) / "release-notes.md"
        write_lf(notes, VALID_RELEASE_NOTES)
        expect_pass(["--release-notes", str(notes)])
        mutations = (
            ("wrong-version", (RELEASE_VERSION, "0.1.0"),
             "release-notes-version-missing"),
            ("missing-absence", (ABSENCE_SENTENCE, ""),
             "release-notes-absence-missing"),
            ("comment-only-absence",
             (ABSENCE_SENTENCE, f"<!-- {ABSENCE_SENTENCE} -->"),
             "release-notes-absence-missing"),
            ("missing-ledger-link",
             (f"(https://example.invalid/{LEDGER})",
              "(https://example.invalid/docs/support/v0.1.0.md)"),
             "release-notes-ledger-link-missing"),
            ("missing-unsigned-limit", ("unsigned and not notarized", "ready"),
             "release-notes-unsigned-limit-missing"),
            ("missing-perf-percentage", (f"+{percent}%", "+0.0%"),
             "release-notes-perf-disclosure-missing"),
            ("missing-perf-receipt-path", (PERF_ATTRIBUTION, "the receipt"),
             "release-notes-perf-disclosure-missing"),
            ("comment-only-perf-disclosure",
             (f"- Instruction count: +{percent}% versus v0.2.0 (receipt: {PERF_ATTRIBUTION}).",
              f"<!-- Instruction count: +{percent}% ({PERF_ATTRIBUTION}) -->"),
             "release-notes-perf-disclosure-missing"),
            ("contrary-game-claim", None,
             "release-notes-unsupported-cgb-game-qualification"),
            ("false-signing-claim", None,
             "release-notes-false-signing-or-notarization-claim"),
        )
        for name, edit, reason in mutations:
            if name == "contrary-game-claim":
                changed = VALID_RELEASE_NOTES + "\nCGB game passes acceptance.\n"
            elif name == "false-signing-claim":
                changed = VALID_RELEASE_NOTES + "\nThe player is signed and notarized.\n"
            else:
                changed = VALID_RELEASE_NOTES.replace(edit[0], edit[1])
            require(changed != VALID_RELEASE_NOTES,
                    f"self-test-mutation-no-op:{name}")
            write_lf(notes, changed)
            expect_reject(["--release-notes", str(notes)], reason)
        write_lf(notes, VALID_RELEASE_NOTES)
        expect_pass(["--release-notes", str(notes)])
    return len(mutations), len(mutations)


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
    originals = {relative: read_document(root, relative)
                 for relative in PUBLIC_SURFACES}
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-docs-") as temp:
        test_root = Path(temp)
        copy_inputs(root, test_root)
        child_result(test_root, "docs")
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
             append("v0.2.0 has been published."),
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
    controls = len(mutations) + 4
    require(rejected == controls, "self-test-control-count-mismatch")
    notes_controls, notes_rejected = run_self_test_release_notes()
    return controls + notes_controls, rejected + notes_rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", choices=("game", "docs"))
    group.add_argument("--self-test", choices=("game", "docs"))
    group.add_argument("--release-notes", type=Path, metavar="PATH")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    try:
        if args.release_notes is not None:
            checks = check_release_notes(args.release_notes, args.root.resolve(strict=True))
            print(json.dumps({
                "mode": "release-notes",
                "target": RELEASE_VERSION,
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
