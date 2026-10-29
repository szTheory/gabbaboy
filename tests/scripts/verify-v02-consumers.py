#!/usr/bin/env python3
"""Verify relocated C and C++ consumers against installed GabbaBoy bytes."""
from __future__ import annotations

import argparse
import errno
import hashlib
import io
import json
import os
import pathlib
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import unicodedata
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve()
LANGUAGES = ("c", "cpp")
BEHAVIORS = (
    "profile_selection",
    "probe_info",
    "rgb555_frame_copy",
    "rtc_catch_up",
)
MAX_COMMAND_OUTPUT = 1_048_576
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 1000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 64 * 1024 * 1024
CANDIDATE_MANIFEST_SCHEMA = 1
# A sanitizer-built runner and package run several times slower; scale every bounded wait alike.
TIMEOUT_SCALE = 5 if os.environ.get("GBB_SANITIZER_LINK_OPTIONS") else 1
COMMAND_TIMEOUT_SECONDS = 90 * TIMEOUT_SCALE
TEST_PAUSE_ENV = "GABBABOY_V02_TEST_INSTALL_PAUSE"
TEST_EXTRACT_PAUSE_ENV = "GABBABOY_V02_TEST_EXTRACT_PAUSE"
# The release job extracts untrusted archives on windows-2022. There a backslash is a path separator, a
# colon in a component can select an alternate data stream or another volume, and these names are device
# files whatever their extension, so all of them must be refused before anything is created. CONIN$ and CONOUT$
# are console device names too, and Windows also treats the superscript digits in COM and LPT names as devices, so
# the stem is compared after NFKC normalisation and upper-casing (superscript one folds to COM1).
WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"]
    + [f"COM{index}" for index in range(1, 10)]
    + [f"LPT{index}" for index in range(1, 10)]
)
_ACTIVE_PROCESSES: list[subprocess.Popen[str]] = []


class ContractError(Exception):
    """A named failure in the installed-consumer contract."""


class InterruptedRun(Exception):
    """Raised after the active subprocess tree receives a stop signal."""


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ContractError(reason)


def within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def run_command(command: list[str], *, cwd: Path, env: dict[str, str] | None = None,
                timeout: int = COMMAND_TIMEOUT_SECONDS,
                rejection: str) -> tuple[str, str]:
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=(os.name != "nt"),
        )
    except OSError as error:
        raise ContractError(f"{rejection}:start-failed:{type(error).__name__}") from error
    _ACTIVE_PROCESSES.append(process)
    try:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            terminate_process(process)
            process.communicate()
            raise ContractError(f"{rejection}:timeout") from error
        except InterruptedRun:
            terminate_process(process)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                terminate_process(process, force=True)
                process.communicate()
            raise
    finally:
        if process in _ACTIVE_PROCESSES:
            _ACTIVE_PROCESSES.remove(process)
    if len(stdout.encode("utf-8")) + len(stderr.encode("utf-8")) > MAX_COMMAND_OUTPUT:
        raise ContractError(f"{rejection}:output-limit")
    if process.returncode != 0:
        tail = " ".join((stdout + " " + stderr).split())[-500:]
        raise ContractError(f"{rejection}:exit-{process.returncode}" + (f":{tail}" if tail else ""))
    return stdout, stderr


def terminate_process(process: subprocess.Popen[str], *, force: bool = False) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.kill() if force else process.terminate()
        else:
            os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass


def install_signal_handlers() -> None:
    def stop(signum: int, _frame: object) -> None:
        for process in tuple(_ACTIVE_PROCESSES):
            terminate_process(process)
        raise InterruptedRun(f"signal-{signum}")

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, stop)


def maybe_test_pause(marker_path: Path, temp_root: Path, staged_prefix: Path) -> None:
    """A bounded, private self-test pause lets the harness interrupt a real --run."""
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    staged_file_count = sum(1 for path in staged_prefix.rglob("*") if path.is_file())
    marker_path.write_text(
        json.dumps({"temp_root": str(temp_root), "staged_file_count": staged_file_count}) + "\n",
        encoding="utf-8",
    )
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        time.sleep(0.05)
    raise ContractError("test-pause-timeout")


def package_configs(prefix: Path) -> list[Path]:
    return sorted(prefix.rglob("GabbaBoyConfig.cmake"))


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def hash_package(prefix: Path) -> str:
    digest = hashlib.sha256()
    entries = sorted(prefix.rglob("*"), key=lambda item: item.relative_to(prefix).as_posix())
    file_count = 0
    for path in entries:
        metadata = path.lstat()
        if path.is_symlink() or not path.is_file():
            if path.is_dir() and not path.is_symlink():
                continue
            raise ContractError("package-special-file")
        relative = path.relative_to(prefix).as_posix().encode("utf-8")
        content_hash = bytes.fromhex(hash_file(path))
        digest.update(relative + b"\0" + content_hash + b"\n")
        file_count += 1
    need(file_count > 0, "package-empty")
    return digest.hexdigest()


def hash_archive(archive: Path) -> str:
    need(archive.is_file() and not archive.is_symlink(), "archive-file-invalid")
    try:
        size = archive.stat().st_size
    except OSError as error:
        raise ContractError("archive-unreadable") from error
    need(size <= MAX_ARCHIVE_BYTES, "archive-too-large")
    return hash_file(archive)


def candidate_source_revision(project_root: Path) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ContractError("candidate-source-unavailable") from error
    revision = result.stdout.strip()
    need(result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", revision) is not None,
         "candidate-source-unavailable")
    return revision


def make_candidate_manifest(source_sha: str, archive_sha: str,
                            build_receipt_sha: str) -> dict[str, object]:
    need(re.fullmatch(r"[0-9a-f]{40,64}", source_sha) is not None,
         "candidate-manifest-source-invalid")
    need(re.fullmatch(r"[0-9a-f]{64}", archive_sha) is not None,
         "candidate-manifest-archive-invalid")
    need(re.fullmatch(r"[0-9a-f]{64}", build_receipt_sha) is not None,
         "candidate-manifest-build-invalid")
    return {
        "schema_version": CANDIDATE_MANIFEST_SCHEMA,
        "candidate_source_sha": source_sha,
        "archive_sha256": archive_sha,
        "build_receipt_sha256": build_receipt_sha,
    }


def write_candidate_manifest(archive: Path, source_sha: str, build_receipt: Path, output: Path) -> dict[str, object]:
    """Bind a candidate archive to its source and build receipt, for a workflow that built both itself.

    The release rehearsal builds its archive in the same job, so it has no validator-supplied manifest.
    A JSON build receipt that names a source or an asset digest must agree with the inputs; any other
    receipt (for example a CMake cache) is bound by its digest alone, as --run does."""
    need(re.fullmatch(r"[0-9a-f]{40,64}", source_sha) is not None, "candidate-manifest-source-invalid")
    archive_sha = hash_archive(archive)
    need(build_receipt.is_file() and not build_receipt.is_symlink(), "candidate-build-receipt-missing")
    try:
        receipt_bytes = build_receipt.read_bytes()
    except OSError as error:
        raise ContractError("candidate-build-receipt-missing") from error
    need(0 < len(receipt_bytes) <= 16_777_216, "candidate-build-receipt-size-invalid")
    try:
        parsed = json.loads(receipt_bytes.decode("utf-8"))
    except (UnicodeError, ValueError):
        parsed = None
    if isinstance(parsed, dict):
        need(parsed.get("source_sha", source_sha) == source_sha, "candidate-build-receipt-source-mismatch")
        need(parsed.get("asset_sha256", archive_sha) == archive_sha, "candidate-build-receipt-asset-mismatch")
    manifest = make_candidate_manifest(source_sha, archive_sha, hashlib.sha256(receipt_bytes).hexdigest())
    try:
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    except FileExistsError as error:
        raise ContractError("candidate-manifest-exists") from error
    return manifest


def read_candidate_manifest(path: Path) -> tuple[dict[str, object], str]:
    need(path.is_file() and not path.is_symlink(), "candidate-manifest-missing")
    try:
        content = path.read_bytes()
    except OSError as error:
        raise ContractError("candidate-manifest-unreadable") from error
    need(0 < len(content) <= 65_536, "candidate-manifest-size-invalid")
    try:
        manifest = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError) as error:
        raise ContractError("candidate-manifest-invalid") from error
    need(isinstance(manifest, dict), "candidate-manifest-invalid")
    need(type(manifest.get("schema_version")) is int and
         manifest["schema_version"] == CANDIDATE_MANIFEST_SCHEMA,
         "candidate-manifest-version-unsupported")
    source_sha = manifest.get("candidate_source_sha")
    archive_sha = manifest.get("archive_sha256")
    build_sha = manifest.get("build_receipt_sha256")
    need(isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40,64}", source_sha) is not None,
         "candidate-manifest-source-invalid")
    need(isinstance(archive_sha, str) and re.fullmatch(r"[0-9a-f]{64}", archive_sha) is not None,
         "candidate-manifest-archive-invalid")
    need(isinstance(build_sha, str) and re.fullmatch(r"[0-9a-f]{64}", build_sha) is not None,
         "candidate-manifest-build-invalid")
    return manifest, hashlib.sha256(content).hexdigest()


def windows_unsafe_member(raw_name: str, parts: tuple[str, ...]) -> bool:
    if "\\" in raw_name:
        return True
    for part in parts:
        if ":" in part or part.endswith((".", " ")):
            return True
        if unicodedata.normalize("NFKC", part.split(".", 1)[0].rstrip(" ")).upper() in WINDOWS_RESERVED_NAMES:
            return True
    return False


def safe_extract_archive(archive: Path, destination: Path) -> Path:
    need(not destination.exists() and not destination.is_symlink(), "extract-destination-exists")
    need(archive.is_file() and not archive.is_symlink(), "archive-file-invalid")
    try:
        archive_size = archive.stat().st_size
    except OSError as error:
        raise ContractError("archive-unreadable") from error
    need(archive_size > 0, "archive-empty")
    need(archive_size <= MAX_ARCHIVE_BYTES, "archive-too-large")
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with tarfile.open(archive, "r:gz") as bundle:
            members: list[tuple[tarfile.TarInfo, tuple[str, ...]]] = []
            seen: set[str] = set()
            total_size = 0
            for member in bundle:
                need(len(members) < MAX_ARCHIVE_ENTRIES, "archive-too-many-entries")
                name = pathlib.PurePosixPath(member.name)
                parts = tuple(part for part in name.parts if part not in ("", "."))
                need(not name.is_absolute() and bool(parts) and ".." not in parts and
                     not windows_unsafe_member(member.name, parts), "archive-path-unsafe")
                normalized = "/".join(parts)
                need(normalized not in seen, "archive-duplicate-path")
                seen.add(normalized)
                need(member.isdir() or member.isreg(), "archive-special-file")
                need(member.size >= 0, "archive-member-size-invalid")
                total_size += member.size
                need(total_size <= MAX_ARCHIVE_UNCOMPRESSED_BYTES, "archive-uncompressed-too-large")
                members.append((member, parts))
            need(bool(members), "archive-empty")
            destination.mkdir()
            created = True
            extracted_file = False
            pause_value = os.environ.get(TEST_EXTRACT_PAUSE_ENV)
            for member, parts in members:
                target = destination.joinpath(*parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                need(source is not None, "archive-member-unreadable")
                with source, target.open("xb") as output:
                    remaining = member.size
                    while remaining:
                        chunk = source.read(min(1024 * 1024, remaining))
                        need(bool(chunk), "archive-member-truncated")
                        output.write(chunk)
                        remaining -= len(chunk)
                target.chmod(member.mode & 0o777 & ~0o6000)
                if not extracted_file:
                    extracted_file = True
                    if pause_value:
                        maybe_test_pause(Path(pause_value), destination.parent, destination)
        return destination
    except InterruptedRun:
        if created:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    except ContractError:
        if created:
            shutil.rmtree(destination, ignore_errors=True)
        raise
    except (OSError, EOFError, tarfile.TarError, ValueError) as error:
        if created:
            shutil.rmtree(destination, ignore_errors=True)
        raise ContractError("archive-invalid") from error


def create_product_archive(prefix: Path, archive: Path) -> str:
    hash_package(prefix)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "w:gz") as bundle:
        for path in sorted(prefix.rglob("*"), key=lambda item: item.relative_to(prefix).as_posix()):
            bundle.add(path, arcname=path.relative_to(prefix).as_posix(), recursive=False)
    return hash_archive(archive)


def verify_prefix(prefix_value: Path, project_root: Path) -> tuple[Path, Path, str]:
    if not prefix_value.exists():
        raise ContractError("prefix-missing")
    if not prefix_value.is_dir():
        raise ContractError("prefix-not-directory")
    prefix = prefix_value.resolve(strict=True)
    root = project_root.resolve(strict=True)
    build = (root / "build").resolve(strict=False)
    need(not within(prefix, root) and not within(prefix, build), "prefix-not-relocated")
    configs = package_configs(prefix)
    need(len(configs) == 1, f"package-config-count:expected-one-found-{len(configs)}")
    config = configs[0].resolve(strict=True)
    header = prefix / "include" / "gabbaboy" / "gabbaboy.h"
    tracer = prefix / "share" / "gabbaboy" / "fixtures" / "tracer" / "tracer.gb"
    runner = prefix / "bin" / ("gabbaboy-runner.exe" if os.name == "nt" else "gabbaboy-runner")
    for required in (header, tracer, runner):
        need(required.is_file() and not required.is_symlink(), "package-file-missing")
    config_dir = config.parent
    for metadata in sorted(config_dir.rglob("*.cmake")):
        text = metadata.read_text(encoding="utf-8", errors="strict")
        need(str(root) not in text and str(build) not in text, "package-metadata-leaks-source-path")
    return prefix, config, hash_package(prefix)


def cmake_executable() -> str:
    executable = shutil.which("cmake")
    need(executable is not None, "cmake-unavailable")
    return executable


def clean_package_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in tuple(environment):
        if name in {
            "CMAKE_PREFIX_PATH", "CMAKE_FRAMEWORK_PATH", "CMAKE_APPBUNDLE_PATH",
            "GabbaBoy_DIR", "GabbaBoy_ROOT", "GBB_INSTALL_PREFIX",
        }:
            environment.pop(name, None)
    return environment


def validate_behavior_sources(project_root: Path) -> None:
    for language in LANGUAGES:
        source = project_root / "tests" / "consumers" / language / ("main.c" if language == "c" else "main.cpp")
        need(source.is_file(), f"consumer-source-missing:{language}")
        text = source.read_text(encoding="utf-8")
        for token in ("GBB_PROFILE_CGB_CPU_E", "gbb_probe_rom(", "gbb_get_info(",
                      "gbb_copy_frame_rgb555(", "gbb_rtc_catch_up("):
            need(token in text, f"consumer-behavior-missing:{language}:{token}")
        for call in ("cgb_api_smoke()", "rtc_api_smoke()"):
            need(call in text, f"consumer-behavior-not-invoked:{language}:{call}")


def compiler_identity(build_dir: Path, language: str) -> dict[str, str]:
    cache = build_dir / "CMakeCache.txt"
    values: dict[str, str] = {}
    if cache.is_file():
        for line in cache.read_text(encoding="utf-8", errors="replace").splitlines():
            for key in (f"CMAKE_{'C' if language == 'c' else 'CXX'}_COMPILER_ID",
                        f"CMAKE_{'C' if language == 'c' else 'CXX'}_COMPILER_VERSION"):
                if line.startswith(key + ":") and "=" in line:
                    values[key] = line.split("=", 1)[1]
    prefix = "CMAKE_C_COMPILER" if language == "c" else "CMAKE_CXX_COMPILER"
    identifier = values.get(prefix + "_ID", "")
    version = values.get(prefix + "_VERSION", "")
    if not identifier or not version:
        compiler_file_name = "CMakeCCompiler.cmake" if language == "c" else "CMakeCXXCompiler.cmake"
        compiler_files = sorted((build_dir / "CMakeFiles").glob(f"*/{compiler_file_name}"))
        if compiler_files:
            text = compiler_files[0].read_text(encoding="utf-8", errors="replace")
            identifier_match = re.search(rf'set\({prefix}_ID "([^"]+)"\)', text)
            version_match = re.search(rf'set\({prefix}_VERSION "([^"]+)"\)', text)
            identifier = identifier or (identifier_match.group(1) if identifier_match else "")
            version = version or (version_match.group(1) if version_match else "")
    need(identifier != "" and version != "", f"compiler-identity-missing:{language}")
    return {"id": identifier, "version": version}


CONFIGURATION_NAMES = {"debug": "Debug", "release": "Release",
                       "relwithdebinfo": "RelWithDebInfo", "minsizerel": "MinSizeRel"}


def installed_configuration(prefix: Path) -> str:
    """Multi-config generators (the Windows default) need the installed package's configuration.

    Single-config generators ignore it, so it is only derived on Windows from the one
    GabbaBoyTargets-<config>.cmake the package installed; anything else stays empty.
    """
    if os.name != "nt":
        return ""
    names = sorted({
        path.stem.split("-", 1)[1].lower()
        for path in prefix.rglob("GabbaBoyTargets-*.cmake")
    })
    need(len(names) == 1 and names[0] in CONFIGURATION_NAMES, "package-configuration-ambiguous")
    return CONFIGURATION_NAMES[names[0]]


def run_consumer(language: str, prefix: Path, config: Path, build_dir: Path,
                 project_root: Path, cmake: str) -> tuple[dict[str, object], dict[str, str]]:
    language_build = build_dir / language
    language_build.parent.mkdir(parents=True, exist_ok=True)
    environment = clean_package_environment()
    script = project_root / "cmake" / "RunInstalledConsumer.cmake"
    need(script.is_file(), "installed-consumer-driver-missing")
    command = [
        cmake,
        f"-DGBB_INSTALL_PREFIX={prefix}",
        f"-DGBB_CONSUMER_SOURCE={project_root / 'tests' / 'consumers' / language}",
        f"-DGBB_CONSUMER_BINARY={language_build}",
        f"-DGBB_LANGUAGE={language}",
        f"-DGBB_EXECUTABLE_SUFFIX={'.exe' if os.name == 'nt' else ''}",
        f"-DGBB_CONFIGURATION={installed_configuration(prefix)}",
    ]
    # A sanitizer-built package references the sanitizer runtime; the consumer must link it too,
    # or the linker emits one undefined-reference line per instrumented function.
    sanitizer_link = os.environ.get("GBB_SANITIZER_LINK_OPTIONS", "")
    if sanitizer_link:
        command.append(f"-DGBB_SANITIZER_LINK_OPTIONS={sanitizer_link}")
    command += ["-P", str(script)]
    stdout, _stderr = run_command(command, cwd=build_dir, env=environment,
                                  rejection=f"consumer-failed:{language}")
    compiler = compiler_identity(language_build, language)
    result: dict[str, object] = {
        "status": "passed",
        "exit_code": 0,
        "build_isolated": True,
        "behavioral_checks": list(BEHAVIORS),
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
    }
    return result, compiler


def source_identity(prefix: Path, project_root: Path) -> tuple[str, bool]:
    runner = prefix / "bin" / ("gabbaboy-runner.exe" if os.name == "nt" else "gabbaboy-runner")
    cases = project_root / "tests" / "acceptance" / "cases.txt"
    need(cases.is_file(), "source-identity-input-missing")
    stdout, _stderr = run_command(
        [str(runner), "--acceptance", str(cases), "--case", "libbet", "--receipt"],
        cwd=project_root,
        env=clean_package_environment(),
        timeout=45 * TIMEOUT_SCALE,
        rejection="source-identity-probe-failed",
    )
    match = re.search(r"\bcore_revision=([0-9a-f]{40,64})\s+build_qualified=(true|false)\b", stdout)
    need(match is not None, "source-identity-not-reported")
    return match.group(1), match.group(2) == "true"


def configured_build_dir(project_root: Path) -> Path:
    """The configured build tree: CTest names its own (for example build-asan) through GBB_TEST_BUILD_DIR."""
    override = os.environ.get("GBB_TEST_BUILD_DIR")
    return Path(override) if override else project_root / "build"


def install_package(project_root: Path, temp_root: Path, cmake: str) -> Path:
    build = configured_build_dir(project_root)
    need(build.is_dir(), "configured-build-missing")
    staged = temp_root / "staged-prefix"
    relocated = temp_root / "relocated-prefix"
    run_command([cmake, "--install", str(build), "--prefix", str(staged)],
                cwd=project_root, env=clean_package_environment(), rejection="package-install-failed")
    need(staged.is_dir(), "package-install-produced-no-prefix")
    marker = os.environ.get(TEST_PAUSE_ENV)
    if marker:
        maybe_test_pause(Path(marker), temp_root, staged)
    staged.rename(relocated)
    need(not within(relocated.resolve(), project_root.resolve()), "installed-prefix-not-isolated")
    return relocated


def make_receipt(prefix: Path, config: Path, package_hash: str, project_root: Path,
                 candidate_manifest: dict[str, object], candidate_manifest_sha: str,
                 archive_sha: str, *, prefix_origin: str, run_id: str,
                 temp_root: Path) -> dict[str, object]:
    temp_root.mkdir(parents=True, exist_ok=True)
    validate_behavior_sources(project_root)
    cmake = cmake_executable()
    results: dict[str, object] = {}
    compiler: dict[str, object] = {}
    for language in LANGUAGES:
        result, identity = run_consumer(language, prefix, config, temp_root, project_root, cmake)
        results[language] = result
        compiler[language] = identity
    source_sha, build_qualified = source_identity(prefix, project_root)
    need(hash_package(prefix) == package_hash, "package-changed-during-consumer-run")
    api_behaviors = {
        behavior: {language: "passed" for language in LANGUAGES}
        for behavior in BEHAVIORS
    }
    return {
        "schema_version": 2,
        "result": "passed",
        "source_sha": source_sha,
        "runner_reported_source_sha": source_sha,
        "build_qualified": build_qualified,
        "candidate_source_sha": candidate_manifest["candidate_source_sha"],
        "candidate_manifest_sha256": candidate_manifest_sha,
        "candidate_build_receipt_sha256": candidate_manifest["build_receipt_sha256"],
        "archive_sha256": archive_sha,
        "installed_tree_sha256": package_hash,
        "package_sha256": package_hash,
        "compiler": compiler,
        "api_behaviors": api_behaviors,
        "isolated_prefix": True,
        "prefix_origin": prefix_origin,
        "build_run_id": run_id,
        "results": results,
    }


def _windows_process_is_alive(pid: int) -> bool | None:
    """os.kill(pid, 0) is not a liveness probe on Windows (signal 0 is CTRL_C_EVENT); ask the kernel."""
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    process_query_limited_information = 0x1000
    error_access_denied, error_invalid_parameter, still_active = 5, 87, 259
    handle = kernel32.OpenProcess(process_query_limited_information, 0, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == error_invalid_parameter:
            return False
        return True if error == error_access_denied else None
    try:
        code = ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return None
        return code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def process_is_alive(pid: int) -> bool | None:
    if pid <= 0:
        return None
    if os.name == "nt":
        return _windows_process_is_alive(pid)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError as error:
        if getattr(error, "errno", None) == errno.ESRCH:
            return False
        return None


def stale_lock(path: Path) -> bool:
    try:
        before = path.read_bytes()
        data = json.loads(before.decode("utf-8"))
        pid = data.get("pid")
        if not isinstance(pid, int):
            return False
        alive = process_is_alive(pid)
        if alive is not False:
            return False
        if path.read_bytes() != before:
            return False
        path.unlink()
        return True
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return False


class OutputReservation:
    def __init__(self, value: Path):
        self.value = value
        self.output: Path | None = None
        self.lock: Path | None = None
        self.token = uuid.uuid4().hex

    def __enter__(self) -> Path:
        raw = self.value.expanduser()
        parent = raw.parent.resolve(strict=True)
        need(raw.name not in ("", ".", ".."), "output-path-invalid")
        output = parent / raw.name
        lock = Path(str(output) + ".lock")
        need(not output.exists() and not output.is_symlink(), "receipt-exists")
        for attempt in range(2):
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                self.output = output
                self.lock = lock
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(json.dumps({"pid": os.getpid(), "token": self.token}) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                break
            except FileExistsError:
                if attempt == 0 and stale_lock(lock):
                    continue
                raise ContractError("output-owned")
            except OSError:
                self._release_owned_lock()
                raise
        if output.exists() or output.is_symlink():
            self._release_owned_lock()
            raise ContractError("receipt-exists")
        return output

    def _release_owned_lock(self) -> None:
        if self.lock is None:
            return
        try:
            current = json.loads(self.lock.read_text(encoding="utf-8"))
            if current.get("token") == self.token:
                self.lock.unlink()
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    def publish(self, receipt: dict[str, object]) -> None:
        need(self.output is not None, "output-reservation-missing")
        parent = self.output.parent
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(prefix=f".{self.output.name}.", suffix=".tmp", dir=parent)
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(receipt, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, self.output)
            except FileExistsError as error:
                raise ContractError("receipt-exists") from error
            temporary.unlink()
            try:
                directory_fd = os.open(parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                pass
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self._release_owned_lock()


def run_driver(*, project_root: Path, output_path: Path, prefix_value: Path | None,
               archive_value: Path | None, candidate_manifest_value: Path | None,
               fresh_install: bool, platform_id: str | None = None,
               host_smoke: dict[str, str] | None = None) -> dict[str, object]:
    run_id = uuid.uuid4().hex
    reservation = OutputReservation(output_path)
    with reservation as output:
        with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-consumers-") as temp_name:
            temp_root = Path(temp_name)
            if fresh_install:
                cmake = cmake_executable()
                prefix = install_package(project_root, temp_root, cmake)
                archive = temp_root / "candidate.tar.gz"
                archive_sha = create_product_archive(prefix, archive)
                build_cache = configured_build_dir(project_root) / "CMakeCache.txt"
                need(build_cache.is_file(), "candidate-build-manifest-unavailable")
                candidate_manifest = make_candidate_manifest(
                    candidate_source_revision(project_root), archive_sha, hash_file(build_cache))
                manifest_bytes = (json.dumps(candidate_manifest, sort_keys=True) + "\n").encode("utf-8")
                candidate_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
            else:
                need(archive_value is not None, "candidate-manifest-required")
                need(candidate_manifest_value is not None, "candidate-manifest-required")
                archive = archive_value.expanduser()
                manifest_path = candidate_manifest_value.expanduser()
                candidate_manifest, candidate_manifest_sha = read_candidate_manifest(manifest_path)
                archive_sha = hash_archive(archive)
                need(archive_sha == candidate_manifest["archive_sha256"],
                     "candidate-archive-digest-mismatch")

            extracted = safe_extract_archive(archive, temp_root / "archive-prefix")
            resolved_prefix, config, package_hash = verify_prefix(extracted, project_root)
            if prefix_value is not None:
                supplied_prefix, _supplied_config, supplied_hash = verify_prefix(prefix_value, project_root)
                need(supplied_hash == package_hash, "installed-tree-mismatch")
                prefix_origin = "candidate-archive-and-relocated-prefix"
            elif fresh_install:
                prefix_origin = "fresh-install-relocated"
            else:
                prefix_origin = "candidate-archive-relocated"
            receipt = make_receipt(
                resolved_prefix, config, package_hash, project_root,
                candidate_manifest, candidate_manifest_sha, archive_sha,
                prefix_origin=prefix_origin, run_id=run_id,
                temp_root=temp_root / "consumer-builds",
            )
            if platform_id is not None:
                receipt["platform"] = platform_id
                receipt["host_smoke"] = host_smoke
        reservation.publish(receipt)
    return receipt


def read_host_smoke(path: Path, platform_id: str) -> dict[str, str]:
    need(path.is_file() and not path.is_symlink(), "host-smoke-receipt-missing")
    try:
        content = path.read_bytes()
        need(0 < len(content) <= 4096, "host-smoke-receipt-size-invalid")
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ContractError("host-smoke-receipt-invalid") from error
    if platform_id == "windows-x64":
        need(value == {"result": "not-applicable"}, "host-smoke-result-invalid")
    else:
        need(value == {"result": "passed", "continuation": "01,02", "preload": "42"},
             "host-smoke-result-invalid")
    return value


def parse_receipt(result: subprocess.CompletedProcess[str], path: Path) -> dict[str, object]:
    if result.returncode != 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}


class ConsumerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gabbaboy-v02-self-test-")
        cls.test_root = Path(cls.temporary.name)
        cls.prefix = cls.test_root / "relocated-prefix"
        staged = cls.test_root / "staged-prefix"
        run_command(
            [cmake_executable(), "--install", str(configured_build_dir(ROOT)), "--prefix", str(staged)],
            cwd=ROOT,
            env=clean_package_environment(),
            rejection="self-test-package-install-failed",
        )
        staged.rename(cls.prefix)
        cls.archive = cls.test_root / "candidate.tar.gz"
        archive_sha = create_product_archive(cls.prefix, cls.archive)
        cls.candidate_source_sha = candidate_source_revision(ROOT)
        cls.candidate_manifest = cls.test_root / "candidate-manifest.json"
        manifest = make_candidate_manifest(cls.candidate_source_sha, archive_sha, "a" * 64)
        cls.candidate_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def run_cli(self, args: list[str], *, script: Path = SCRIPT,
                env: dict[str, str] | None = None,
                cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(script), *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120 * TIMEOUT_SCALE,
            check=False,
        )

    def assert_rejected(self, result: subprocess.CompletedProcess[str], reason: str,
                        output: Path) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"verify-v02-consumers: rejected:{reason}", result.stderr)
        self.assertFalse(output.exists(), "a rejected run must not publish a success receipt")

    def candidate_args(self, prefix: Path, *, archive: Path | None = None,
                       manifest: Path | None = None) -> list[str]:
        return ["--prefix", str(prefix), "--archive", str(archive or self.archive),
                "--candidate-manifest", str(manifest or self.candidate_manifest)]

    def test_relocated_prefix_runs_both_consumers(self) -> None:
        output = self.test_root / "positive.json"
        result = self.run_cli([*self.candidate_args(self.prefix), "--output", str(output)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = parse_receipt(result, output)
        self.assertEqual(receipt.get("result"), "passed")
        self.assertEqual(receipt.get("schema_version"), 2)
        self.assertEqual(set(receipt.get("results", {})), set(LANGUAGES))
        self.assertTrue(receipt.get("isolated_prefix"))
        self.assertEqual(receipt.get("candidate_source_sha"), self.candidate_source_sha)
        self.assertEqual(receipt.get("archive_sha256"), hash_file(self.archive))
        self.assertEqual(receipt.get("installed_tree_sha256"), receipt.get("package_sha256"))
        self.assertEqual(receipt.get("runner_reported_source_sha"), receipt.get("source_sha"))
        self.assertEqual(receipt.get("api_behaviors"), {
            behavior: {language: "passed" for language in LANGUAGES} for behavior in BEHAVIORS
        })

    def test_missing_prefix_is_rejected(self) -> None:
        output = self.test_root / "missing-prefix.json"
        missing = self.test_root / "does-not-exist"
        result = self.run_cli([*self.candidate_args(missing), "--output", str(output)])
        self.assert_rejected(result, "prefix-missing", output)

    def test_removed_package_config_is_rejected(self) -> None:
        broken = self.test_root / "without-config"
        shutil.copytree(self.prefix, broken)
        configs = package_configs(broken)
        self.assertEqual(len(configs), 1)
        configs[0].unlink()
        output = self.test_root / "missing-config.json"
        result = self.run_cli([*self.candidate_args(broken), "--output", str(output)])
        self.assert_rejected(result, "package-config-count:expected-one-found-0", output)

    def test_forged_runner_source_does_not_qualify_changed_package(self) -> None:
        expected_source = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", check=True,
        ).stdout.strip()
        archive = self.test_root / "candidate.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            for path in sorted(self.prefix.rglob("*")):
                bundle.add(path, arcname=path.relative_to(self.prefix).as_posix(), recursive=False)
        candidate_manifest = self.test_root / "candidate-manifest.json"
        candidate_manifest.write_text(json.dumps({
            "schema_version": 1,
            "candidate_source_sha": expected_source,
            "archive_sha256": hash_file(archive),
            "build_receipt_sha256": "a" * 64,
        }, sort_keys=True) + "\n", encoding="utf-8")

        forged = self.test_root / "forged-source-package"
        shutil.copytree(self.prefix, forged)
        header = forged / "include" / "gabbaboy" / "gabbaboy.h"
        header.write_bytes(header.read_bytes() + b"\n/* changed package bytes */\n")
        fake_runner_source = self.test_root / "fake-runner-source"
        fake_runner_source.mkdir()
        (fake_runner_source / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.25)\n"
            "project(ForgedRunner C)\n"
            "add_executable(gabbaboy-runner fake.c)\n",
            encoding="utf-8",
        )
        (fake_runner_source / "fake.c").write_text(
            "#include <stdio.h>\n"
            f'int main(void) {{ puts("core_revision={expected_source} build_qualified=true"); return 0; }}\n',
            encoding="utf-8",
        )
        fake_runner_build = self.test_root / "fake-runner-build"
        cmake = cmake_executable()
        run_command([cmake, "-S", str(fake_runner_source), "-B", str(fake_runner_build)],
                    cwd=ROOT, rejection="self-test-fake-runner-configure-failed")
        run_command([cmake, "--build", str(fake_runner_build), "--parallel", "2"],
                    cwd=ROOT, rejection="self-test-fake-runner-build-failed")
        runner_name = "gabbaboy-runner.exe" if os.name == "nt" else "gabbaboy-runner"
        fake_runner = next(path for path in fake_runner_build.rglob(runner_name) if path.is_file())
        shutil.copy2(fake_runner, forged / "bin" / runner_name)
        reported_source, _qualified = source_identity(forged, ROOT)
        self.assertEqual(reported_source, expected_source)
        self.assertNotEqual(hash_package(forged), hash_package(self.prefix))
        self.assertTrue(candidate_manifest.is_file())

        output = self.test_root / "forged-source.json"
        result = self.run_cli([
            *self.candidate_args(forged, archive=archive, manifest=candidate_manifest),
            "--output", str(output),
        ])
        self.assert_rejected(result, "installed-tree-mismatch", output)

    def write_manifest(self, out: Path, *, archive: Path | None = None, source: str | None = None,
                       receipt: Path | None = None) -> subprocess.CompletedProcess[str]:
        return self.run_cli([
            "--write-candidate-manifest", str(out), "--archive", str(archive or self.archive),
            "--source-sha", source or self.candidate_source_sha,
            # test_forged_runner_source rewrites the shared archive, so bind the archive as it is now.
            "--build-receipt", str(receipt or self.json_receipt()),
        ])

    def test_workflow_command_without_candidate_manifest_is_rejected(self) -> None:
        # The release rehearsal (run 39634983581) called the verifier with only --prefix and --output.
        output = self.test_root / "no-manifest.json"
        result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)])
        self.assert_rejected(result, "candidate-manifest-required", output)

    def test_written_manifest_binds_archive_and_build_receipt_and_qualifies(self) -> None:
        manifest = self.test_root / "written-manifest.json"
        receipt = self.json_receipt()
        written = self.write_manifest(manifest, receipt=receipt)
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        loaded, _digest = read_candidate_manifest(manifest)
        self.assertEqual(loaded["archive_sha256"], hash_file(self.archive))
        self.assertEqual(loaded["build_receipt_sha256"], hash_file(receipt))
        self.assertEqual(loaded["candidate_source_sha"], self.candidate_source_sha)
        output = self.test_root / "written-qualifies.json"
        result = self.run_cli([*self.candidate_args(self.prefix, manifest=manifest), "--output", str(output)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(parse_receipt(result, output).get("result"), "passed")

    def test_manifest_writer_rejects_unbound_inputs(self) -> None:
        cases = {
            "candidate-manifest-source-invalid": dict(source="not-a-sha"),
            "candidate-build-receipt-missing": dict(receipt=self.test_root / "absent-receipt.json"),
            "candidate-build-receipt-asset-mismatch": dict(receipt=self.json_receipt(asset="0" * 64)),
            "candidate-build-receipt-source-mismatch": dict(receipt=self.json_receipt(source="1" * 40)),
            "archive-file-invalid": dict(archive=self.test_root / "absent.tar.gz"),
        }
        for reason, options in cases.items():
            out = self.test_root / f"writer-{reason}.json"
            result = self.write_manifest(out, **options)
            self.assertNotEqual(result.returncode, 0, reason)
            self.assertIn(f"verify-v02-consumers: rejected:{reason}", result.stderr, reason)
            self.assertFalse(out.exists(), f"{reason} must not leave a manifest")
        existing = self.test_root / "writer-existing.json"
        existing.write_text("keep\n", encoding="utf-8")
        result = self.write_manifest(existing)
        self.assertIn("verify-v02-consumers: rejected:candidate-manifest-exists", result.stderr)
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")

    def json_receipt(self, *, asset: str | None = None, source: str | None = None) -> Path:
        path = self.test_root / f"receipt-{asset or 'ok'}-{source or 'ok'}.json"
        path.write_text(json.dumps({"source_sha": source or self.candidate_source_sha,
                                    "asset_sha256": asset or hash_file(self.archive)}), encoding="utf-8")
        return path

    def test_changed_archive_does_not_match_stale_candidate_manifest(self) -> None:
        changed_archive = self.test_root / "changed-candidate.tar.gz"
        shutil.copy2(self.archive, changed_archive)
        with changed_archive.open("ab") as stream:
            stream.write(b"changed archive bytes")
        output = self.test_root / "changed-archive.json"
        result = self.run_cli([
            "--archive", str(changed_archive), "--candidate-manifest", str(self.candidate_manifest),
            "--output", str(output),
        ])
        self.assert_rejected(result, "candidate-archive-digest-mismatch", output)

    def test_empty_archive_with_matching_manifest_is_rejected(self) -> None:
        empty_archive = self.test_root / "empty.tar.gz"
        empty_archive.write_bytes(b"")
        empty_manifest = self.test_root / "empty-manifest.json"
        empty_manifest.write_text(json.dumps(make_candidate_manifest(
            self.candidate_source_sha, hash_file(empty_archive), "a" * 64)), encoding="utf-8")
        output = self.test_root / "empty-archive.json"
        result = self.run_cli([
            "--archive", str(empty_archive), "--candidate-manifest", str(empty_manifest),
            "--output", str(output),
        ])
        self.assert_rejected(result, "archive-empty", output)

    def failing_project(self, language: str) -> Path:
        project = self.test_root / f"failing-{language}"
        (project / "tests" / "scripts").mkdir(parents=True)
        for candidate in LANGUAGES:
            target = project / "tests" / "consumers" / candidate
            source = ROOT / "tests" / "consumers" / candidate
            target.mkdir(parents=True)
            shutil.copy2(source / "CMakeLists.txt", target / "CMakeLists.txt")
            program = "main.c" if candidate == "c" else "main.cpp"
            original = source / program
            body = original.read_text(encoding="utf-8")
            if candidate == language:
                terminal = "    return 0;\n}"
                position = body.rfind(terminal)
                self.assertNotEqual(position, -1)
                failure = 17 if candidate == "c" else 19
                body = body[:position] + f"    return {failure};\n}}" + body[position + len(terminal):]
            (target / program).write_text(body, encoding="utf-8")
        shutil.copy2(SCRIPT, project / "tests" / "scripts" / SCRIPT.name)
        shutil.copytree(ROOT / "cmake", project / "cmake")
        shutil.copytree(ROOT / "tests" / "acceptance", project / "tests" / "acceptance")
        shutil.copytree(ROOT / "fixtures" / "libbet", project / "fixtures" / "libbet")
        return project

    def test_failing_c_consumer_is_rejected(self) -> None:
        project = self.failing_project("c")
        output = self.test_root / "failing-c.json"
        script = project / "tests" / "scripts" / SCRIPT.name
        result = self.run_cli([*self.candidate_args(self.prefix), "--output", str(output)], script=script)
        self.assert_rejected(result, "consumer-failed:c:exit-1", output)

    def test_failing_cpp_consumer_is_rejected(self) -> None:
        project = self.failing_project("cpp")
        output = self.test_root / "failing-cpp.json"
        script = project / "tests" / "scripts" / SCRIPT.name
        result = self.run_cli([*self.candidate_args(self.prefix), "--output", str(output)], script=script)
        self.assert_rejected(result, "consumer-failed:cpp:exit-1", output)

    def test_repeated_runs_keep_behavior_and_package_identity(self) -> None:
        receipts: list[dict[str, object]] = []
        for index in (1, 2):
            output_dir = self.test_root / f"repeat-{index}"
            output_dir.mkdir()
            output = output_dir / "receipt.json"
            result = self.run_cli([*self.candidate_args(self.prefix), "--output", str(output)])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipts.append(parse_receipt(result, output))
            self.assertFalse(Path(str(output) + ".lock").exists())
        for field in ("source_sha", "runner_reported_source_sha", "candidate_source_sha",
                      "archive_sha256", "installed_tree_sha256", "package_sha256",
                      "compiler", "api_behaviors", "results"):
            self.assertEqual(receipts[0].get(field), receipts[1].get(field), field)
        self.assertNotEqual(receipts[0].get("build_run_id"), receipts[1].get("build_run_id"))

    def test_concurrent_runs_use_distinct_build_and_output_roots(self) -> None:
        outputs = [self.test_root / f"concurrent-{index}" / "receipt.json" for index in (1, 2)]
        for output in outputs:
            output.parent.mkdir()
        processes = [
            subprocess.Popen(
                [sys.executable, "-I", str(SCRIPT), *self.candidate_args(self.prefix),
                 "--output", str(output)],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for output in outputs
        ]
        completed: list[subprocess.CompletedProcess[str]] = []
        try:
            for process in processes:
                stdout, stderr = process.communicate(timeout=120 * TIMEOUT_SCALE)
                completed.append(subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr))
        except subprocess.TimeoutExpired:
            for process in processes:
                process.kill()
            for process in processes:
                process.communicate()
            self.fail("concurrent consumer verification timed out")
        for result in completed:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipts = [json.loads(output.read_text(encoding="utf-8")) for output in outputs]
        self.assertEqual(receipts[0].get("package_sha256"), receipts[1].get("package_sha256"))
        self.assertEqual(receipts[0].get("source_sha"), receipts[1].get("source_sha"))
        self.assertNotEqual(receipts[0].get("build_run_id"), receipts[1].get("build_run_id"))
        for receipt in receipts:
            results = receipt.get("results", {})
            self.assertEqual(set(results), set(LANGUAGES))
            self.assertTrue(all(item.get("build_isolated") for item in results.values()))

    def test_active_output_collision_is_rejected(self) -> None:
        output = self.test_root / "owned" / "receipt.json"
        output.parent.mkdir()
        lock = Path(str(output) + ".lock")
        lock.write_text(json.dumps({"pid": os.getpid(), "token": "held-by-test"}), encoding="utf-8")
        result = self.run_cli([*self.candidate_args(self.prefix), "--output", str(output)])
        self.assert_rejected(result, "output-owned", output)

    def extract_cli(self, archive: Path, destination: Path) -> subprocess.CompletedProcess[str]:
        return self.run_cli(["--extract", str(archive), str(destination)])

    def test_extract_rejects_windows_unsafe_members(self) -> None:
        cases = {
            "backslash-traversal": "..\\..\\evil.txt",
            "backslash-plain": "a\\b",
            "colon-nested": "x/D:evil",
            "reserved-con": "share/CON",
            "reserved-nul-ext": "share/nul.txt",
            "reserved-lpt": "share/LPT1",
            "trailing-dot": "share/name.",
            "reserved-conin": "share/CONIN$",
            "reserved-conout-ext": "share/conout$.txt",
            "reserved-superscript-com": "share/COM\u00b9",
            "reserved-superscript-lpt-ext": "share/LPT\u00b3.log",
        }
        work = self.test_root / "windows-unsafe-members"
        work.mkdir()
        for label, member_name in cases.items():
            with self.subTest(label):
                archive = work / f"{label}.tar.gz"
                payload = b"hostile\n"
                with tarfile.open(archive, "w:gz") as bundle:
                    info = tarfile.TarInfo("ok/file.txt")
                    info.size = len(payload)
                    bundle.addfile(info, io.BytesIO(payload))
                    hostile = tarfile.TarInfo(member_name)
                    hostile.size = len(payload)
                    bundle.addfile(hostile, io.BytesIO(payload))
                destination = work / f"{label}-dest"
                result = self.extract_cli(archive, destination)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("rejected:archive-path-unsafe", result.stderr)
                self.assertFalse(destination.exists(), "a rejected archive must not leave a destination")

    def test_extract_accepts_nested_directories(self) -> None:
        archive = self.test_root / "nested-ok.tar.gz"
        payload = b"fine\n"
        with tarfile.open(archive, "w:gz") as bundle:
            directory = tarfile.TarInfo("top/inner")
            directory.type = tarfile.DIRTYPE
            bundle.addfile(directory)
            info = tarfile.TarInfo("top/inner/file.txt")
            info.size = len(payload)
            bundle.addfile(info, io.BytesIO(payload))
        destination = self.test_root / "nested-ok-dest"
        result = self.extract_cli(archive, destination)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((destination / "top/inner/file.txt").read_bytes(), payload)

    def test_extract_rejects_existing_destination(self) -> None:
        destination = self.test_root / "idempotent-dest"
        first = self.extract_cli(self.archive, destination)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        listing = sorted(str(path.relative_to(destination)) for path in destination.rglob("*"))
        self.assertTrue(listing)
        second = self.extract_cli(self.archive, destination)
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn("rejected:extract-destination-exists", second.stderr)
        after = sorted(str(path.relative_to(destination)) for path in destination.rglob("*"))
        self.assertEqual(listing, after)

    @unittest.skipIf(os.name == "nt", "Process.terminate() on Windows kills the child without delivering a signal, so the "
                                     "interrupt cleanup path cannot be exercised there; it runs on the POSIX evidence runners")
    def test_interrupted_extraction_removes_partial_tree_and_retries(self) -> None:
        output_dir = self.test_root / "interrupted-extraction"
        output_dir.mkdir()
        output = output_dir / "receipt.json"
        marker = output_dir / "extract-paused.json"
        environment = os.environ.copy()
        environment[TEST_EXTRACT_PAUSE_ENV] = str(marker)
        process = subprocess.Popen(
            [sys.executable, "-I", str(SCRIPT), "--archive", str(self.archive),
             "--candidate-manifest", str(self.candidate_manifest), "--output", str(output)],
            cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace",
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not marker.exists() and process.poll() is None:
            time.sleep(0.05)
        self.assertTrue(marker.exists(), "archive extraction did not reach its controlled point")
        marker_data = json.loads(marker.read_text(encoding="utf-8"))
        process.terminate()
        stdout, stderr = process.communicate(timeout=15)
        self.assertNotEqual(process.returncode, 0, stdout + stderr)
        self.assertIn("verify-v02-consumers: rejected:interrupted:signal-", stderr)
        self.assertFalse(output.exists(), "an interrupted extraction must not publish a receipt")
        self.assertFalse(Path(str(output) + ".lock").exists(), "interrupted extraction must release its lock")
        temp_root = Path(marker_data.get("temp_root", ""))
        self.assertFalse(temp_root.exists(), "interrupted extraction must remove its partial tree")
        self.assertGreater(marker_data.get("staged_file_count", 0), 0,
                           "interruption must occur after archive bytes are extracted")
        retry = self.run_cli([
            "--archive", str(self.archive), "--candidate-manifest", str(self.candidate_manifest),
            "--output", str(output),
        ])
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        self.assertEqual(parse_receipt(retry, output).get("result"), "passed")

    @unittest.skipIf(os.name == "nt", "Process.terminate() on Windows kills the child without delivering a signal, so the "
                                     "interrupt cleanup path cannot be exercised there; it runs on the POSIX evidence runners")
    def test_interrupted_run_retries_without_partial_receipt(self) -> None:
        output_dir = self.test_root / "interrupted"
        output_dir.mkdir()
        output = output_dir / "receipt.json"
        marker = output_dir / "install-paused.json"
        environment = os.environ.copy()
        environment[TEST_PAUSE_ENV] = str(marker)
        process = subprocess.Popen(
            [sys.executable, "-I", str(SCRIPT), "--run", "--output", str(output)],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not marker.exists() and process.poll() is None:
            time.sleep(0.05)
        self.assertTrue(marker.exists(), "the interrupted install did not reach its controlled point")
        marker_data = json.loads(marker.read_text(encoding="utf-8"))
        process.terminate()
        stdout, stderr = process.communicate(timeout=15)
        self.assertNotEqual(process.returncode, 0, stdout + stderr)
        self.assertIn("verify-v02-consumers: rejected:interrupted:signal-", stderr)
        self.assertFalse(output.exists(), "an interrupted run must not publish a success receipt")
        temp_root = Path(marker_data.get("temp_root", ""))
        temp_base = Path(tempfile.gettempdir()).resolve()
        if temp_root.exists() and temp_root.resolve().parent == temp_base and temp_root.name.startswith("gabbaboy-v02-consumers-"):
            shutil.rmtree(temp_root)
        retry = self.run_cli(["--run", "--output", str(output)])
        self.assertEqual(retry.returncode, 0, retry.stdout + retry.stderr)
        receipt = parse_receipt(retry, output)
        self.assertEqual(receipt.get("result"), "passed")
        self.assertGreater(marker_data.get("staged_file_count", 0), 0,
                           "interruption must occur after staged package bytes exist")


# Phase 16 D-19: --self-test --consumer {c,cpp} runs the static controls plus one half of the heavy relocated
# builds, so the two halves can run side by side in CTest. Every test method must be classified exactly once;
# an unclassified or doubly classified test fails the self-test instead of silently dropping out of a half.
SELF_TEST_STATIC = frozenset({
    "test_missing_prefix_is_rejected",
    "test_removed_package_config_is_rejected",
    "test_forged_runner_source_does_not_qualify_changed_package",
    "test_workflow_command_without_candidate_manifest_is_rejected",
    "test_manifest_writer_rejects_unbound_inputs",
    "test_changed_archive_does_not_match_stale_candidate_manifest",
    "test_empty_archive_with_matching_manifest_is_rejected",
    "test_active_output_collision_is_rejected",
    "test_extract_rejects_windows_unsafe_members",
    "test_extract_accepts_nested_directories",
    "test_extract_rejects_existing_destination",
})
SELF_TEST_HEAVY = {
    "c": frozenset({
        "test_relocated_prefix_runs_both_consumers",
        "test_repeated_runs_keep_behavior_and_package_identity",
        "test_failing_c_consumer_is_rejected",
        "test_interrupted_extraction_removes_partial_tree_and_retries",
    }),
    "cpp": frozenset({
        "test_written_manifest_binds_archive_and_build_receipt_and_qualifies",
        "test_concurrent_runs_use_distinct_build_and_output_roots",
        "test_interrupted_run_retries_without_partial_receipt",
        "test_failing_cpp_consumer_is_rejected",
    }),
}
SELF_TEST_POSITIVE = frozenset({
    "test_relocated_prefix_runs_both_consumers",
    "test_repeated_runs_keep_behavior_and_package_identity",
    "test_written_manifest_binds_archive_and_build_receipt_and_qualifies",
    "test_concurrent_runs_use_distinct_build_and_output_roots",
    "test_interrupted_run_retries_without_partial_receipt",
    "test_extract_accepts_nested_directories",
})


def select_self_tests(consumer: str | None) -> unittest.TestSuite:
    loaded = list(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContractTests))
    names = [test._testMethodName for test in loaded]
    classified = list(SELF_TEST_STATIC) + [n for group in SELF_TEST_HEAVY.values() for n in group]
    need(sorted(names) == sorted(classified),
         "self-test-partition-mismatch:" + ",".join(sorted(set(names) ^ set(classified))))
    chosen = set(names) if consumer is None else set(SELF_TEST_STATIC) | set(SELF_TEST_HEAVY[consumer])
    return unittest.TestSuite(test for test in loaded if test._testMethodName in chosen)


def self_test(consumer: str | None = None) -> int:
    suite = select_self_tests(consumer)
    names = {test._testMethodName for test in suite}  # a run empties the suite, so read it first
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    if consumer is None:
        controls = 12
        positives = 8
    else:
        positives = len(names & SELF_TEST_POSITIVE)
        controls = len(names - SELF_TEST_POSITIVE)
    summary = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "positive_successes": positives if result.wasSuccessful() else 0,
        "negative_controls": controls,
        "tests_run": result.testsRun,
    }
    if consumer is not None:
        summary["consumer"] = consumer
    print(json.dumps(summary, sort_keys=True))
    if not result.wasSuccessful() or controls == 0 or summary["positive_successes"] == 0:
        return 1
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="install and verify the configured build")
    mode.add_argument("--self-test", action="store_true", help="exercise positive and named rejection controls")
    parser.add_argument("--consumer", choices=LANGUAGES,
                        help="with --self-test, run the static controls plus this half of the relocated builds")
    parser.add_argument("--prefix", type=Path, help="require an extracted prefix matching the candidate archive")
    parser.add_argument("--archive", type=Path, help="candidate product archive to qualify")
    parser.add_argument("--candidate-manifest", type=Path,
                        help="versioned source/archive manifest supplied by the candidate validator")
    parser.add_argument("--platform", choices=("linux-x64", "macos-arm64", "windows-x64"),
                        help="release platform for the optional host-smoke receipt")
    host_smoke_mode = parser.add_mutually_exclusive_group()
    host_smoke_mode.add_argument("--host-smoke-receipt", type=Path,
                                 help="embed a successful installed-host smoke receipt")
    host_smoke_mode.add_argument("--host-smoke-not-applicable", action="store_true",
                                 help="record the Windows host-mode exclusion")
    parser.add_argument("--extract", nargs=2, metavar=("ARCHIVE", "DESTINATION"),
                        help="safely extract a product archive into a new destination")
    parser.add_argument("--output", type=Path, help="write the success receipt atomically")
    parser.add_argument("--write-candidate-manifest", type=Path, metavar="MANIFEST",
                        help="write a candidate manifest binding --archive, --source-sha and --build-receipt")
    parser.add_argument("--source-sha", help="candidate source commit for --write-candidate-manifest")
    parser.add_argument("--build-receipt", type=Path, help="build receipt bound by --write-candidate-manifest")
    args = parser.parse_args(argv)
    if args.consumer and not args.self_test:
        parser.error("--consumer is only for --self-test")
    if args.write_candidate_manifest:
        if (args.run or args.self_test or args.prefix or args.extract or args.output or args.candidate_manifest
                or args.platform or args.host_smoke_receipt or args.host_smoke_not_applicable):
            parser.error("--write-candidate-manifest accepts only --archive, --source-sha and --build-receipt")
        if not (args.archive and args.source_sha and args.build_receipt):
            parser.error("--write-candidate-manifest requires --archive, --source-sha and --build-receipt")
        return args
    if args.source_sha or args.build_receipt:
        parser.error("--source-sha and --build-receipt are only for --write-candidate-manifest")
    if args.extract:
        if (args.run or args.self_test or args.prefix or args.archive or args.candidate_manifest or args.output
                or args.platform or args.host_smoke_receipt or args.host_smoke_not_applicable):
            parser.error("--extract does not accept consumer qualification options")
        return args
    if args.self_test:
        if (args.run or args.prefix or args.archive or args.candidate_manifest or args.output
                or args.platform or args.host_smoke_receipt or args.host_smoke_not_applicable):
            parser.error("--self-test does not accept qualification options")
        return args
    if args.run and (args.prefix or args.archive or args.candidate_manifest):
        parser.error("--run creates its own local candidate manifest")
    if args.platform is None and (args.host_smoke_receipt or args.host_smoke_not_applicable):
        parser.error("host-smoke options require --platform")
    if args.platform is not None and not (args.host_smoke_receipt or args.host_smoke_not_applicable):
        parser.error("--platform requires a host-smoke receipt mode")
    if args.host_smoke_receipt and args.platform == "windows-x64":
        parser.error("windows-x64 uses --host-smoke-not-applicable")
    if args.host_smoke_not_applicable and args.platform != "windows-x64":
        parser.error("--host-smoke-not-applicable requires --platform windows-x64")
    if not args.run and not args.prefix and not args.archive:
        parser.error("--run, --prefix, --archive, or --self-test is required")
    if args.output is None:
        parser.error("--output is required with --run or candidate qualification")
    return args


def main(argv: list[str]) -> int:
    install_signal_handlers()
    try:
        args = parse_args(argv)
        if args.extract:
            safe_extract_archive(Path(args.extract[0]), Path(args.extract[1]))
            return 0
        if args.write_candidate_manifest:
            manifest = write_candidate_manifest(args.archive.expanduser(), args.source_sha,
                                                args.build_receipt.expanduser(),
                                                args.write_candidate_manifest.expanduser())
            print(json.dumps(manifest, sort_keys=True))
            return 0
        host_smoke_receipt = None
        if args.host_smoke_receipt:
            host_smoke_receipt = read_host_smoke(args.host_smoke_receipt.expanduser(), args.platform)
        elif args.host_smoke_not_applicable:
            host_smoke_receipt = {"result": "not-applicable"}
        receipt = run_driver(
            project_root=ROOT,
            output_path=args.output,
            prefix_value=args.prefix,
            archive_value=args.archive,
            candidate_manifest_value=args.candidate_manifest,
            fresh_install=args.run,
            platform_id=args.platform,
            host_smoke=host_smoke_receipt,
        )
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except InterruptedRun as error:
        print(f"verify-v02-consumers: rejected:interrupted:{error}", file=sys.stderr)
        return 130
    except (ContractError, OSError, ValueError, json.JSONDecodeError) as error:
        reason = str(error) if isinstance(error, ContractError) else f"driver-error:{type(error).__name__}"
        print(f"verify-v02-consumers: rejected:{reason}", file=sys.stderr)
        return 1
    except SystemExit as error:
        return int(error.code) if isinstance(error.code, int) else 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        install_signal_handlers()
        raise SystemExit(self_test())
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--self-test", "--consumer"] and sys.argv[3] in LANGUAGES:
        install_signal_handlers()
        raise SystemExit(self_test(sys.argv[3]))
    raise SystemExit(main(sys.argv[1:]))
