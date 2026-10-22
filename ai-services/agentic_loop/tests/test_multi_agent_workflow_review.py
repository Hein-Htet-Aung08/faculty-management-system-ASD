
import json
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from collectors.multi_agent_workflow_collector import collect
from config.review_config import build_mode_config
from core.prompt_registry import PromptRegistry
from pipelines.multi_agent_workflow_pipeline import (
    build_implementation_prompt,
    build_review_prompt,
)


class MultiAgentWorkflowReviewTests(unittest.TestCase):

    def test_mode_and_prompts_registered(self):
        cfg = build_mode_config()[
            "multi_agent_workflow_review"
        ]

        self.assertFalse(cfg.per_student)

        registry = PromptRegistry(APP_DIR)

        for relative in (
            *cfg.implementation_prompts,
            *cfg.review_prompts,
        ):
            self.assertTrue(
                registry.read(cfg.prompt_family, relative)
            )

    def test_prompt_includes_supplied_evidence(self):
        implementation = build_implementation_prompt(
            "Review the workflow",
            "REAL_EVIDENCE",
        )

        self.assertIn("REAL_EVIDENCE", implementation)

        review = build_review_prompt(
            "FIRST_ASSESSMENT",
            "REAL_EVIDENCE",
        )

        self.assertIn("FIRST_ASSESSMENT", review)
        self.assertIn("REAL_EVIDENCE", review)

    def test_missing_evidence_does_not_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app_dir = root / "ai-services" / "agentic_loop"

            ok, evidence = collect(app_dir, root)

            self.assertFalse(ok)
            self.assertIn("OBSERVE FAILED", evidence)

    def test_joins_workflow_with_human_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            source = (
                root
                / "student-2-test"
                / "reports"
                / "release2"
                / "multi-agent"
            )
            source.mkdir(parents=True)

            workflow = {
                "event": "workflow",
                "workflow_id": "test-123",
                "feature": "student2",
                "planner_result": {"status": "success"},
                "worker_result": {
                    "status": "success",
                    "evidence_count": 3,
                },
                "reviewer_result": {"status": "success"},
                "automated_checks": [
                    {
                        "check": "citations_exist",
                        "passed": False,
                    },
                ],
            }

            decision = {
                "event": "human_decision",
                "workflow_id": "test-123",
                "decision": "Correct",
            }

            events = [
                "workflow_started",
                "planner_completed",
                "evidence_collected",
                "worker_completed",
                "automated_checks_completed",
                "reviewer_completed",
                "awaiting_human_review",
                "human_decision_recorded",
            ]

            audit = [
                {
                    "workflow_id": "test-123",
                    "event": event,
                }
                for event in events
            ]

            history_file = (
                source / "workflow_history.jsonl"
            )
            audit_file = (
                source / "coordination_audit.jsonl"
            )

            history_file.write_text(
                "\n".join(
                    json.dumps(item)
                    for item in (workflow, decision)
                ) + "\n",
                encoding="utf-8",
            )

            audit_file.write_text(
                "\n".join(
                    json.dumps(item) for item in audit
                ) + "\n",
                encoding="utf-8",
            )

            ok, evidence = collect(
                root / "ai-services" / "agentic_loop",
                root,
            )

            self.assertTrue(ok)
            self.assertIn("test-123", evidence)
            self.assertIn("Correct", evidence)
            self.assertIn("citations_exist", evidence)
            self.assertIn("REVIEW_REQUIRED", evidence)


if __name__ == "__main__":
    unittest.main()
