# Student 5 Release 0 evidence guide

This guide separates evidence that can be collected for Matthew's working base feature now from evidence that can only be produced after the team's shared agentic loop is connected.

## Collect now: base feature and delivery evidence

Keep the original files or links, not only statements that the work occurred.

- Git evidence: relevant commits, branch name, pull request, and review comments.
- Automated-test evidence: terminal output showing database and backend tests passing.
- Container evidence: `docker compose ps`, service health responses, and successful image builds.
- CI/CD evidence: the GitHub Actions run URL and a screenshot of both jobs passing.
- CRUD evidence: screenshots showing a record created, displayed, edited, filtered, and deleted through the UI.
- AI-Mode evidence: input staff ID, model name, generated recommendation, saved recommendation row, and any validation/error response.
- Integration evidence: the feature linked from the shared group application and running with the integrated Compose configuration.

Suggested commands from `student-5Matthew-Barnard`:

```powershell
python -m unittest discover -s database-service/tests -v
python -m unittest discover -s backend/tests -v
docker compose up --build -d
docker compose ps
docker compose logs --no-color
```

Do not place secrets, API keys, private tokens, or unnecessary personal information in screenshots or logs.

## Collect later: shared agentic-loop evidence

Do not invent this evidence before the loop exists. For each genuine run, preserve:

- date/time, feature, user goal, and anonymised input;
- Plan output and selected actions;
- Act tool/API calls and their results;
- Observe output, including validation or test results;
- Adapt decision and why another iteration was or was not needed;
- final output and whether a human accepted, edited, or rejected it;
- model/configuration used and relevant error/retry logs;
- code revision or commit connected to the run.

The tutor announcement says the loop execution should **not** consume time in the showcase video. Its technical workflow is assessed from the report evidence and logs, so include a short architecture explanation and selected readable log excerpts in the report.

## Showcase recording checklist

The team video must demonstrate these three items:

1. The integrated group application, including Matthew's working feature.
2. Visible AI-Mode functionality in Matthew's frontend UI.
3. The CI/CD workflow and a successful run.

For Matthew's short segment, show the dashboard, perform one small CRUD change, generate one AI recommendation, confirm that it was saved, and then show the passing workflow. Do not demonstrate the agentic loop running in the video.
