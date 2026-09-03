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

## Collect later: shared software-development agentic-loop evidence

The tutor confirmed that this is the shared code-review and improvement loop, not the user-facing AI recommendation feature. It uses an LLM to review areas such as database design, architecture, endpoints, and DevOps; the team applies useful findings and repeats the cycle.

Do not invent this evidence before the shared loop exists. For each genuine run, preserve:

- date/time, model/configuration, starting commit, and the component being reviewed;
- **Plan:** the review focus and checks to perform;
- **Act:** the code/configuration supplied to the reviewer and its findings;
- **Observe:** which findings were accepted or rejected, with test results;
- **Adapt:** the resulting code change and why it was made;
- the next iteration, if validation exposed another problem;
- before/after commits, relevant logs, and a short human reflection.

Matthew should run the shared loop against his own feature after the group agrees on the implementation. Suitable review targets are the SQLite schema and relationships, API validation/error handling, Docker/CI configuration, and AI-output grounding. The evidence must show an actual change or a reasoned decision not to apply a suggestion.

The tutor announcement says the loop execution should **not** consume time in the showcase video. Its technical workflow is assessed from the report evidence and logs, so include a short architecture explanation and selected readable log excerpts in the report.

## Writing the report in your own voice

Use evidence first, then explain your reasoning plainly. A useful paragraph structure is:

1. What you were trying to achieve.
2. What you implemented and why you chose that design.
3. What went wrong or what the tests revealed.
4. What you changed and what evidence shows it worked.
5. What limitation or next step remains.

Avoid vague claims such as “the system was optimised” or “AI generated the solution.” Name the endpoint, table, container, failed check, or commit. Rewrite notes in language you would naturally use and include one or two genuine decisions you can explain during Q&A.

## Showcase recording checklist

The team video must demonstrate these three items:

1. The integrated group application, including Matthew's working feature.
2. Visible AI-Mode functionality in Matthew's frontend UI.
3. The CI/CD workflow and a successful run.

For Matthew's short segment, show the dashboard, perform one small CRUD change, generate one AI recommendation, confirm that it was saved, and then show the passing workflow. Do not demonstrate the agentic loop running in the video.
