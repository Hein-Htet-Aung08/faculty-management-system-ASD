import os
import sys
import tempfile
import unittest
from pathlib import Path

SERVICE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_DIR))


class DevelopmentGoalApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATABASE_PATH"] = str(Path(cls.temp_dir.name) / "test.db")

        from app import create_app

        cls.app = create_app({"TESTING": True})

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
        os.environ.pop("DATABASE_PATH", None)

    def setUp(self):
        self.client = self.app.test_client()

    def test_seeded_tables_have_at_least_ten_records(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(count >= 10 for count in response.json["tableCounts"].values()))

    def test_goal_crud_lifecycle(self):
        created = self.client.post("/development-goals", json={
            "staffID": 111,
            "title": "Improve inclusive teaching practice",
            "description": "Complete accessibility training and review subject materials.",
            "targetDate": "2027-01-31",
            "progress": 5,
            "status": "In Progress",
        })
        self.assertEqual(created.status_code, 201)
        goal_id = created.json["goalID"]

        fetched = self.client.get(f"/development-goals/{goal_id}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json["title"], "Improve inclusive teaching practice")

        updated = self.client.put(f"/development-goals/{goal_id}", json={
            "progress": 60,
            "status": "In Progress",
        })
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["progress"], 60)

        deleted = self.client.delete(f"/development-goals/{goal_id}")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(f"/development-goals/{goal_id}").status_code, 404)

    def test_goal_filters(self):
        response = self.client.get("/development-goals?staffID=1&status=In%20Progress")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json)
        self.assertTrue(all(goal["staffID"] == 1 for goal in response.json))
        self.assertTrue(all(goal["status"] == "In Progress" for goal in response.json))

    def test_invalid_goal_is_rejected(self):
        response = self.client.post("/development-goals", json={
            "staffID": 1,
            "title": "Invalid progress",
            "progress": 120,
            "status": "In Progress",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("progress", response.json["error"])

    def test_unknown_goal_returns_404(self):
        self.assertEqual(self.client.get("/development-goals/99999").status_code, 404)
        self.assertEqual(
            self.client.put("/development-goals/99999", json={"progress": 20}).status_code,
            404,
        )
        self.assertEqual(self.client.delete("/development-goals/99999").status_code, 404)


if __name__ == "__main__":
    unittest.main()
