import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import rag_pipeline


RECORDS = {
    "/api/performance-reviews": [{
        "reviewID": 1, "staffID": 1, "reviewDate": "2026-02-12",
        "reviewerID": 5, "rating": 4.5, "feedback": "Strong teaching leadership",
        "status": "Completed",
    }],
    "/api/development-goals": [{
        "goalID": 1, "staffID": 1, "title": "Strengthen academic leadership",
        "description": "Complete leadership training", "targetDate": "2026-11-30",
        "progress": 0, "status": "In Progress",
    }],
    "/api/training-programs": [{
        "trainingID": 1, "title": "Academic Leadership Foundations",
        "description": "Leadership fundamentals", "provider": "UTS Learning Hub",
        "startDate": "2026-09-10", "endDate": "2026-09-24",
        "skillArea": "Leadership",
    }],
    "/api/staff-training": [{
        "staffTrainingID": 1, "staffID": 1, "trainingID": 1,
        "enrolmentDate": "2026-08-20", "completionDate": None,
        "status": "Enrolled",
    }],
    "/api/development-recommendations": [{
        "recommendationID": 1, "staffID": 1, "goalID": 1,
        "recommendationType": "Training",
        "recommendation": "Complete Academic Leadership Foundations",
        "rationale": "Supports the leadership goal",
        "dateGenerated": "2026-08-29", "status": "Pending",
    }],
    "/api/integration/staff": {
        "staff": [{"staff_id": 1, "name": "John Smith", "email": "private@example.com"}]
    },
}


class Student5ContextTests(unittest.TestCase):
    @patch("rag_pipeline.call_feature_api")
    def test_loader_builds_cited_chunks_from_backend_records(self, call_api):
        call_api.side_effect = lambda method, base, path: RECORDS[path]

        chunks = rag_pipeline.load_student5_context()
        by_id = {chunk["chunk_id"]: chunk for chunk in chunks}

        self.assertEqual(set(by_id), {
            "student5_reviews_1", "student5_goals_1", "student5_programs_1",
            "student5_training_1", "student5_recommendations_1",
            "student5_summary_counts",
        })
        for chunk in chunks:
            self.assertEqual(chunk["student"], 5)
            self.assertEqual(chunk["authority_tier"], "tier_1")
            self.assertEqual(chunk["feature"], "performance_professional_development")
            self.assertTrue(chunk["source_id"].startswith("student5/"))
        self.assertEqual(by_id["student5_goals_1"]["source_id"], "student5/development-goals/1")
        self.assertIn("Progress: 0%", by_id["student5_goals_1"]["text"])
        self.assertIn("Academic Leadership Foundations", by_id["student5_training_1"]["text"])
        self.assertIn("Decision status: Pending", by_id["student5_recommendations_1"]["text"])
        self.assertIn("Related goal: Strengthen academic leadership", by_id["student5_recommendations_1"]["text"])
        self.assertIn("not proof", by_id["student5_recommendations_1"]["text"])
        self.assertIn("John Smith", by_id["student5_reviews_1"]["text"])
        self.assertNotIn("private@example.com", " ".join(chunk["text"] for chunk in chunks))
        self.assertEqual(call_api.call_count, 6)
        for call in call_api.call_args_list:
            self.assertEqual(call.args[0], "GET")
            self.assertEqual(call.args[1], rag_pipeline.STUDENT5_BACKEND_URL)
            self.assertTrue(call.args[2].startswith("/api/"))

    @patch("rag_pipeline.call_feature_api")
    def test_staff_ids_remain_when_directory_unavailable(self, call_api):
        def fake_api(method, base, path):
            if path == "/api/integration/staff":
                raise requests.ConnectionError("staff service unavailable")
            return RECORDS[path]

        call_api.side_effect = fake_api
        chunks = rag_pipeline.load_student5_context()
        review = next(chunk for chunk in chunks if chunk["chunk_id"] == "student5_reviews_1")
        self.assertIn("staff ID 1", review["text"])

    @patch("rag_pipeline.call_feature_api")
    def test_required_api_failure_returns_no_partial_corpus(self, call_api):
        def fake_api(method, base, path):
            if path == "/api/staff-training":
                raise requests.ConnectionError("backend unavailable")
            return RECORDS[path]

        call_api.side_effect = fake_api
        self.assertEqual(rag_pipeline.load_student5_context(), [])

    @patch("rag_pipeline.call_feature_api")
    def test_empty_resources_have_only_a_totals_chunk(self, call_api):
        call_api.side_effect = lambda method, base, path: (
            {"staff": []} if path == "/api/integration/staff" else []
        )
        chunks = rag_pipeline.load_student5_context()
        self.assertEqual([chunk["chunk_id"] for chunk in chunks], ["student5_summary_counts"])
        self.assertIn("0 performance review(s)", chunks[0]["text"])


if __name__ == "__main__":
    unittest.main()
