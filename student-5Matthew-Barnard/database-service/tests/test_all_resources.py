import os
import sys
import tempfile
import unittest
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))


class AllResourceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "resources.db")
        from app import create_app
        cls.app = create_app({"TESTING": True})

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
        os.environ.pop("DATABASE_PATH", None)

    def setUp(self):
        self.client = self.app.test_client()

    def _create_update_delete(self, resource, primary_key, payload, update):
        created = self.client.post(f"/{resource}", json=payload)
        self.assertEqual(created.status_code, 201, created.get_data(as_text=True))
        row_id = created.json[primary_key]

        updated = self.client.put(f"/{resource}/{row_id}", json=update)
        self.assertEqual(updated.status_code, 200, updated.get_data(as_text=True))
        for field, expected in update.items():
            self.assertEqual(updated.json[field], expected)

        deleted = self.client.delete(f"/{resource}/{row_id}")
        self.assertEqual(deleted.status_code, 204)

    def test_performance_review_crud(self):
        self._create_update_delete(
            "performance-reviews",
            "reviewID",
            {
                "staffID": 120, "reviewDate": "2026-09-01", "reviewerID": 201,
                "rating": 3.5, "feedback": "Initial review", "status": "Draft"
            },
            {"rating": 4.0, "status": "Completed"},
        )

    def test_training_program_crud(self):
        self._create_update_delete(
            "training-programs",
            "trainingID",
            {
                "title": "Accessible Teaching", "description": "Inclusive design",
                "provider": "UTS", "startDate": "2027-01-10",
                "endDate": "2027-01-11", "skillArea": "Teaching"
            },
            {"provider": "UTS Learning Hub"},
        )

    def test_staff_training_crud(self):
        self._create_update_delete(
            "staff-training",
            "staffTrainingID",
            {
                "staffID": 120, "trainingID": 1, "enrolmentDate": "2026-09-01",
                "completionDate": None, "status": "Enrolled"
            },
            {"status": "In Progress"},
        )

    def test_recommendation_crud(self):
        self._create_update_delete(
            "development-recommendations",
            "recommendationID",
            {
                "staffID": 120, "goalID": 1, "recommendationType": "Mentoring",
                "recommendation": "Arrange a mentoring partnership.",
                "rationale": "Supports the leadership goal.",
                "dateGenerated": "2026-09-01", "status": "Pending"
            },
            {"status": "Accepted"},
        )

    def test_database_rejects_invalid_foreign_key(self):
        response = self.client.post("/staff-training", json={
            "staffID": 120,
            "trainingID": 99999,
            "status": "Enrolled",
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
