
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from collectors.testing_report_collector import (
    collect,
    inspect_test_report,
    inspect_security_report,
)
from config.review_config import build_mode_config
from core.prompt_registry import PromptRegistry


class TestingReportReviewTests(unittest.TestCase):

    def test_mode_and_prompts_registered(self):
        cfg = build_mode_config()["testing_report_review"]

        self.assertFalse(cfg.per_student)

        registry = PromptRegistry(APP_DIR)

        for relative in (
            *cfg.implementation_prompts,
            *cfg.review_prompts,
        ):
            self.assertTrue(
                registry.read(cfg.prompt_family, relative)
            )

    def test_stale_endpoint_report_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            report = Path(temp) / "endpoint-tests.txt"
            report.write_text(
                "7 passed in 0.91s\n",
                encoding="utf-8",
            )

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

    def test_no_reports_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ok, evidence = collect(
                root / "ai-services" / "agentic_loop",
                root,
            )

            self.assertFalse(ok)
            self.assertIn("OBSERVE FAILED", evidence)


if __name__ == "__main__":
    unittest.main()
