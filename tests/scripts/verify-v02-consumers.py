#!/usr/bin/env python3
"""Verify relocated C and C++ consumers against installed GabbaBoy bytes."""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
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
# A sanitizer-built runner and package run several times slower; scale every bounded wait alike.
TIMEOUT_SCALE = 5 if os.environ.get("GBB_SANITIZER_LINK_OPTIONS") else 1
COMMAND_TIMEOUT_SECONDS = 90 * TIMEOUT_SCALE
TEST_PAUSE_ENV = "GABBABOY_V02_TEST_INSTALL_PAUSE"
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
                 *, prefix_origin: str, run_id: str, temp_root: Path) -> dict[str, object]:
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
        "schema_version": 1,
        "result": "passed",
        "source_sha": source_sha,
        "build_qualified": build_qualified,
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
               fresh_install: bool) -> dict[str, object]:
    run_id = uuid.uuid4().hex
    reservation = OutputReservation(output_path)
    with reservation as output:
        if fresh_install:
            cmake = cmake_executable()
            with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-consumers-") as temp_name:
                temp_root = Path(temp_name)
                prefix = install_package(project_root, temp_root, cmake)
                resolved_prefix, config, package_hash = verify_prefix(prefix, project_root)
                receipt = make_receipt(
                    resolved_prefix, config, package_hash, project_root,
                    prefix_origin="fresh-install-relocated", run_id=run_id,
                    temp_root=temp_root / "consumer-builds",
                )
        else:
            need(prefix_value is not None, "prefix-missing")
            prefix, config, package_hash = verify_prefix(prefix_value, project_root)
            with tempfile.TemporaryDirectory(prefix="gabbaboy-v02-consumers-") as temp_name:
                receipt = make_receipt(
                    prefix, config, package_hash, project_root,
                    prefix_origin="supplied-relocated-install", run_id=run_id,
                    temp_root=Path(temp_name),
                )
        reservation.publish(receipt)
    return receipt


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

    def test_relocated_prefix_runs_both_consumers(self) -> None:
        output = self.test_root / "positive.json"
        result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = parse_receipt(result, output)
        self.assertEqual(receipt.get("result"), "passed")
        self.assertEqual(set(receipt.get("results", {})), set(LANGUAGES))
        self.assertTrue(receipt.get("isolated_prefix"))
        self.assertEqual(receipt.get("api_behaviors"), {
            behavior: {language: "passed" for language in LANGUAGES} for behavior in BEHAVIORS
        })

    def test_missing_prefix_is_rejected(self) -> None:
        output = self.test_root / "missing-prefix.json"
        missing = self.test_root / "does-not-exist"
        result = self.run_cli(["--prefix", str(missing), "--output", str(output)])
        self.assert_rejected(result, "prefix-missing", output)

    def test_removed_package_config_is_rejected(self) -> None:
        broken = self.test_root / "without-config"
        shutil.copytree(self.prefix, broken)
        configs = package_configs(broken)
        self.assertEqual(len(configs), 1)
        configs[0].unlink()
        output = self.test_root / "missing-config.json"
        result = self.run_cli(["--prefix", str(broken), "--output", str(output)])
        self.assert_rejected(result, "package-config-count:expected-one-found-0", output)

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
        result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)], script=script)
        self.assert_rejected(result, "consumer-failed:c:exit-1", output)

    def test_failing_cpp_consumer_is_rejected(self) -> None:
        project = self.failing_project("cpp")
        output = self.test_root / "failing-cpp.json"
        script = project / "tests" / "scripts" / SCRIPT.name
        result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)], script=script)
        self.assert_rejected(result, "consumer-failed:cpp:exit-1", output)

    def test_repeated_runs_keep_behavior_and_package_identity(self) -> None:
        receipts: list[dict[str, object]] = []
        for index in (1, 2):
            output_dir = self.test_root / f"repeat-{index}"
            output_dir.mkdir()
            output = output_dir / "receipt.json"
            result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipts.append(parse_receipt(result, output))
            self.assertFalse(Path(str(output) + ".lock").exists())
        for field in ("source_sha", "package_sha256", "compiler", "api_behaviors", "results"):
            self.assertEqual(receipts[0].get(field), receipts[1].get(field), field)
        self.assertNotEqual(receipts[0].get("build_run_id"), receipts[1].get("build_run_id"))

    def test_concurrent_runs_use_distinct_build_and_output_roots(self) -> None:
        outputs = [self.test_root / f"concurrent-{index}" / "receipt.json" for index in (1, 2)]
        for output in outputs:
            output.parent.mkdir()
        processes = [
            subprocess.Popen(
                [sys.executable, "-I", str(SCRIPT), "--prefix", str(self.prefix),
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
        result = self.run_cli(["--prefix", str(self.prefix), "--output", str(output)])
        self.assert_rejected(result, "output-owned", output)

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


def self_test() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerContractTests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    controls = 6
    summary = {
        "status": "passed" if result.wasSuccessful() else "failed",
        "positive_successes": 5 if result.wasSuccessful() else 0,
        "negative_controls": controls,
        "tests_run": result.testsRun,
    }
    print(json.dumps(summary, sort_keys=True))
    if not result.wasSuccessful() or controls == 0 or summary["positive_successes"] == 0:
        return 1
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true", help="install and verify the configured build")
    mode.add_argument("--prefix", type=Path, help="verify an extracted installation outside the checkout")
    mode.add_argument("--self-test", action="store_true", help="exercise positive and named rejection controls")
    parser.add_argument("--output", type=Path, help="write the success receipt atomically")
    args = parser.parse_args(argv)
    if args.self_test:
        parser.error("--self-test does not accept --output")
    if args.output is None:
        parser.error("--output is required with --run or --prefix")
    return args


def main(argv: list[str]) -> int:
    install_signal_handlers()
    try:
        args = parse_args(argv)
        receipt = run_driver(
            project_root=ROOT,
            output_path=args.output,
            prefix_value=args.prefix,
            fresh_install=args.run,
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
    raise SystemExit(main(sys.argv[1:]))
