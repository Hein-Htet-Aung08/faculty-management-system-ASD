import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse

import requests


FEATURE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FEATURE_DIR / "backend-service"))

from app import create_app


class DevelopmentGoalEndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        env_patch = patch.dict("os.environ", {
            "DATABASE_PATH": str(Path(self.temp_dir.name) / "test.db"),
            "AI_MODE_ENABLED": "false", "MCP_ENABLED": "false",
            "RAG_ENABLED": "false", "MULTI_AGENT_ENABLED": "false",
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)
        database_dir = FEATURE_DIR / "database-service"
        path_patch = patch.object(sys, "path", [str(database_dir), *sys.path])
        path_patch.start()
        self.addCleanup(path_patch.stop)
        spec = importlib.util.spec_from_file_location("student5_database_app", database_dir / "app.py")
        database_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_app)
        self.database = database_app.create_app({"TESTING": True}).test_client()
        self.client = create_app().test_client()
        request_patch = patch("database_client.requests.request", side_effect=self.database_request)
        self.call_database = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.goal = {
            "staffID": 111, "title": "Improve inclusive teaching",
            "description": "Complete accessibility training",
            "targetDate": "2027-01-31", "progress": 0, "status": "Planned",
        }

    def database_request(self, method, url, params=None, json=None, timeout=None):
        result = self.database.open(urlparse(url).path, method=method, query_string=params, json=json)
        response = requests.Response()
        response.status_code = result.status_code
        response._content = result.data
        response.headers.update(result.headers)
        return response

    def test_get_goals_returns_seeded_records(self):
        response = self.client.get("/api/development-goals")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 10)
        goal = next(row for row in response.json if row["goalID"] == 1)
        self.assertEqual(goal["title"], "Strengthen academic leadership")
        self.assertEqual(goal["staffID"], 1)

    def test_get_goals_filters_by_staff_and_status(self):
        response = self.client.get("/api/development-goals?staffID=1&status=In%20Progress")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json)
        self.assertTrue(all(row["staffID"] == 1 and row["status"] == "In Progress" for row in response.json))

    def test_get_goals_returns_empty_list_for_no_matches(self):
        response = self.client.get("/api/development-goals?staffID=99999")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_get_goals_rejects_invalid_status(self):
        response = self.client.get("/api/development-goals?status=Invalid")

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json["error"])

    def test_get_goals_handles_database_failure(self):
        self.call_database.side_effect = requests.ConnectionError("database unavailable")
        response = self.client.get("/api/development-goals")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "database service is unavailable")

    def test_post_goal_returns_created_record(self):
        response = self.client.post("/api/development-goals", json=self.goal)

        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(response.json["goalID"], int)
        self.assertEqual(response.json["title"], self.goal["title"])
        self.assertEqual(response.json["progress"], 0)

    def test_post_goal_is_saved_and_returned_by_get(self):
        created = self.client.post("/api/development-goals", json=self.goal)
        response = self.client.get("/api/development-goals?staffID=111")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [created.json])

    def test_post_goal_rejects_missing_title(self):
        payload = {key: value for key, value in self.goal.items() if key != "title"}
        response = self.client.post("/api/development-goals", json=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json["error"])

    def test_post_goal_rejects_progress_outside_range(self):
        response = self.client.post("/api/development-goals", json={**self.goal, "progress": 120})

        self.assertEqual(response.status_code, 400)
        self.assertIn("progress", response.json["error"])

    def test_post_goal_requires_full_progress_for_completion(self):
        response = self.client.post("/api/development-goals", json={
            **self.goal, "status": "Completed", "progress": 25,
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn("progress", response.json["error"])

    def test_post_goal_rejects_non_object_without_database_call(self):
        response = self.client.post("/api/development-goals", json=[])

        self.assertEqual(response.status_code, 400)
        self.call_database.assert_not_called()

    def test_failed_post_does_not_add_a_goal(self):
        before = self.client.get("/api/development-goals").json
        self.client.post("/api/development-goals", json={**self.goal, "progress": -1})
        after = self.client.get("/api/development-goals").json

        self.assertEqual(after, before)

    def test_post_goal_stores_sql_text_as_data(self):
        title = "Goal'); DROP TABLE DevelopmentGoals; --"
        created = self.client.post("/api/development-goals", json={**self.goal, "title": title})
        response = self.client.get("/api/development-goals?staffID=111")

        self.assertEqual(created.status_code, 201)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]["title"], title)

    def test_post_goal_handles_database_failure(self):
        self.call_database.side_effect = requests.ConnectionError("database unavailable")
        response = self.client.post("/api/development-goals", json=self.goal)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json["error"], "database service is unavailable")


if __name__ == "__main__":
    unittest.main()
