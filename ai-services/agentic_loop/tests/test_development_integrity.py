import sys
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from collectors.development_integrity_collector import collect
from config.review_config import build_mode_config
from core.prompt_registry import PromptRegistry
from pipelines.development_integrity_pipeline import build_user_prompt


class DevelopmentIntegrityCollectorTests(unittest.TestCase):
    def test_collects_real_student_5_integrity_evidence(self):
        student_dir = REPO_ROOT / "student-5Matthew-Barnard"

        ok, evidence = collect(student_dir, "5")

        self.assertTrue(ok)
        self.assertIn("real database was not modified", evidence)
        self.assertIn(
            "REJECTED: Completed development goal with progress=25", evidence
        )
        self.assertNotIn("staff training with", evidence)

    def test_pipeline_inserts_only_supplied_values(self):
        prompt = build_user_prompt(
            "Review {{REVIEW_TARGET}} using {{INTEGRITY_EVIDENCE}}",
            "Context",
            "Student 5",
            "measured evidence",
        )

        self.assertEqual(
            prompt, "Context\n\nReview Student 5 using measured evidence"
        )

    def test_mode_is_scoped_to_student_5(self):
        mode = build_mode_config()["development_integrity"]

        self.assertEqual(mode.student_numbers, ("5",))
        self.assertEqual(len(mode.implementation_prompts), 3)

    def test_existing_modes_and_prompts_remain_available(self):
        modes = build_mode_config()
        registry = PromptRegistry(APP_DIR)

        self.assertTrue(
            {"db", "endpoints", "architecture", "ai_mode"}.issubset(modes)
        )
        for key in ("db", "endpoints", "architecture", "ai_mode"):
            mode = modes[key]
            for relative_prompt in (
                *mode.implementation_prompts,
                *mode.review_prompts,
            ):
                self.assertTrue(registry.read(mode.prompt_family, relative_prompt))


if __name__ == "__main__":
    unittest.main()
