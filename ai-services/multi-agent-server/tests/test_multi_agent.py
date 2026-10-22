import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import openai


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as server
import coordinator
import evidence
from agents.llm_client import parse_sections


EVIDENCE = [
    {"source": "student3/profiles/1", "record": {"staff_name": "John Smith", "status": "overloaded"}},
    {"source": "student3/alerts/1", "record": {"alert_type": "overload", "staff_id": 1}},
]


def fake_chat(model, prompt, **kwargs):
    if "Planner Agent" in prompt:
        return "Objective: List overloaded staff.\nSteps: 1. Read profiles.\nEvidence Required: profiles.\nHuman Approval: Required."
    if "Worker Agent" in prompt:
        return "Output: John Smith is overloaded [student3/profiles/1].\nEvidence Used: student3/profiles/1\nLimitations: None."
    return "Risk: Low.\nCorrection: None.\nRetest: Not needed.\nRecommendation: Accept."


class TempLogs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        patches = [
            patch.object(coordinator, "HISTORY_PATH", tmp / "history.jsonl"),
            patch.object(coordinator, "AUDIT_PATH", tmp / "audit.jsonl"),
            patch("agents.planner_agent.chat", side_effect=fake_chat),
            patch("agents.worker_agent.chat", side_effect=fake_chat),
            patch("agents.reviewer_agent.chat", side_effect=fake_chat),
            patch.object(coordinator, "collect_evidence", return_value=(EVIDENCE, 2)),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self.tmp.cleanup)


class WorkflowTests(TempLogs):
    def test_runs_planner_worker_reviewer_then_waits_for_human(self):
        result = coordinator.run_workflow("Which staff are overloaded?", "student3")

        self.assertEqual(result["status"], "awaiting_human_review")
        self.assertEqual(result["planner_result"]["sections"]["Objective"], "List overloaded staff.")
        self.assertEqual(result["worker_result"]["evidence_count"], 2)
        self.assertEqual(result["reviewer_result"]["sections"]["Recommendation"], "Accept.")
        self.assertEqual(result["human_decision"]["status"], "pending")

    def test_audit_log_records_each_coordination_step(self):
        result = coordinator.run_workflow("Which staff are overloaded?", "3")
        events = [r["event"] for r in coordinator.read_jsonl(coordinator.AUDIT_PATH)]

        self.assertEqual(events, [
            "workflow_started", "planner_completed", "evidence_collected", "worker_completed",
            "automated_checks_completed", "reviewer_completed", "awaiting_human_review",
        ])
        self.assertEqual(result["feature"], "student3")

    def test_automated_checks_pass_for_grounded_output(self):
        result = coordinator.run_workflow("Which staff are overloaded?", "student3")
        self.assertTrue(all(c["passed"] for c in result["automated_checks"]), result["automated_checks"])

    def test_automated_checks_flag_missing_output_and_unknown_citation(self):
        def bad_worker(model, prompt, **kwargs):
            return "Evidence Used: [student3/profiles/99]\nLimitations: None."

        with patch("agents.worker_agent.chat", side_effect=bad_worker):
            result = coordinator.run_workflow("Which staff are overloaded?", "student3")

        failed = {c["check"] for c in result["automated_checks"] if not c["passed"]}
        self.assertEqual(failed, {"sections_present", "output_not_empty", "citations_exist"})

    def test_human_decision_is_recorded_once(self):
        workflow_id = coordinator.run_workflow("Which staff are overloaded?", "student3")["workflow_id"]

        final = coordinator.record_decision(workflow_id, "partially accept", "Tristan", "Check hours")
        self.assertEqual(final["status"], "partially_accepted")
        self.assertEqual(coordinator.get_workflow(workflow_id)["human_decision"]["reviewer"], "Tristan")

        with self.assertRaises(coordinator.DecisionConflict):
            coordinator.record_decision(workflow_id, "Accept")

    def test_correct_decision_requires_a_correction(self):
        workflow_id = coordinator.run_workflow("Which staff are overloaded?", "student3")["workflow_id"]

        with self.assertRaises(ValueError):
            coordinator.record_decision(workflow_id, "Correct")
        final = coordinator.record_decision(workflow_id, "Correct", correction="Priya Nair is also overloaded.")
        self.assertEqual(final["status"], "corrected")

    def test_rejects_unknown_feature_and_blank_request(self):
        with self.assertRaises(ValueError):
            coordinator.run_workflow("Anything", "student9")
        with self.assertRaises(ValueError):
            coordinator.run_workflow("   ", "student3")

    def test_status_counts_pending_and_decided(self):
        first = coordinator.run_workflow("Which staff are overloaded?", "student3")["workflow_id"]
        coordinator.run_workflow("Open alerts?", "student3")
        coordinator.record_decision(first, "Reject")

        status = coordinator.workflow_status()
        self.assertEqual(status["workflow_history_count"], 2)
        self.assertEqual(status["pending_human_review"], 1)
        self.assertEqual(status["decisions"], {"Reject": 1})


class FailureTests(TempLogs):
    def test_unreachable_backend_gives_no_evidence_without_calling_worker_model(self):
        with patch.object(coordinator, "collect_evidence", side_effect=evidence.EvidenceError("down")), \
                patch("agents.worker_agent.chat") as worker_chat:
            result = coordinator.run_workflow("Which staff are overloaded?", "student3")

        worker_chat.assert_not_called()
        self.assertEqual(result["worker_result"]["status"], "no_evidence")
        self.assertEqual(result["worker_result"]["evidence_error"], "down")

    def test_ollama_failure_falls_back_and_still_needs_human_review(self):
        error = openai.APIConnectionError(request=None)
        with patch("agents.planner_agent.chat", side_effect=error), \
                patch("agents.reviewer_agent.chat", side_effect=error):
            result = coordinator.run_workflow("Which staff are overloaded?", "student3")

        self.assertEqual(result["planner_result"]["status"], "fallback")
        self.assertEqual(result["reviewer_result"]["status"], "error")
        self.assertIn("Do not accept", result["reviewer_result"]["review"])
        self.assertEqual(result["status"], "awaiting_human_review")


class EvidenceTests(unittest.TestCase):
    def test_student3_labels_alerts_with_staff_names_and_drops_private_fields(self):
        responses = {
            "/api/staff-workload/profiles": [{"profile_id": 1, "staff_id": 1, "staff_name": "John Smith",
                                              "department": "Computer Science", "email": "j@x"}],
            "/api/staff-workload/alerts": [{"alert_id": 7, "staff_id": 1, "alert_type": "overload"}],
        }
        with patch.object(evidence, "fetch_json", side_effect=lambda base, path, params=None: responses[path]):
            items = evidence.student3_evidence()

        self.assertEqual([i["source"] for i in items], ["student3/profiles/1", "student3/alerts/7"])
        self.assertNotIn("email", items[0]["record"])
        self.assertEqual(items[1]["record"]["staff_name"], "John Smith")
        self.assertEqual(items[1]["record"]["department"], "Computer Science")

    def test_student4_denormalises_project_title_onto_each_grant(self):
        responses = {
            "/projects": [{"projectID": 1, "title": "AI-Driven Curriculum Analytics",
                           "department": "Computer Science", "status": "in progress"}],
            "/projects/1/grants": [{"grantID": 10, "projectID": 1, "fundingBody": "ARC",
                                    "amountRequested": 150000, "status": "awarded"}],
            "/ai-analysis": [{"analysisID": 5, "projectID": 1, "generatedSummary": "Strong progress."}],
        }
        with patch.object(evidence, "fetch_json", side_effect=lambda base, path, params=None: responses[path]):
            items = evidence.student4_evidence()

        self.assertEqual(
            [i["source"] for i in items],
            ["student4/projects/1", "student4/grants/10", "student4/research_history/5"],
        )
        self.assertEqual(items[1]["record"]["projectTitle"], "AI-Driven Curriculum Analytics")

    def test_unfilled_sections_report_not_implemented(self):
        for student in (1, 5):
            with self.assertRaisesRegex(evidence.EvidenceError, f"Student {student} evidence is not implemented"):
                evidence.FEATURES[f"student{student}"]["collect"]()

    def test_select_relevant_prefers_matching_records(self):
        items = [
            {"source": "a", "record": {"status": "underloaded"}},
            {"source": "b", "record": {"status": "overloaded"}},
        ]
        self.assertEqual(evidence.select_relevant(items, "who is overloaded", limit=1)[0]["source"], "b")

    def test_normalise_feature(self):
        self.assertEqual(evidence.normalise_feature("Student 3"), "student3")
        self.assertEqual(evidence.normalise_feature(5), "student5")
        self.assertIsNone(evidence.normalise_feature("student9"))

    def test_parse_sections_handles_markdown_bold_headings(self):
        sections = parse_sections("**Risk:** Low\n**Recommendation:** Accept", ["Risk", "Recommendation"])
        self.assertEqual(sections, {"Risk": "Low", "Recommendation": "Accept"})

    
    def test_student2_collects_all_four_evidence_types(self):
        context = {
            "subjects": [
                {"subject_code": "41114", "name": "Advanced Software Development"}
            ],
            "subject_offers": [
                {"offer_id": "41114_SPR_2026", "year": "2026"}
            ],
            "classrooms": [
                {"classroom_id": "CB11.04.406", "capacity": 30}
            ],
            "teaching_allocations": [
                {"allocation_id": 4, "classroom_id": "CB11.04.406",
                 "email": "private@example.com"}
            ],
        }

        with patch.object(evidence, "fetch_json", return_value=context):
            items = evidence.student2_evidence()

        self.assertEqual(
            [item["source"] for item in items],
            [
                "student2/subjects/41114",
                "student2/subject_offers/41114_SPR_2026",
                "student2/classrooms/CB11.04.406",
                "student2/teaching_allocations/4",
            ],
        )
        self.assertNotIn("email", items[3]["record"])



class ApiTests(TempLogs):
    def setUp(self):
        super().setUp()
        self.client = server.app.test_client()

    def test_workflow_then_decision_over_http(self):
        response = self.client.post("/workflow", json={"user_request": "Overloaded staff?", "feature": "student3"})
        self.assertEqual(response.status_code, 200)
        workflow_id = response.get_json()["workflow_id"]

        decided = self.client.post(f"/workflow/{workflow_id}/decision", json={"decision": "Accept"})
        self.assertEqual(decided.get_json()["status"], "accepted")
        self.assertEqual(self.client.post(f"/workflow/{workflow_id}/decision", json={"decision": "Reject"}).status_code, 409)
        self.assertEqual(self.client.get("/workflow/history?feature=student3").get_json()["workflows"][0]["decision"], "Accept")

    def test_bad_requests_return_400_and_404(self):
        self.assertEqual(self.client.post("/workflow", json={"feature": "student3"}).status_code, 400)
        self.assertEqual(self.client.post("/workflow", json={"user_request": "x", "feature": "nope"}).status_code, 400)
        self.assertEqual(self.client.get("/workflow/missing-id").status_code, 404)
        self.assertEqual(self.client.post("/workflow/missing-id/decision", json={"decision": "Accept"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
