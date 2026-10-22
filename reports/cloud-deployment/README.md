# Cloud Deployment Evidence (Release 2)

Input for the agentic-loop **Cloud Deployment Report Review** (menu option 11 in
`ai-services/agentic_loop/main.py`). Whoever runs the cloud deployment fills in
`deployment-evidence.json` here; the review checks it, the repository and,
optionally, the live URLs, then asks a human for the final release decision.

## Files

| File | Written by | Contents |
|---|---|---|
| `deployment-evidence.json` | The person deploying | Platform, deployed commit, workflow run and each student's URLs (format below) |
| `cloud-deployment-run.log` | The person deploying | Log of the successful `cloud-deployment.yml` run, downloaded from GitHub Actions |
| `release-decision.json` | The review, at the human prompt | Final human release decision, reviewer, notes, timestamp |

Copy `deployment-evidence.example.json` to `deployment-evidence.json` and replace
every value. Never put AWS keys, passwords or other credentials in these files.

## `deployment-evidence.json` fields

| Field | Required | Meaning |
|---|---|---|
| `platform` | yes | `AWS` or `Azure` |
| `region`, `hosting` | recommended | e.g. `ap-southeast-2`, `EC2 + Docker Compose` |
| `deployed_commit`, `deployed_at` | recommended | Commit SHA that was deployed and when |
| `workflow_run.url` | yes | Link to the `cloud-deployment.yml` run |
| `workflow_run.conclusion` | yes | Must be `success` |
| `workflow_run.log` | yes | Name of the saved log file in this folder |
| `deployment_scripts` | yes | Repo paths of the reusable deployment scripts |
| `cloud_config` | yes | Repo paths of the cloud configuration (e.g. a cloud compose file). Any `AI_MODE_ENABLED`, `MCP_ENABLED`, `RAG_ENABLED` or `MULTI_AGENT_ENABLED` set to true blocks release |
| `services` | yes | One entry per student, 1 to 5 |
| `services[].frontend_url` | yes | Deployed frontend URL |
| `services[].backend_url` | yes | Deployed backend base URL |
| `services[].crud_read_path` | yes | A read endpoint proving the backend and database work, e.g. `/api/staff` |
| `services[].ai_status_path` | optional | A route reporting AI flags as JSON, e.g. `/api/ai-services/status` |

## Release verdict

The review's deterministic verdict is `NOT_READY` until every check passes,
including live probes (option 2 at the prompt). `HUMAN_VALIDATION_REQUIRED`
means the evidence is complete and a person must decide; the AI output is
advisory only.
