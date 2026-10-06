# Student 5 Release 1 MCP evidence

## Contribution

The Performance and Professional Development feature now calls two registered
tools on the shared local MCP server through its own backend/API. The tools read
existing Student 5 APIs and do not change database records.

| Tool | Input | Output |
|---|---|---|
| `student5_staff_development_summary` | Positive staff ID | Reviews, goals, training with program titles, recommendations |
| `student5_training_by_skill_area` | Skill area text | Matching training catalogue programs and match count |

The frontend has an MCP Tools tab for both interactions. The backend enables
MCP through `MCP_ENABLED=true` and uses `MCP_SERVER_URL` to reach the shared
server. MCP remains disabled in Student 5 CI.

## Local validation

On 1 October 2026, the three local Python services were started with a
temporary database. Requests to the Student 5 backend used the real MCP
protocol client and the shared MCP server. Results:

| Check | Observed result |
|---|---|
| `GET /api/mcp/status` | `enabled: true` |
| `POST /api/mcp/development-summary` with `{"staffID":1}` | `status: success`, staff ID 1, one review, one goal, training title `Academic Leadership Foundations` |
| `POST /api/mcp/training-by-skill` with `{"skillArea":"Leadership"}` | `status: success`, one matching program, `Academic Leadership Foundations` |

Automated checks passed: 18 backend tests, 12 database tests, 6 shared MCP
tool tests, JavaScript syntax, `git diff --check`, and validation of both
Docker Compose configurations. A temporary local frontend proxy served the
MCP tab and JavaScript and returned successful results for both tool requests
through the frontend's `/api` path. Docker Desktop and a browser were
unavailable during this validation, so a click-through in the containerised
frontend and a GitHub Actions run still need to be captured after deployment.

## Demonstration checklist

1. Start the integrated application and the shared local MCP server.
2. Open `http://localhost:8005` and choose **MCP Tools**.
3. Enter staff ID `1` and select **Get summary**. Capture the result.
4. Search for `Leadership` and capture the returned program.
5. Record the successful Student 5 workflow link after the code is pushed.

Commit IDs, screenshots, and the workflow run link should be added to the
group contribution log after those events occur.
