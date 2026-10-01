import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tools


class Student5ToolTests(unittest.TestCase):
    @patch("tools.call_feature_api")
    def test_staff_summary_reads_existing_backend_routes(self, call_api):
        records = {
            "/api/performance-reviews": [{"staffID": 1, "rating": 4.5}],
            "/api/development-goals": [{"staffID": 1, "title": "Lead a team"}],
            "/api/staff-training": [{"staffID": 1, "trainingID": 3}],
            "/api/development-recommendations": [{"staffID": 1, "status": "Pending"}],
            "/api/training-programs": [{"trainingID": 3, "title": "Leadership course"}],
        }
        call_api.side_effect = lambda method, base, path, **kwargs: {
            "status": "success", "data": records[path]
        }

        result = tools.student5_staff_development_summary(1)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"]["training"][0]["trainingTitle"], "Leadership course")
        self.assertEqual(result["data"]["goals"][0]["title"], "Lead a team")
        self.assertEqual(call_api.call_count, 5)
        for call in call_api.call_args_list:
            self.assertEqual(call.args[0], "GET")
            self.assertEqual(call.args[1], tools.STUDENT5_BACKEND_URL)
            self.assertTrue(call.args[2].startswith("/api/"))

    @patch("tools.call_feature_api")
    def test_staff_summary_rejects_invalid_id(self, call_api):
        for value in (0, -1, True, "1"):
            self.assertEqual(
                tools.student5_staff_development_summary(value)["error"], "invalid_input"
            )
        call_api.assert_not_called()

    @patch("tools.call_feature_api")
    def test_staff_summary_returns_backend_error(self, call_api):
        call_api.return_value = {"status": "error", "http_status": 503}
        self.assertEqual(
            tools.student5_staff_development_summary(1)["http_status"], 503
        )

    @patch("tools.call_feature_api")
    def test_training_search_is_case_insensitive(self, call_api):
        call_api.return_value = {
            "status": "success",
            "data": [
                {"title": "Leadership course", "skillArea": "Academic Leadership"},
                {"title": "Feedback course", "skillArea": "Teaching"},
            ],
        }

        result = tools.student5_training_by_skill_area(" leadership ")

        self.assertEqual(result["match_count"], 1)
        self.assertEqual(result["data"][0]["title"], "Leadership course")
        call_api.assert_called_once_with(
            "GET", tools.STUDENT5_BACKEND_URL, "/api/training-programs"
        )

    @patch("tools.call_feature_api")
    def test_training_search_rejects_empty_input(self, call_api):
        self.assertEqual(
            tools.student5_training_by_skill_area(" ")["error"], "invalid_input"
        )
        call_api.assert_not_called()

    def test_tools_are_registered(self):
        import server

        self.assertIn("student5_staff_development_summary", server.AVAILABLE_TOOLS)
        self.assertIn("student5_training_by_skill_area", server.AVAILABLE_TOOLS)


if __name__ == "__main__":
    unittest.main()
