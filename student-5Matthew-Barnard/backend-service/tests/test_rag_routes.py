import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
import rag_client


class RAGRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch.dict("os.environ", {"RAG_ENABLED": "false"})
    @patch("rag_client.answer_question")
    def test_disabled_mode_does_not_call_server(self, answer_question):
        response = self.client.post("/api/rag/ask", json={"query": "What is the goal?"})
        self.assertEqual(response.status_code, 503)
        self.assertFalse(self.client.get("/api/rag/status").json["enabled"])
        self.assertEqual(self.client.post("/api/rag/refresh").status_code, 503)
        answer_question.assert_not_called()

    @patch.dict("os.environ", {"RAG_ENABLED": "true"})
    @patch("rag_client.answer_question")
    def test_answer_returns_grounded_fields(self, answer_question):
        answer_question.return_value = {
            "status": "success", "answer": "The goal is 35% complete.",
            "citations": [{"source_id": "student5/development-goals/1"}],
            "confidence_category": "High",
        }
        response = self.client.post("/api/rag/ask", json={"query": "  What is the goal?  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["confidence_category"], "High")
        self.assertEqual(response.json["citations"][0]["source_id"], "student5/development-goals/1")
        answer_question.assert_called_once_with("What is the goal?")

    @patch.dict("os.environ", {"RAG_ENABLED": "true"})
    @patch("rag_client.answer_question")
    def test_invalid_questions_are_rejected(self, answer_question):
        for payload in ([], {}, {"query": "   "}, {"query": 10}, {"query": "x" * 501}):
            self.assertEqual(self.client.post("/api/rag/ask", json=payload).status_code, 400)
        answer_question.assert_not_called()

    @patch.dict("os.environ", {"RAG_ENABLED": "true"})
    @patch("rag_client.refresh_corpus")
    def test_refresh_calls_shared_server(self, refresh_corpus):
        refresh_corpus.return_value = {"status": "success", "chunk_count": 51}
        response = self.client.post("/api/rag/refresh")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["chunk_count"], 51)

    @patch.dict("os.environ", {"RAG_ENABLED": "true"})
    @patch("rag_client.answer_question", side_effect=rag_client.RAGServiceError("RAG server is unavailable"))
    def test_unavailable_server_returns_503(self, answer_question):
        response = self.client.post("/api/rag/ask", json={"query": "What is the goal?"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("RAG server is unavailable", response.json["error"])

    @patch.dict("os.environ", {"AI_MODE_ENABLED": "false"})
    @patch("ai_service.generate_recommendation")
    def test_ai_mode_is_disabled_in_ci(self, generate_recommendation):
        self.assertEqual(self.client.get("/api/ai/health").status_code, 503)
        response = self.client.post("/api/ai/recommend-development", json={"staffID": 1})
        self.assertEqual(response.status_code, 503)
        generate_recommendation.assert_not_called()


class RAGClientTests(unittest.TestCase):
    @patch("rag_client.request_rag")
    def test_insufficient_answer_clears_citations(self, request_rag):
        request_rag.return_value = {
            "status": "success", "answer": "Insufficient context.",
            "citations": [{"source_id": "unrelated"}], "confidence_category": "High",
        }
        result = rag_client.answer_question("unrelated question")
        self.assertEqual(result["answer"], "Insufficient context.")
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["confidence_category"], "Insufficient")

    @patch("rag_client.requests.post")
    def test_client_passes_caller_to_shared_server(self, post):
        post.return_value.json.return_value = {"status": "success", "chunk_count": 51}
        post.return_value.ok = True
        rag_client.refresh_corpus()
        self.assertEqual(post.call_args.args[0], "http://localhost:5200/refresh")
        self.assertEqual(post.call_args.kwargs["json"]["caller"], "student5-performance-development")

    @patch("rag_client.requests.post", side_effect=requests.ConnectionError("offline"))
    def test_client_reports_connection_failure(self, post):
        with self.assertRaisesRegex(rag_client.RAGServiceError, "RAG server is unavailable"):
            rag_client.answer_question("What is the goal?")

    @patch("rag_client.requests.post")
    def test_client_keeps_shared_error_detail(self, post):
        post.return_value.ok = False
        post.return_value.json.return_value = {
            "status": "error", "error": "local_model_unavailable",
            "details": "Ollama is unavailable",
        }
        with self.assertRaisesRegex(rag_client.RAGServiceError, "Ollama is unavailable"):
            rag_client.answer_question("What is the goal?")


if __name__ == "__main__":
    unittest.main()
