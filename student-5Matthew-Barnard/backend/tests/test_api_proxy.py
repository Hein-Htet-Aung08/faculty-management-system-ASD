import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app


def fake_response(status, body=b"{}"):
    response = Mock()
    response.status_code = status
    response.content = body
    response.headers = {"Content-Type": "application/json"}
    return response


class ApiProxyTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("database_client.list_resource")
    def test_list_forwards_only_supported_filters(self, list_resource):
        list_resource.return_value = fake_response(200, b"[]")
        response = self.client.get(
            "/api/development-goals?staffID=101&status=In%20Progress&ignored=value"
        )
        self.assertEqual(response.status_code, 200)
        list_resource.assert_called_once_with(
            "development-goals", {"staffID": "101", "status": "In Progress"}
        )

    @patch("database_client.create_resource")
    def test_create_forwards_json_and_status(self, create_resource):
        create_resource.return_value = fake_response(
            201, b'{"goalID":11,"title":"New goal"}'
        )
        response = self.client.post("/api/development-goals", json={
            "staffID": 101, "title": "New goal", "status": "Planned"
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["goalID"], 11)

    @patch("database_client.delete_resource")
    def test_delete_preserves_empty_204_response(self, delete_resource):
        delete_resource.return_value = fake_response(204, b"")
        response = self.client.delete("/api/training-programs/1")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")

    def test_unknown_resource_returns_404(self):
        self.assertEqual(self.client.get("/api/not-a-resource").status_code, 404)


class AiModeRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("ai_service.generate_recommendation")
    def test_ai_mode_returns_saved_recommendation(self, generate):
        generate.return_value = {
            "mode": "single-pass-ai",
            "model": "qwen2.5:0.5b",
            "recommendation": {"recommendationID": 11, "status": "Pending"},
        }
        response = self.client.post(
            "/api/ai/recommend-development", json={"staffID": 101}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["mode"], "single-pass-ai")

    def test_ai_mode_requires_positive_staff_id(self):
        response = self.client.post(
            "/api/ai/recommend-development", json={"staffID": 0}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
