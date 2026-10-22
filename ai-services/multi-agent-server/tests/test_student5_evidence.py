import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import evidence
from agents.worker_agent import format_evidence


class Student5EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.records = {
            "/api/performance-reviews": [{
                "reviewID": 11, "staffID": 1, "rating": 4.5,
                "feedback": "Strong teaching leadership", "status": "Completed",
            }],
            "/api/development-goals": [{
                "goalID": 12, "staffID": 1, "title": "Strengthen academic leadership",
                "description": "Complete leadership training", "progress": 0,
                "targetDate": "2026-11-30", "status": "In Progress",
            }],
            "/api/training-programs": [{
                "trainingID": 13, "title": "Academic Leadership Foundations",
                "skillArea": "Leadership", "provider": "UTS Learning Hub",
            }],
            "/api/staff-training": [{
                "staffID": 1, "trainingID": 13, "staffTrainingID": 14,
                "status": "Enrolled", "completionDate": None,
            }],
            "/api/development-recommendations": [{
                "recommendationID": 15, "staffID": 1, "goalID": 12,
                "recommendationType": "Training", "status": "Pending",
                "recommendation": "Complete Academic Leadership Foundations",
            }],
            "/api/integration/staff": {
                "staff": [{"staff_id": 1, "name": "John Smith", "email": "private@example.com"}]
            },
        }
        api_patch = patch.object(evidence, "fetch_json")
        self.call_api = api_patch.start()
        self.addCleanup(api_patch.stop)
        self.call_api.side_effect = lambda base, path: self.records[path]

    def test_collects_all_five_resources_with_source_ids_and_links(self):
        items = evidence.student5_evidence()
        by_source = {item["source"]: item["record"] for item in items}

        self.assertEqual(set(by_source), {
            "student5/performance-reviews/11", "student5/development-goals/12",
            "student5/training-programs/13", "student5/staff-training/14",
            "student5/development-recommendations/15",
        })
        self.assertEqual(by_source["student5/development-goals/12"]["progress"], 0)
        self.assertEqual(by_source["student5/staff-training/14"]["trainingTitle"],
                         "Academic Leadership Foundations")
        recommendation = by_source["student5/development-recommendations/15"]
        self.assertEqual(recommendation["goalTitle"], "Strengthen academic leadership")
        self.assertEqual(recommendation["status"], "Pending")
        self.assertEqual(recommendation["actionState"], "Proposed recommendation")
        self.assertEqual(by_source["student5/performance-reviews/11"]["staffName"], "John Smith")
        self.assertNotIn("private@example.com", str(items))
        self.assertEqual(self.call_api.call_count, 6)
        for call in self.call_api.call_args_list:
            self.assertEqual(call.args[0], evidence.STUDENT5_BACKEND_URL)

    def test_enrolments_for_the_same_staff_have_distinct_sources(self):
        self.records["/api/staff-training"].append({
            "staffID": 1, "trainingID": 13, "staffTrainingID": 16, "status": "Completed",
        })

        items = evidence.student5_evidence()
        sources = [item["source"] for item in items]

        self.assertEqual(len(sources), len(set(sources)))
        self.assertIn("student5/staff-training/14", sources)
        self.assertIn("student5/staff-training/16", sources)

    def test_staff_directory_failure_keeps_staff_ids(self):
        def fetch(base, path):
            if path == "/api/integration/staff":
                raise evidence.EvidenceError("staff service unavailable")
            return self.records[path]

        self.call_api.side_effect = fetch
        items = evidence.student5_evidence()

        self.assertEqual(items[0]["record"]["staffID"], 1)
        self.assertNotIn("staffName", items[0]["record"])
        self.assertEqual(len(items), 5)

    def test_required_api_failure_reports_unavailable_evidence(self):
        def fetch(base, path):
            if path == "/api/staff-training":
                raise evidence.EvidenceError("database service unavailable")
            return self.records[path]

        self.call_api.side_effect = fetch

        with self.assertRaisesRegex(evidence.EvidenceError, "database service unavailable"):
            evidence.collect_evidence("student5", "Review development goals")

    def test_invalid_resource_responses_raise_evidence_error(self):
        for response in ({"error": "unavailable"}, [None], [{"staffID": 1}]):
            with self.subTest(response=response):
                self.records["/api/performance-reviews"] = response
                with self.assertRaises(evidence.EvidenceError):
                    evidence.student5_evidence()

    def test_empty_resources_return_no_evidence(self):
        self.call_api.side_effect = lambda base, path: (
            {"staff": []} if path == "/api/integration/staff" else []
        )

        items, available = evidence.collect_evidence("student5", "Review development goals")

        self.assertEqual(items, [])
        self.assertEqual(available, 0)

    def test_missing_links_keep_ids_without_inventing_titles(self):
        self.records["/api/training-programs"] = []
        self.records["/api/development-goals"] = []
        items = evidence.student5_evidence()
        by_source = {item["source"]: item["record"] for item in items}

        enrolment = by_source["student5/staff-training/14"]
        recommendation = by_source["student5/development-recommendations/15"]
        self.assertEqual(enrolment["trainingID"], 13)
        self.assertNotIn("trainingTitle", enrolment)
        self.assertEqual(recommendation["goalID"], 12)
        self.assertNotIn("goalTitle", recommendation)

    def test_goal_progress_and_dates_survive_worker_text_limit(self):
        goal = self.records["/api/development-goals"][0]
        goal["description"] = "Detailed goal background. " * 30
        items, available = evidence.collect_evidence("student5", "Strengthen academic leadership")
        goal_item = next(item for item in items if item["source"] == "student5/development-goals/12")
        text = format_evidence([goal_item])

        self.assertEqual(available, 5)
        self.assertIn("progress=0", text)
        self.assertIn("targetDate=2026-11-30", text)
        self.assertNotIn("TODO", evidence.describe_features()["student5"]["evidence_description"])

    def test_pending_recommendation_survives_long_rationale(self):
        self.records["/api/development-recommendations"] = [{
            "dateGenerated": "2026-10-22", "goalID": 12,
            "rationale": "Detailed recommendation background. " * 30,
            "recommendation": "Complete Academic Leadership Foundations",
            "recommendationID": 15, "recommendationType": "Training",
            "staffID": 1, "status": "Pending",
        }]
        items = evidence.student5_evidence()
        recommendation = next(item for item in items
                              if item["source"] == "student5/development-recommendations/15")
        text = format_evidence([recommendation])

        self.assertIn("actionState=Proposed recommendation", text)
        self.assertIn("status=Pending", text)
        self.assertIn("recommendation=Complete Academic Leadership Foundations", text)


if __name__ == "__main__":
    unittest.main()
