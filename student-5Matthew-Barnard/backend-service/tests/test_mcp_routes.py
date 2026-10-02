import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


class MCPRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch.dict("os.environ", {"MCP_ENABLED": "false"})
    @patch("mcp_client.call_tool")
    def test_disabled_mode_does_not_call_server(self, call_tool):
        response = self.client.post("/api/mcp/development-summary", json={"staffID": 1})
        self.assertEqual(response.status_code, 503)
        self.assertFalse(self.client.get("/api/mcp/status").json["enabled"])
        call_tool.assert_not_called()

    @patch.dict("os.environ", {"MCP_ENABLED": "true"})
    @patch("mcp_client.call_tool")
    def test_development_summary_calls_registered_tool(self, call_tool):
        call_tool.return_value = {
            "status": "success", "data": {"staffID": 1, "goals": []}
        }
        response = self.client.post("/api/mcp/development-summary", json={"staffID": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["data"]["staffID"], 1)
        call_tool.assert_called_once_with(
            "student5_staff_development_summary", {"staff_id": 1}
        )

    @patch.dict("os.environ", {"MCP_ENABLED": "true"})
    @patch("mcp_client.call_tool")
    def test_training_search_passes_trimmed_skill_area(self, call_tool):
        call_tool.return_value = {"status": "success", "data": [], "match_count": 0}
        response = self.client.post(
            "/api/mcp/training-by-skill", json={"skillArea": " Leadership "}
        )
        self.assertEqual(response.status_code, 200)
        call_tool.assert_called_once_with(
            "student5_training_by_skill_area", {"skill_area": "Leadership"}
        )

    @patch.dict("os.environ", {"MCP_ENABLED": "true"})
    @patch("mcp_client.call_tool")
    def test_bad_input_is_rejected_before_calling_server(self, call_tool):
        bad_requests = [
            ("/api/mcp/development-summary", {"staffID": 0}),
            ("/api/mcp/development-summary", {"staffID": True}),
            ("/api/mcp/development-summary", {"staffID": 1.5}),
            ("/api/mcp/training-by-skill", {"skillArea": " "}),
            ("/api/mcp/training-by-skill", []),
        ]
        for path, payload in bad_requests:
            self.assertEqual(self.client.post(path, json=payload).status_code, 400)
        call_tool.assert_not_called()

    @patch.dict("os.environ", {"MCP_ENABLED": "true"})
    @patch("mcp_client.call_tool")
    def test_tool_error_is_returned(self, call_tool):
        call_tool.return_value = {
            "status": "error", "error": "invalid_input", "details": "bad staff ID"
        }
        response = self.client.post("/api/mcp/development-summary", json={"staffID": 1})
        self.assertEqual(response.status_code, 400)

    @patch.dict("os.environ", {"MCP_ENABLED": "true"})
    @patch("mcp_client.call_tool")
    def test_unavailable_server_returns_503(self, call_tool):
        from mcp_client import MCPServiceError

        call_tool.side_effect = MCPServiceError("MCP server is unavailable")
        response = self.client.post("/api/mcp/development-summary", json={"staffID": 1})
        self.assertEqual(response.status_code, 503)
        self.assertIn("MCP server is unavailable", response.json["error"])


if __name__ == "__main__":
    unittest.main()
