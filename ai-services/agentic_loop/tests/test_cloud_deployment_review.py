"""Cloud Deployment Review regression tests (no deployment or network invoked)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from collectors import cloud_deployment_report_collector as cloud
from config.review_config import build_mode_config
from core.orchestrator import run_mode
from core.prompt_registry import PromptRegistry


GATED_WORKFLOW = """name: Cloud Deployment
on:
  workflow_run:
    workflows: ["Student 1 CI"]
    types: [completed]
jobs:
  deploy:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy/deploy.sh
"""

CLOUD_COMPOSE = """services:
  staff-backend:
    environment:
      - AI_MODE_ENABLED=false
      - MCP_ENABLED=false
      - RAG_ENABLED=false
      - MULTI_AGENT_ENABLED=false
"""


def manifest(**overrides):
    data = {
        "platform": "AWS",
        "region": "ap-southeast-2",
        "hosting": "EC2 + Docker Compose",
        "deployed_commit": "abc1234",
        "workflow_run": {"url": "https://example/run/1", "conclusion": "success", "log": "run.log"},
        "deployment_scripts": ["deploy/deploy.sh"],
        "cloud_config": ["docker-compose.cloud.yml"],
        "services": [
            {
                "student": n,
                "frontend_url": f"http://host:800{n}",
                "backend_url": f"http://host:500{n}",
                "crud_read_path": "/api/items",
                **({"ai_status_path": "/api/ai-services/status"} if n == 1 else {}),
            }
            for n in range(1, 6)
        ],
    }
    data.update(overrides)
    return data


def build_repo(root, data, workflow=GATED_WORKFLOW, compose=CLOUD_COMPOSE, script="#!/bin/sh\ndocker compose up -d\n"):
    evidence = root / "reports" / "cloud-deployment"
    evidence.mkdir(parents=True)
    (evidence / "deployment-evidence.json").write_text(json.dumps(data), encoding="utf-8")
    (evidence / "run.log").write_text("Deploy finished\n", encoding="utf-8")
    (root / "deploy").mkdir()
    (root / "deploy" / "deploy.sh").write_text(script, encoding="utf-8")
    (root / "docker-compose.cloud.yml").write_text(compose, encoding="utf-8")
    if workflow is not None:
        (root / ".github" / "workflows").mkdir(parents=True)
        (root / ".github" / "workflows" / "cloud-deployment.yml").write_text(workflow, encoding="utf-8")


def all_ok_probe(url):
    if url.endswith("/api/ai-services/status"):
        return "OK", f"{url}: HTTP 200", {"ai_mode_enabled": False, "mcp_enabled": False}
    return "OK", f"{url}: HTTP 200", None


def collect(root, mode="saved"):
    with patch.dict(os.environ, {"AGENTIC_CLOUD_PROBE_MODE": mode}):
        return cloud.collect(root / "ai-services" / "agentic_loop", root)


class CloudDeploymentReviewTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()

    def test_mode_and_prompts_registered(self):
        cfg = build_mode_config()["cloud_deployment_report_review"]
        registry = PromptRegistry(APP_DIR)
        for rel in (*cfg.implementation_prompts, *cfg.review_prompts):
            self.assertTrue(registry.read(cfg.prompt_family, rel))

    def test_missing_manifest_fails_observe(self):
        ok, evidence = collect(self.root)

        self.assertFalse(ok)
        self.assertIn("no cloud deployment evidence found", evidence)

    def test_complete_live_evidence_needs_human_validation(self):
        build_repo(self.root, manifest())

        with patch.object(cloud, "probe", side_effect=all_ok_probe):
            ok, evidence = collect(self.root, "live")

        self.assertTrue(ok)
        self.assertIn("DETERMINISTIC RELEASE VERDICT: HUMAN_VALIDATION_REQUIRED", evidence)
        self.assertIn("Release blockers: ['None identified']", evidence)
        self.assertIn("Student 1: frontend=OK backend=OK crud_read=OK ai_status=DISABLED", evidence)

    def test_saved_mode_cannot_be_ready_without_probes(self):
        build_repo(self.root, manifest())

        ok, evidence = collect(self.root)

        self.assertTrue(ok)
        self.assertIn("DETERMINISTIC RELEASE VERDICT: NOT_READY", evidence)
        self.assertIn("RECORDED_NOT_PROBED", evidence)
        self.assertIn("deployed URLs not probed", evidence)

    def test_ai_enabled_in_cloud_config_blocks_release(self):
        build_repo(self.root, manifest(), compose="environment:\n  - MCP_ENABLED=true\n")

        with patch.object(cloud, "probe", side_effect=all_ok_probe):
            _, evidence = collect(self.root, "live")

        self.assertIn("NOT_READY", evidence)
        self.assertIn("AI_ENABLED - MCP_ENABLED=true", evidence)

    def test_ai_enabled_on_live_status_route_blocks_release(self):
        build_repo(self.root, manifest())

        def probe(url):
            if url.endswith("/api/ai-services/status"):
                return "OK", "HTTP 200", {"rag_enabled": True}
            return "OK", "HTTP 200", None

        with patch.object(cloud, "probe", side_effect=probe):
            _, evidence = collect(self.root, "live")

        self.assertIn("NOT_READY", evidence)
        self.assertIn("AI enabled in cloud: rag_enabled", evidence)

    def test_unreachable_service_blocks_release(self):
        build_repo(self.root, manifest())

        def probe(url):
            if "host:8003" in url:
                return "UNREACHABLE", f"{url}: ConnectionError", None
            return all_ok_probe(url)

        with patch.object(cloud, "probe", side_effect=probe):
            _, evidence = collect(self.root, "live")

        self.assertIn("NOT_READY", evidence)
        self.assertIn("Student 3: frontend probe UNREACHABLE", evidence)

    def test_workflow_must_wait_for_ci(self):
        build_repo(self.root, manifest(), workflow="on: push\njobs:\n  deploy:\n    runs-on: ubuntu-latest\n")

        _, evidence = collect(self.root)

        self.assertIn("cloud-deployment.yml: NOT_GATED", evidence)

    def test_failed_deployment_run_blocks_release(self):
        data = manifest(workflow_run={"url": "https://example/run/2", "conclusion": "failure", "log": "run.log"})
        build_repo(self.root, data)

        _, evidence = collect(self.root)

        self.assertIn("Deployment run: FAILED - conclusion=failure", evidence)

    def test_committed_aws_key_is_reported(self):
        build_repo(self.root, manifest(), script="export AWS_ACCESS_KEY_ID=AKIAABCDEFGHIJKLMNOP\n")

        _, evidence = collect(self.root)

        self.assertIn("Credential scan of deployment files: FOUND - AWS access key ID in deploy.sh", evidence)

    def test_missing_student_is_not_recorded(self):
        data = manifest()
        data["services"] = [s for s in data["services"] if s["student"] != 4]
        build_repo(self.root, data)

        _, evidence = collect(self.root)

        self.assertIn("Student 4: NOT_RECORDED in manifest", evidence)

    def test_release_decision_is_recorded_and_reported(self):
        build_repo(self.root, manifest())

        with self.assertRaises(ValueError):
            cloud.write_release_decision(self.root, "Ship it", "Andy", "", "report.md")

        cloud.write_release_decision(self.root, "Release with conditions", "Andy", "Fix S4 first", "report.md")
        _, evidence = collect(self.root)

        self.assertIn("Human release decision: Release with conditions by Andy", evidence)

    def test_run_mode_writes_report_with_fake_models(self):
        build_repo(self.root, manifest())

        class FakeRunner:
            def model_for(self, review):
                return "fake"

            def call(self, system_prompt, user_prompt, review=False):
                return ("Recommendation for the Human Release Decision: hold" if review else "Release Blockers: probes"), None

        with patch.dict(os.environ, {"AGENTIC_CLOUD_PROBE_MODE": "saved"}):
            result = run_mode("cloud_deployment_report_review", str(APP_DIR), str(self.root), runner=FakeRunner())

        self.assertIn("Cloud Deployment Report Review completed.", result)
        report = Path(result.split("Report: ", 1)[1].splitlines()[0])
        self.assertTrue(report.is_file())
        self.assertIn("DETERMINISTIC RELEASE VERDICT: NOT_READY", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
