"""Testing review regression tests (no live tests or network invoked)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from collectors.testing_report_collector import (
    collect,
    inspect_security_report,
    inspect_test_report,
)
from collectors.fresh_test_runner import SAFE_SUITES, WORKFLOWS, suite_environment
from config.review_config import build_mode_config
from core.prompt_registry import PromptRegistry


class TestingReportReviewTests(unittest.TestCase):
    def test_mode_and_prompts_registered(self):
        cfg = build_mode_config()["testing_report_review"]
        self.assertFalse(cfg.per_student)
        registry = PromptRegistry(APP_DIR)
        for rel in (*cfg.implementation_prompts, *cfg.review_prompts):
            self.assertTrue(registry.read(cfg.prompt_family, rel))

    def test_stale_endpoint_report_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "endpoint-tests.txt"
            report.write_text("7 passed in 0.91s\n", encoding="utf-8")
            status, detail = inspect_test_report(report, 13)
            self.assertEqual(status, "STALE_OR_INCOMPLETE")
            self.assertIn("13", detail)

    def test_three_security_scans_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "precommit-results.txt"
            report.write_text(
                "Ruff Security Scan........Passed\n"
                "Secret Detection..........Passed\n"
                "Dependency Audit..........Passed\n",
                encoding="utf-8",
            )
            status, _ = inspect_security_report(report)
            self.assertEqual(status, "PASS_RECORDED")

    def test_no_reports_cannot_pass_in_saved_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {"AGENTIC_TEST_RUN_MODE": "saved"}):
                ok, evidence = collect(root / "ai-services/agentic_loop", root)
            self.assertFalse(ok)
            self.assertIn("OBSERVE FAILED", evidence)

    def test_safe_suite_registry_has_no_shell_or_docker(self):
        self.assertEqual(set(SAFE_SUITES), {1, 2, 3, 4, 5})
        self.assertEqual(SAFE_SUITES[3], [])
        self.assertEqual(set(WORKFLOWS), {1, 2, 3, 4, 5})
        for suites in SAFE_SUITES.values():
            for _, kind, path in suites:
                self.assertIn(kind, {"pytest", "unittest", "unittest_discover"})
                self.assertTrue(path.startswith("student-"))

    def test_student_4_import_path_is_scoped_to_route_test(self):
        base = {"AI_MODE_ENABLED": "false", "PYTHONPATH": "existing"}
        root = Path("/example/repository")
        actual = suite_environment(
            base, 4, "research-route-registration", root
        )
        self.assertTrue(actual["PYTHONPATH"].startswith(
            str(root / "student-4Nicholas-Hatzidimitriou" / "backend")
        ))
        self.assertIn("existing", actual["PYTHONPATH"])
        self.assertEqual(actual["AI_MODE_ENABLED"], "false")
        self.assertEqual(base["PYTHONPATH"], "existing")

    def test_student_5_mocked_ai_tests_enable_ai_mode_only_for_that_suite(self):
        base = {"AI_MODE_ENABLED": "false"}
        root = Path("/example/repository")
        backend_env = suite_environment(base, 5, "performance-backend", root)
        database_env = suite_environment(base, 5, "performance-database", root)
        staff_env = suite_environment(base, 1, "staff-pytest", root)
        self.assertEqual(backend_env["AI_MODE_ENABLED"], "true")
        self.assertEqual(database_env["AI_MODE_ENABLED"], "false")
        self.assertEqual(staff_env["AI_MODE_ENABLED"], "false")
        self.assertEqual(base["AI_MODE_ENABLED"], "false")

    @patch("collectors.testing_report_collector.fresh_test_runner.check_current_commit_ci")
    @patch("collectors.testing_report_collector.fresh_test_runner.run_local_suites")
    def test_fresh_mode_uses_live_execution_not_saved_report(
        self, run_local_suites, check_ci
    ):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            student2 = root / "student-2-test"
            reports = student2 / "reports" / "release2"
            reports.mkdir(parents=True)
            (reports / "endpoint-tests.txt").write_text("7 passed\n", encoding="utf-8")

            run_local_suites.return_value = {
                "commit": "a" * 40,
                "branch": "test-branch",
                "timestamp": "2026-10-22T00:00:00+00:00",
                "local_tracked_changes": False,
                "summary_path": "reports/release2/live-tests/test/summary.json",
                "students": {
                    1: [],
                    2: [{
                        "suite": "allocation-endpoints", "status": "PASS",
                        "test_count": 13, "exit_code": 0, "log": "mock.log",
                    }],
                    3: [], 4: [], 5: [],
                },
            }
            check_ci.return_value = (
                {i: "CI_UNVERIFIED" for i in range(1, 6)},
                "No current CI result",
            )

            with patch.dict(os.environ, {"AGENTIC_TEST_RUN_MODE": "fresh"}):
                ok, evidence = collect(root / "ai-services/agentic_loop", root)

            self.assertTrue(ok)
            self.assertIn("Collection mode: FRESH", evidence)
            self.assertIn("allocation-endpoints=PASS", evidence)
            self.assertIn("saved_endpoint_report: NOT_USED_FOR_FRESH_RESULT", evidence)
            self.assertIn("DETERMINISTIC VERDICT: NOT_READY", evidence)
            run_local_suites.assert_called_once()
            check_ci.assert_called_once_with("a" * 40)

    def test_invalid_mode_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {"AGENTIC_TEST_RUN_MODE": "unknown"}):
                ok, evidence = collect(root / "ai-services/agentic_loop", root)
            self.assertFalse(ok)
            self.assertIn("unknown", evidence)


if __name__ == "__main__":
    unittest.main()
