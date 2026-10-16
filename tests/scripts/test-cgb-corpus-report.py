#!/usr/bin/env python3
"""Contract tests for the private CGB corpus report adapter."""

import contextlib
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = Path(os.environ.get("GBB_TEST_BUILD_DIR", ROOT / "build"))
if not BUILD_DIR.is_absolute():
    BUILD_DIR = ROOT / BUILD_DIR
REPORTER = ROOT / "tests" / "scripts" / "verify-cgb-corpus-report.py"
INVENTORY_VALIDATOR = ROOT / "tests" / "scripts" / "verify-cgb-corpus-inventory.py"
DAA_CASE_ID = "mooneye:acceptance/instr/daa.s"
REPORTER_SPEC = importlib.util.spec_from_file_location("cgb_corpus_reporter", REPORTER)
REPORTER_IMPL = importlib.util.module_from_spec(REPORTER_SPEC)
REPORTER_SPEC.loader.exec_module(REPORTER_IMPL)


class CorpusReportTracerTests(unittest.TestCase):
    def test_tracer_single_case_receipt(self):
        completed = subprocess.run(
            [sys.executable, "-I", str(REPORTER), "--self-test", "--build-dir", str(BUILD_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt.get("schema"), "gabbaboy-cgb-corpus-receipt-v1")
        self.assertEqual(receipt.get("status"), "complete", receipt)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual([case.get("id") for case in receipt.get("cases", [])], [DAA_CASE_ID])
        self.assertEqual(receipt["counts"]["attempted_cases"], 1)
        self.assertEqual(receipt["counts"]["completed_cases"], 1)
        self.assertEqual(receipt["counts"]["observed_pass_cases"], 1)
        self.assertEqual(receipt["counts"]["assertions"], 1)
        runner_path = REPORTER_IMPL.build_executable_path(BUILD_DIR, "gabbaboy-runner")
        self.assertEqual(receipt["identity"]["executable_path"], REPORTER_IMPL.repo_path(runner_path))

    def test_tracer_controls(self):
        completed = subprocess.run(
            [sys.executable, "-I", str(REPORTER), "--self-test-controls",
             "--build-dir", str(BUILD_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("cgb-corpus-report tracer-controls pass clean=1 altered=1 stale-green=1",
                      completed.stdout)
        with tempfile.TemporaryDirectory(prefix="cgb-report-control-", dir=BUILD_DIR) as temp:
            base = Path(temp)
            fake_build = base / "missing-build"
            receipt_path = base / "receipt.json"
            receipt_path.write_text(
                '{"schema":"gabbaboy-cgb-corpus-receipt-v1","status":"complete"}\n',
                encoding="utf-8",
            )
            failed = subprocess.run(
                [sys.executable, "-I", str(REPORTER), "--run", "--build-dir", str(fake_build),
                 "--receipt", str(receipt_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            current = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(current.get("status"), "incomplete", current)
            self.assertEqual(current.get("counts", {}).get("completed_cases"), 0, current)
            self.assertEqual(current.get("failure_codes"), ["input-unavailable"], current)


class CorpusReportCorpusTests(unittest.TestCase):
    def test_native_full_ctest_receipt_contract(self):
        checked = subprocess.run(
            [sys.executable, "-I", str(INVENTORY_VALIDATOR), "--ci-contract"],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("ci-contract pass cases=107", checked.stdout)
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        native_job = workflow.split("\n  native-macos:", 1)[0]
        self.assertIn("--begin-run --build-dir build", native_job,
                      "native job must create a fresh receipt run before CTest")
        self.assertIn("-T Test --no-compress-output", native_job,
                      "native job must retain the full CTest event output")
        self.assertIn("--test-output-size-passed 16777216", native_job,
                      "native job must retain bounded full output for passing tests")
        self.assertIn("--from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json",
                      native_job, "native job must derive the receipt from that CTest run")
        self.assertIn("verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json",
                      native_job, "native job must validate claims against the derived receipt")
        self.assertLess(native_job.index("--from-ctest --build-dir build --receipt build/cgb-corpus-receipt.json"),
                        native_job.index("verify-cgb-corpus-claims.py --receipt build/cgb-corpus-receipt.json"),
                        "public claims must run only after receipt construction")
        cmake = (ROOT / "tests/CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn("cgb_corpus_build_stamp", cmake,
                      "CMake must maintain a dependency-backed build input stamp")
        self.assertIn("CONFIGURE_DEPENDS", cmake,
                      "CMake must refresh the stamp dependency set when input membership changes")
        self.assertIn("DEPENDS ${GBB_CGB_BUILD_CODE_INPUTS}", cmake,
                      "the stamp must depend on the inputs that are compiled")
        self.assertIn("cgb_corpus_inventory", (ROOT / "tests/expected-tests.txt").read_text(encoding="utf-8"),
                      "the complete inventory validator must remain required")
        self.assertIn("cgb_corpus_ci_contract", (ROOT / "tests/expected-tests.txt").read_text(encoding="utf-8"),
                      "the native receipt contract must be a required inventory member")

    def test_contract(self):
        completed = subprocess.run(
            [sys.executable, "-I", str(INVENTORY_VALIDATOR), "--self-test"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("cgb-corpus-inventory self-test pass", completed.stdout)
        self.assertIn("source-only-execution", completed.stdout)
        context = REPORTER_IMPL.load_corpus_context()
        self.assertEqual(len(context["cases"]), 107)
        self.assertEqual(context["assertion_rows"], 4959)
        self.assertEqual(set(context["case_by_test"]), set(context["test_names"]))


class CorpusReportNativeExecutableTests(unittest.TestCase):
    def _build_dir(self, suffix, *, extensionless=None, suffixed=None):
        temp = tempfile.TemporaryDirectory(prefix="cgb-report-build-", dir=ROOT)
        self.addCleanup(temp.cleanup)
        build_dir = Path(temp.name)
        (build_dir / "CMakeCache.txt").write_text(
            "CMAKE_BUILD_TYPE:STRING=Release\nCMAKE_GENERATOR:INTERNAL=Ninja\n",
            encoding="utf-8",
        )
        if extensionless is not None:
            (build_dir / "gabbaboy-runner").write_bytes(extensionless)
        if suffixed is not None:
            (build_dir / f"gabbaboy-runner{suffix}").write_bytes(suffixed)
        return build_dir

    def test_build_identity_selects_native_executable_on_both_platform_shapes(self):
        contract = REPORTER_IMPL.load_daa_contract()
        for suffix, expected, decoy in (("", b"posix-native", b"wrong-exe"),
                                        (".exe", b"windows-native", b"wrong-extensionless")):
            with self.subTest(suffix=suffix):
                if suffix:
                    build_dir = self._build_dir(suffix, extensionless=decoy, suffixed=expected)
                else:
                    build_dir = self._build_dir(suffix, extensionless=expected)
                    (build_dir / "gabbaboy-runner.exe").write_bytes(decoy)
                with mock.patch.object(sysconfig, "get_config_var", return_value=suffix):
                    identity = REPORTER_IMPL.build_identity(build_dir, contract)
                native_path = build_dir / f"gabbaboy-runner{suffix}"
                self.assertEqual(identity["executable_path"], native_path.relative_to(ROOT).as_posix())
                self.assertEqual(identity["executable_sha256"], REPORTER_IMPL.sha256(expected))

    def test_build_identity_rejects_missing_windows_native_path(self):
        build_dir = self._build_dir(".exe", extensionless=b"wrong-extensionless")
        with mock.patch.object(sysconfig, "get_config_var", return_value=".exe"):
            with self.assertRaises(REPORTER_IMPL.ReportError) as raised:
                REPORTER_IMPL.build_identity(build_dir, REPORTER_IMPL.load_daa_contract())
        self.assertEqual(raised.exception.code, "input-unavailable")

    def test_full_build_identity_uses_native_suffix_for_all_artifacts(self):
        context = REPORTER_IMPL.load_corpus_context()
        executable_names = (
            "gabbaboy-runner", "tests/test_age", "tests/test_age_m3",
            "tests/test_magentests", "tests/test_magentests_hdma",
            "tests/test_samesuite_apu", "tests/test_samesuite_hdma",
        )
        temp = tempfile.TemporaryDirectory(prefix="cgb-report-full-build-", dir=ROOT)
        self.addCleanup(temp.cleanup)
        build_dir = Path(temp.name)
        (build_dir / "CMakeCache.txt").write_text(
            "CMAKE_BUILD_TYPE:STRING=Release\nCMAKE_GENERATOR:INTERNAL=Ninja\n",
            encoding="utf-8",
        )
        expected = {}
        for name in executable_names:
            suffixed = build_dir / f"{name}.exe"
            suffixed.parent.mkdir(parents=True, exist_ok=True)
            data = f"native:{name}".encode()
            suffixed.write_bytes(data)
            extensionless = build_dir / name
            extensionless.parent.mkdir(parents=True, exist_ok=True)
            extensionless.write_bytes(b"wrong-extensionless")
            expected[suffixed.relative_to(ROOT).as_posix()] = REPORTER_IMPL.sha256(data)
        with mock.patch.object(sysconfig, "get_config_var", return_value=".exe"):
            identity = REPORTER_IMPL.full_build_identity(build_dir, context)
        artifacts = {row["path"]: row["sha256"] for row in identity["build_artifacts"]}
        self.assertEqual(artifacts, expected)

    def test_build_tracer_report_runs_native_executable_path(self):
        build_dir = BUILD_DIR
        contract = {"manifest_path": ROOT / "fixtures/age/manifest.json"}
        with mock.patch.object(sysconfig, "get_config_var", return_value=".exe"):
            with mock.patch.object(REPORTER_IMPL, "load_daa_contract", return_value=contract):
                with mock.patch.object(REPORTER_IMPL, "build_identity", return_value={"identity": True}):
                    with mock.patch.object(REPORTER_IMPL, "run_bounded", return_value=(0, b"event")) as run:
                        with mock.patch.object(REPORTER_IMPL, "validate_event_with_identity", return_value={}):
                            with mock.patch.object(REPORTER_IMPL, "complete_receipt", return_value={"status": "complete"}):
                                REPORTER_IMPL.build_tracer_report(build_dir)
        command = run.call_args.args[0]
        self.assertEqual(command[0], str(build_dir / "gabbaboy-runner.exe"))


class CorpusReportBoundedProcessTests(unittest.TestCase):
    def _assert_windows_failure(self, command, expected_code, *, timeout=5,
                                max_stream_bytes=None, reader_error=False):
        original_popen = REPORTER_IMPL.subprocess.Popen
        processes = []

        def tracked_popen(*args, **kwargs):
            proc = original_popen(*args, **kwargs)
            processes.append(proc)
            return proc

        def terminate(proc):
            try:
                proc.kill()
            except OSError:
                pass
            proc.wait(timeout=2)

        reader_patch = (mock.patch.object(REPORTER_IMPL, "_read_bounded_pipe_chunk",
                                          side_effect=OSError("injected read failure"))
                        if reader_error else contextlib.nullcontext())
        cap_patch = (mock.patch.object(REPORTER_IMPL, "MAX_STREAM_BYTES", max_stream_bytes)
                     if max_stream_bytes is not None else contextlib.nullcontext())
        with mock.patch.object(REPORTER_IMPL.os, "name", "nt"):
            with mock.patch.object(REPORTER_IMPL.subprocess, "Popen", side_effect=tracked_popen):
                with mock.patch.object(REPORTER_IMPL, "_terminate_bounded_process", side_effect=terminate):
                    with reader_patch, cap_patch:
                        with self.assertRaises(REPORTER_IMPL.ReportError) as raised:
                            REPORTER_IMPL.run_bounded(command, timeout_seconds=timeout)
        self.assertEqual(raised.exception.code, expected_code)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll(), "failed bounded run must terminate its child")

    def test_windows_pipe_reader_supports_merged_output_and_nonzero_exit(self):
        command = [
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('stdout-marker\\n'); "
            "sys.stderr.write('stderr-marker\\n'); sys.exit(7)",
        ]
        with mock.patch.object(REPORTER_IMPL.os, "name", "nt"):
            with mock.patch.object(REPORTER_IMPL.selectors, "DefaultSelector",
                                   side_effect=OSError("anonymous pipe cannot be selected")):
                code, output = REPORTER_IMPL.run_bounded(command, timeout_seconds=5)
        self.assertEqual(code, 7)
        self.assertIn(b"stdout-marker", output)
        self.assertIn(b"stderr-marker", output)

    def test_windows_output_overflow_terminates_child(self):
        self._assert_windows_failure(
            [sys.executable, "-c", "import sys,time; sys.stdout.buffer.write(b'x'*65536); "
             "sys.stdout.flush(); time.sleep(30)"],
            "captured-stream-too-large", max_stream_bytes=32,
        )

    def test_windows_deadline_terminates_child(self):
        self._assert_windows_failure(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            "runner-timeout", timeout=0.05,
        )

    def test_windows_reader_error_terminates_child(self):
        self._assert_windows_failure(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            "runner-output-read-failed", reader_error=True,
        )


class CorpusReportControlsTests(unittest.TestCase):
    def test_controls(self):
        report = REPORTER_IMPL
        one = "cgb_case"

        def block(test_id, name, output="terminal=pass", total=1):
            return (f"test {test_id}\n        Start {test_id}: {name}\n"
                    f"{test_id}: {output}\n  {test_id}/{total} Test #{test_id}: {name} ... Passed 0.01 sec\n")

        good_log = (block(1, one) + "\n100% tests passed out of 1\n").encode()
        parsed, count = report.parse_ctest_log(good_log, {one})
        self.assertEqual(count, 1)
        self.assertEqual(parsed[0]["output"], "terminal=pass")
        for expected_names, bad_log, code in (
            (set(), good_log, "ctest-log-membership"),
            ({one, "cgb_other"}, good_log, "ctest-log-membership"),
            ({one}, block(1, one).encode(), "ctest-log-incomplete"),
            ({one}, b"x" * (report.MAX_RUN_LOG_BYTES + 1), "ctest-log-too-large"),
        ):
            with self.subTest(code=code, names=sorted(expected_names)):
                with self.assertRaises(report.ReportError) as raised:
                    report.parse_ctest_log(bad_log, expected_names)
                self.assertEqual(raised.exception.code, code)
        duplicate_log = (block(1, one) + block(2, one) +
                         "\n100% tests passed out of 2\n").encode()
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_log(duplicate_log, {one, "cgb_other"})
        self.assertEqual(raised.exception.code, "ctest-log-membership")
        narrowed_log = (block(1, one, total=2) + block(2, "cgb_other", total=2) +
                        "\n100% tests passed out of 2\n").encode()
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_log(narrowed_log, {one})
        self.assertEqual(raised.exception.code, "ctest-log-membership")

        for path in ("../escape", "/etc/passwd", "C:\\private\\file", "a//b"):
            with self.subTest(path=path):
                with self.assertRaises(report.ReportError) as raised:
                    report.validate_relative_path(path, "path-invalid")
                self.assertEqual(raised.exception.code, "path-invalid")
        with tempfile.TemporaryDirectory(prefix="cgb-report-input-", dir=BUILD_DIR) as temp:
            oversized = Path(temp) / "oversized.bin"
            oversized.write_bytes(b"0123456789")
            with self.assertRaises(report.ReportError) as raised:
                report.bounded_read(oversized, 8)
            self.assertEqual(raised.exception.code, "input-too-large")

        signature = "a" * 64
        xfail = {"case": {"evaluator_disposition": {
            "state": "expected-failure", "signature_sha256": signature}}}
        self.assertTrue(report.validate_case_outcome(xfail, "fail", "xfail", signature))

        ctest_xml = (b'<Site><Testing><TestList>'
                     b'<Test>./tests/cgb_case</Test><Test>./tests/other_case</Test>'
                     b'</TestList>'
                     b'<Test Status="passed"><Name>cgb_case</Name><Path>./tests</Path>'
                     b'<FullName>./tests/cgb_case</FullName><Results>'
                     b'<NamedMeasurement type="numeric/double" name="Execution Time">'
                     b'<Value>0.01</Value></NamedMeasurement>'
                     b'<NamedMeasurement type="text/string" name="Completion Status">'
                     b'<Value>Completed</Value></NamedMeasurement>'
                     b'<Measurement><Value>terminal=pass</Value></Measurement>'
                     b'</Results></Test>'
                     b'<Test Status="passed"><Name>other_case</Name><Results/></Test>'
                     b'</Testing></Site>')
        blocks, denominator = report.parse_ctest_xml(ctest_xml, {one})
        self.assertEqual(denominator, 2)
        self.assertEqual([item["name"] for item in blocks], [one])
        self.assertEqual(blocks[0]["output"], "terminal=pass")
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(ctest_xml.replace(b"cgb_case", b"omitted_case"), {one})
        self.assertEqual(raised.exception.code, "ctest-xml-membership")
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(ctest_xml.replace(b'Status="passed"><Name>cgb_case',
                                                     b'Status="failed"><Name>cgb_case'), {one})
        self.assertEqual(raised.exception.code, "ctest-test-failed")
        missing_output = ctest_xml.replace(
            b'<Measurement><Value>terminal=pass</Value></Measurement>', b'')
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(missing_output, {one})
        self.assertEqual(raised.exception.code, "ctest-xml-output-membership")
        duplicate_output = ctest_xml.replace(
            b'<Measurement><Value>terminal=pass</Value></Measurement>',
            b'<Measurement><Value>terminal=pass</Value></Measurement>'
            b'<Measurement><Value>terminal=pass</Value></Measurement>')
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(duplicate_output, {one})
        self.assertEqual(raised.exception.code, "ctest-xml-output-membership")
        duplicate_result = ctest_xml.replace(
            b'</Testing>', b'<Test Status="passed"><Name>cgb_case</Name><Results/></Test></Testing>')
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(duplicate_result, {one})
        self.assertEqual(raised.exception.code, "ctest-xml-test-identity")
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(b"<!DOCTYPE x [<!ENTITY y 'z'>]><Site/>", set())
        self.assertEqual(raised.exception.code, "ctest-xml-invalid")

        context = report.load_corpus_context()
        expected_corpus_tests = set(context["test_names"]) | {report.APU_SUITE_TEST}
        omitted_name = context["cases"]["magentests:bg_oam_priority"]["case"]["test_binding"]["ctest_name"]
        complete_rows = sorted(expected_corpus_tests)
        complete_xml = ("<Site><Testing><TestList>" + "".join(
            f'<Test>./tests/{name}</Test>' for name in complete_rows) + "</TestList>" + "".join(
            f'<Test Status="passed"><Name>{name}</Name><Path>./tests</Path><Results>'
            f'<NamedMeasurement type="numeric/double" name="Execution Time"><Value>0.01</Value>'
            f'</NamedMeasurement><Measurement><Value>terminal=pass</Value></Measurement></Results></Test>'
            for name in complete_rows) + "</Testing></Site>").encode("utf-8")
        complete_blocks, complete_count = report.parse_ctest_xml(complete_xml, expected_corpus_tests)
        self.assertEqual({item["name"] for item in complete_blocks}, expected_corpus_tests)
        self.assertEqual(complete_count, len(expected_corpus_tests))
        omitted_xml = ("<Site><Testing>" + "".join(
            f'<Test Status="passed"><Name>{name}</Name><Results>'
            f'<Measurement><Value>terminal=pass</Value></Measurement></Results></Test>'
            for name in sorted(expected_corpus_tests - {omitted_name})) + "</Testing></Site>").encode("utf-8")
        with self.assertRaises(report.ReportError) as raised:
            report.parse_ctest_xml(omitted_xml, expected_corpus_tests)
        self.assertEqual(raised.exception.code, "ctest-xml-membership")

        with tempfile.TemporaryDirectory(prefix="cgb-stamp-control-", dir=BUILD_DIR) as temp:
            fake_build = Path(temp)
            stamp = {
                "schema": report.BUILD_STAMP_SCHEMA,
                "input_identity_sha256": "a" * 64,
                "core_revision": "b" * 40,
                "build_artifacts": [{"path": "build/runner", "size_bytes": 1, "sha256": "c" * 64}],
                "case_ids": ["case-1"],
                "ctest_names": ["cgb_case"],
            }
            report.write_receipt(report.build_stamp_path(fake_build), stamp)
            identity = {
                "identity_sha256": "a" * 64,
                "core_revision": "b" * 40,
                "build_artifacts": stamp["build_artifacts"],
                "case_ids": stamp["case_ids"],
                "ctest_names": stamp["ctest_names"],
            }
            self.assertEqual(report.verify_build_stamp(fake_build, identity), stamp)
            changed = dict(identity, identity_sha256="d" * 64)
            with self.assertRaises(report.ReportError) as raised:
                report.verify_build_stamp(fake_build, changed)
            self.assertEqual(raised.exception.code, "build-input-stamp-mismatch")

        with tempfile.TemporaryDirectory(prefix="cgb-stale-run-control-", dir=BUILD_DIR) as temp:
            stale_build = Path(temp)
            report.write_receipt(stale_build / "cgb-corpus-run.json", {
                "schema": report.RUN_ID_SCHEMA, "status": "complete", "run_nonce": "0" * 32,
                "started_at_ns": 1, "input_identity_sha256": "a" * 64, "ctest_names": [one],
            })
            with self.assertRaises(report.ReportError) as raised:
                report.load_ctest_run(stale_build, {"identity_sha256": "a" * 64}, {one})
            self.assertEqual(raised.exception.code, "ctest-run-identity-mismatch")
        for observed, evaluator, actual_signature, code in (
            ("pass", "pass", signature, "expected-failure-disposition-mismatch"),
            ("fail", "pass", signature, "expected-failure-disposition-mismatch"),
            ("fail", "xfail", "b" * 64, "expected-failure-signature-mismatch"),
        ):
            with self.subTest(observed=observed, evaluator=evaluator, code=code):
                with self.assertRaises(report.ReportError) as raised:
                    report.validate_case_outcome(xfail, observed, evaluator, actual_signature)
                self.assertEqual(raised.exception.code, code)
        with self.assertRaises(report.ReportError) as raised:
            report.required_cohort_summary("empty-cohort", [{"observed_result": "fail", "matched_xfail": True}])
        self.assertEqual(raised.exception.code, "required-cohort-empty-or-all-xfail")

        age_item = {
            "case": {
                "id": "age:case", "suite": "age", "model": "CGB-CPU-E",
                "mode": "native", "speed": "normal",
                "test_binding": {"ctest_name": "age_case"},
                "source_id": "age:source",
                "evaluator_disposition": {"state": "expected-failure", "value": "expected-failure",
                                          "signature_sha256": signature},
                "execution": {"budget_half_dots": 10},
                "assertion_contract": {"rows": [
                    {"id": "case/row-00", "expected_disposition": "pass", "expected_hex": "0000000000000000"},
                    {"id": "case/row-01", "expected_disposition": "pass", "expected_hex": "0000000000000000"},
                ]},
            },
            "output": {"id": "age:case", "output_path": "fixtures/age/case.gb", "sha256": "0" * 64},
            "source": {"source_path": "src/case.asm", "source_commit": "1" * 40},
        }
        rows = ("age verdict=fail rows_ok=1/2 mask=0001 signature=" + signature + " half_dots=2\n"
                "age-assertion-row id=case/row-00 expected=0000000000000000 actual=0000000000000000 disposition=pass\n"
                "age-assertion-row id=case/row-01 expected=0000000000000000 actual=0000000000000001 disposition=fail\n")
        normalized = report._normalize_age_rows(age_item, rows)
        self.assertEqual(normalized["observed_result"], "fail")
        self.assertTrue(normalized["matched_xfail"])
        for mutated, code in (
            (rows.splitlines()[0] + "\n" + rows.splitlines()[1] + "\n", "age-row-membership"),
            (rows.replace("age-assertion-row id=case/row-01", "age-assertion-row id=unknown"), "age-row-id-membership"),
            (rows.replace("age-assertion-row id=case/row-01", "age-assertion-row id=case/row-00"),
             "age-row-id-membership"),
            (rows.replace("mask=0001", "mask=0003"), "age-verdict-count-mismatch"),
            (rows.replace(signature, "b" * 64), "expected-failure-signature-mismatch"),
            (rows.replace("rows_ok=1/2", "rows_ok=2/2").replace("mask=0001", "mask=0003"),
             "age-verdict-count-mismatch"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(report.ReportError) as raised:
                    report._normalize_age_rows(age_item, mutated)
                self.assertEqual(raised.exception.code, code)

        context = report.load_corpus_context()
        identity = report.full_build_identity(BUILD_DIR, context)
        # Check the real producer stamp, including the configured CTest bytes.
        # A PATH tool and a pinned floor tool must never share green evidence.
        report.verify_build_stamp(BUILD_DIR, identity)
        with mock.patch.object(report.shutil, "which", return_value=sys.executable):
            wrong_tool_identity = report.full_build_identity(BUILD_DIR, context)
        self.assertNotEqual(identity["tools"]["ctest_sha256"],
                            wrong_tool_identity["tools"]["ctest_sha256"])
        with self.assertRaises(report.ReportError) as raised:
            report.verify_build_stamp(BUILD_DIR, wrong_tool_identity)
        self.assertEqual(raised.exception.code, "build-input-stamp-mismatch")
        mooneye_id = "mooneye:misc/boot_hwio-C.s"
        mooneye_item = copy.deepcopy(context["cases"][mooneye_id])
        case = mooneye_item["case"]
        evaluator = case["evaluator_disposition"]
        source = mooneye_item["source"]
        output = mooneye_item["output"]
        runner_case = identity["mooneye_case_ids"][source["source_path"]]
        ticks = case["execution"]["ticks"]
        budget = case["execution"]["budget_half_dots"]
        event_fields = {
            "case": runner_case, "status": "xfail", "observed": "fail",
            "observed_disposition": "expected-failure", "reason": evaluator["reason"],
            "source_path": source["source_path"], "source_revision": source["source_commit"],
            "fixture_sha256": output["sha256"], "manifest_sha256": identity["mooneye_manifest_sha256"],
            "core_revision": identity["core_revision"], "runner_revision": identity["core_revision"],
            "profile": "CGB-CPU-E", "boot": "skipped", "protocol": "mooneye-ld-b-b",
            "eligible": "1", "executed": "1", "stop": "protocol-result",
            "ticks": str(ticks), "budget": str(budget),
        }
        def mooneye_output(fields):
            event = " ".join(f"{key}={value}" for key, value in fields.items())
            assertion = (f"assertion case={runner_case} id=ld-b-b-result expected=pass observed=fail "
                         f"evaluator_status=xfail callback_pc={evaluator['callback_pc'][2:]} "
                         f"result_pc={evaluator['result_pc'][2:]} terminal=1 ticks={ticks} budget={budget}")
            return event + "\n" + assertion + "\n"
        self.assertTrue(report._normalize_mooneye(mooneye_item, mooneye_output(event_fields), identity)["matched_xfail"])
        for fields, item, code in (
            ({**event_fields, "boot": "bootless"}, mooneye_item, "mooneye-identity-mismatch"),
            ({**event_fields, "core_revision": "0" * 40}, mooneye_item, "mooneye-identity-mismatch"),
            ({**event_fields, "fixture_sha256": "0" * 64}, mooneye_item, "mooneye-identity-mismatch"),
            ({**event_fields, "manifest_sha256": "0" * 64}, mooneye_item, "mooneye-identity-mismatch"),
            ({**event_fields, "profile": "CGB-CPU-D"}, mooneye_item, "mooneye-identity-mismatch"),
            ({**event_fields, "reason": "changed"}, mooneye_item, "mooneye-result-mismatch"),
            (event_fields, {**mooneye_item, "case": {**case, "mode": "native"}}, "mooneye-case-profile"),
            (event_fields, {**mooneye_item, "case": {**case, "speed": "double"}}, "mooneye-case-profile"),
            (event_fields, {**mooneye_item, "case": {**case, "model": "CGB-E"}}, "mooneye-case-profile"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(report.ReportError) as raised:
                    report._normalize_mooneye(item, mooneye_output(fields), identity)
                self.assertEqual(raised.exception.code, code)
        with self.assertRaises(report.ReportError) as raised:
            report._normalize_mooneye(mooneye_item, mooneye_output(event_fields).split("assertion ")[0], identity)
        self.assertEqual(raised.exception.code, "mooneye-terminal-membership")

        log = good_log
        log_digest = report.sha256(log)
        run_metadata = {
            "schema": report.RUN_ID_SCHEMA, "status": "complete", "ctest_exit_code": 0,
            "input_identity_sha256": "a" * 64, "ctest_names": [one],
            "log_sha256": log_digest, "started_at_ns": 1, "completed_at_ns": 2,
            "run_id": report._run_id("a" * 64, log_digest, 1, 2),
        }
        with tempfile.TemporaryDirectory(prefix="cgb-report-run-", dir=BUILD_DIR) as temp:
            run_dir = Path(temp)
            (run_dir / "cgb-corpus-ctest.log").write_bytes(log)
            report.write_receipt(run_dir / "cgb-corpus-run.json", run_metadata)
            self.assertEqual(report._load_existing_ctest_run(run_dir, {"identity_sha256": "a" * 64}, {one})[0], log)
            run_metadata["input_identity_sha256"] = "b" * 64
            report.write_receipt(run_dir / "cgb-corpus-run.json", run_metadata)
            with self.assertRaises(report.ReportError) as raised:
                report._load_existing_ctest_run(run_dir, {"identity_sha256": "a" * 64}, {one})
            self.assertEqual(raised.exception.code, "ctest-run-identity-mismatch")

        with self.assertRaises(report.ReportError) as raised:
            report.run_bounded([sys.executable, "-c", "import time; time.sleep(1)"], timeout_seconds=0.05)
        self.assertEqual(raised.exception.code, "runner-timeout")

        with tempfile.TemporaryDirectory(prefix="cgb-report-late-failure-", dir=BUILD_DIR) as temp:
            receipt_path = Path(temp) / "receipt.json"
            receipt_path.write_text('{"schema":"gabbaboy-cgb-corpus-receipt-v1","status":"complete"}\n',
                                    encoding="utf-8")
            arguments = [str(REPORTER), "--from-ctest", "--build-dir", str(BUILD_DIR),
                         "--receipt", str(receipt_path)]
            with mock.patch.object(report, "build_corpus_report",
                                   side_effect=report.ReportError("ctest-log-incomplete")):
                with mock.patch.object(sys, "argv", arguments):
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        exit_code = report.main()
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertNotEqual(exit_code, 0)
            self.assertEqual(receipt.get("status"), "incomplete")
            self.assertEqual(receipt.get("failure_codes"), ["ctest-log-incomplete"])


class PrivatePathFreeResult(unittest.TextTestResult):
    def _exc_info_to_string(self, err, test):
        return "{}: {}".format(err[0].__name__, err[1])


class PrivatePathFreeRunner(unittest.TextTestRunner):
    resultclass = PrivatePathFreeResult


if __name__ == "__main__":
    unittest.main(testRunner=PrivatePathFreeRunner)
