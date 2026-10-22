import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app


def fake_response(payload, status=200):
    response = Mock()
    response.status_code = status
    response.json.return_value = payload
    return response


class MultiAgentRouteTests(unittest.TestCase):
    def setUp(self):
        env_patch = patch.dict("os.environ", {
            "MULTI_AGENT_ENABLED": "true",
            "MULTI_AGENT_SERVER_URL": "http://127.0.0.1:5202",
        })
        env_patch.start()
        self.addCleanup(env_patch.stop)
        request_patch = patch("multi_agent_client.requests.request")
        self.call_server = request_patch.start()
        self.addCleanup(request_patch.stop)
        self.workflow = {
            "workflow_id": "test-workflow", "feature": "student5",
            "status": "awaiting_human_review",
            "planner_result": {"plan": "Review development records"},
            "worker_result": {"evidence_sources": ["student5/development-goals/1"]},
            "reviewer_result": {"review": "Human review required"},
            "human_decision": {"status": "pending"},
        }
        self.call_server.return_value = fake_response(self.workflow)
        self.client = create_app().test_client()

    def test_status_reports_configuration_without_calling_server(self):
        response = self.client.get("/api/multi-agent/status")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["enabled"])
        self.call_server.assert_not_called()

    def test_mode_defaults_to_disabled(self):
        import os

        os.environ.pop("MULTI_AGENT_ENABLED")

        self.assertFalse(self.client.get("/api/multi-agent/status").json["enabled"])
        self.assertEqual(self.client.post(
            "/api/multi-agent/workflow", json={"user_request": "Review goals"}
        ).status_code, 503)
        self.call_server.assert_not_called()

    @patch.dict("os.environ", {"MULTI_AGENT_ENABLED": "false"})
    def test_disabled_routes_do_not_call_server(self):
        paths = [
            ("POST", "/api/multi-agent/workflow"),
            ("GET", "/api/multi-agent/workflow/history"),
            ("GET", "/api/multi-agent/workflow/test-workflow"),
            ("POST", "/api/multi-agent/workflow/test-workflow/decision"),
        ]
        for method, path in paths:
            with self.subTest(path=path):
                response = self.client.open(path, method=method, json={})
                self.assertEqual(response.status_code, 503)
                self.assertIn("disabled", response.json["error"])
        self.call_server.assert_not_called()

    def test_start_workflow_forces_student5_and_keeps_agent_results(self):
        response = self.client.post("/api/multi-agent/workflow", json={
            "user_request": "  Review staff ID 1 development goals  ", "feature": "student2",
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, self.workflow)
        self.assertEqual(self.call_server.call_args.args,
                         ("POST", "http://127.0.0.1:5202/workflow"))
        self.assertEqual(self.call_server.call_args.kwargs["json"], {
            "user_request": "Review staff ID 1 development goals", "feature": "student5",
        })
        self.assertEqual(self.call_server.call_args.kwargs["timeout"], 420)

    def test_invalid_requests_are_rejected_before_calling_server(self):
        for payload in ([], None, {}, {"user_request": 1}, {"user_request": " "},
                        {"user_request": "x" * 1001}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/multi-agent/workflow", json=payload)
                self.assertEqual(response.status_code, 400)
        self.call_server.assert_not_called()

    def test_history_requests_and_returns_only_student5(self):
        self.call_server.return_value = fake_response({
            "status": "success", "workflows": [
                {"workflow_id": "own", "feature": "student5"},
                {"workflow_id": "other", "feature": "student2"},
            ],
        })
        response = self.client.get("/api/multi-agent/workflow/history?feature=student2&limit=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["workflows"], [{"workflow_id": "own", "feature": "student5"}])
        self.assertEqual(self.call_server.call_args.kwargs["params"], {"feature": "student5", "limit": 3})

    def test_invalid_history_limit_is_rejected(self):
        for limit in ("0", "101", "many"):
            with self.subTest(limit=limit):
                response = self.client.get(f"/api/multi-agent/workflow/history?limit={limit}")
                self.assertEqual(response.status_code, 400)
        self.call_server.assert_not_called()

    def test_history_without_workflow_list_returns_502(self):
        self.call_server.return_value = fake_response({"workflows": "invalid"})

        self.assertEqual(self.client.get("/api/multi-agent/workflow/history").status_code, 502)

    def test_workflow_details_return_owned_workflow(self):
        response = self.client.get("/api/multi-agent/workflow/test-workflow")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, self.workflow)

    def test_workflow_details_hide_other_features(self):
        self.call_server.return_value = fake_response({"feature": "student2", "private": "other data"})
        response = self.client.get("/api/multi-agent/workflow/other-workflow")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {"error": "Workflow not found"})

    def test_workflow_id_is_encoded_in_server_path(self):
        response = self.client.get("/api/multi-agent/workflow/run%3Fother%3D1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.call_server.call_args.args[1],
                         "http://127.0.0.1:5202/workflow/run%3Fother%3D1")

    def test_decisions_are_forwarded_after_ownership_check(self):
        for decision in ("Accept", "Partially Accept", "Correct", "Reject"):
            with self.subTest(decision=decision):
                self.call_server.side_effect = [
                    fake_response(self.workflow),
                    fake_response({"feature": "student5", "status": "recorded"}),
                ]
                response = self.client.post("/api/multi-agent/workflow/test-workflow/decision", json={
                    "decision": decision, "reviewer": " Matthew ", "notes": " Checked evidence ",
                    "correction": " Review target date ", "feature": "student2", "ignored": "value",
                })

                self.assertEqual(response.status_code, 200)
                self.assertEqual([call.args[0] for call in self.call_server.call_args_list[-2:]],
                                 ["GET", "POST"])
                self.assertEqual(self.call_server.call_args.kwargs["json"], {
                    "decision": decision, "reviewer": "Matthew", "notes": "Checked evidence",
                    "correction": "Review target date",
                })

    def test_decision_for_other_feature_does_not_reach_post(self):
        self.call_server.return_value = fake_response({"feature": "student2"})
        response = self.client.post("/api/multi-agent/workflow/other/decision", json={
            "decision": "Accept", "reviewer": "Matthew",
        })

        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.call_server.call_count, 1)
        self.assertEqual(self.call_server.call_args.args[0], "GET")

    def test_invalid_decisions_are_rejected_before_calling_server(self):
        payloads = [
            [], {}, {"decision": "Unknown"}, {"decision": []},
            {"decision": "Correct", "correction": " "},
            {"decision": "Accept", "reviewer": 1},
            {"decision": "Accept", "reviewer": "x" * 101},
            {"decision": "Accept", "notes": ["invalid"]},
            {"decision": "Accept", "notes": "x" * 2001},
            {"decision": "Correct", "correction": "x" * 2001},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/api/multi-agent/workflow/test-workflow/decision", json=payload)
                self.assertEqual(response.status_code, 400)
        self.call_server.assert_not_called()

    def test_unknown_workflow_error_is_preserved(self):
        self.call_server.return_value = fake_response({"error": "workflow not found"}, 404)
        response = self.client.get("/api/multi-agent/workflow/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "workflow not found")

    def test_repeated_decision_conflict_is_preserved(self):
        self.call_server.side_effect = [
            fake_response(self.workflow),
            fake_response({"error": "workflow already has a human decision"}, 409),
        ]
        response = self.client.post("/api/multi-agent/workflow/test-workflow/decision", json={
            "decision": "Accept",
        })

        self.assertEqual(response.status_code, 409)
        self.assertIn("already", response.json["error"])

    def test_connection_failure_and_timeout_return_503(self):
        for error in (requests.ConnectionError("offline"), requests.Timeout("timed out")):
            with self.subTest(error=error):
                self.call_server.side_effect = error
                response = self.client.post("/api/multi-agent/workflow", json={"user_request": "Review goals"})
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json["error"], "Multi-Agent server is unavailable")

    def test_invalid_json_response_returns_502(self):
        self.call_server.return_value.json.side_effect = ValueError("invalid JSON")
        response = self.client.get("/api/multi-agent/workflow/test-workflow")

        self.assertEqual(response.status_code, 502)

    def test_non_object_responses_return_502(self):
        for payload in ([], None, "invalid"):
            with self.subTest(payload=payload):
                self.call_server.return_value = fake_response(payload)
                response = self.client.get("/api/multi-agent/workflow/test-workflow")
                self.assertEqual(response.status_code, 502)


if __name__ == "__main__":
    unittest.main()
