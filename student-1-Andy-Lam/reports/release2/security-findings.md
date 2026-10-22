# Student 1 – Pre-Commit Security Findings (Release 2)

Scans: Ruff security rules (`--select S`), detect-secrets, pip-audit, configured in
`student-1-Andy-Lam/.pre-commit-config.yaml` and run on every commit.
Final result: all three passed (`precommit-results.txt`).

## Findings from the first scan and how they were handled

| Tool | Finding | Location | Action |
|---|---|---|---|
| Ruff S201 | Flask `debug=True` – the Werkzeug debugger allows code execution from the browser, and the Docker image runs `python app.py`, so it was on in the container | `backend/app.py` | **Fixed.** Debug is now opt-in via `FLASK_DEBUG=true` and off by default |
| Ruff S104 | Server binds to `0.0.0.0` | `backend/app.py` | **Accepted.** Required so the backend is reachable from outside its Docker container; marked `# noqa: S104` with the reason |
| Ruff S603 | `subprocess.run` call | `tests/conftest.py` | **Accepted.** Runs only this repo's `init_db.py` / `seed.py` with fixed arguments to build the test database; marked `# noqa: S603` |
| Ruff S101 | `assert` statements (130 findings) | `tests/` | **Excluded for tests only.** `assert` is how pytest checks results; still enforced in backend and database code |
| pip-audit | `flask 3.0.3` – PYSEC-2026-2151 | `backend/requirements.txt` | **Fixed.** Upgraded to `flask==3.1.3` |
| pip-audit | `flask-cors 4.0.1` – PYSEC-2024-71, PYSEC-2026-1383/1384/1385 | `backend/requirements.txt` | **Fixed.** Upgraded to `flask-cors==6.0.0`; CORS still allows the frontend origin |
| pip-audit | `requests 2.32.3` – PYSEC-2026-1872, PYSEC-2026-2275 | `backend/requirements.txt` | **Fixed.** Upgraded to `requests==2.33.0` |
| detect-secrets | No secrets found | all Student 1 files | None needed |

After the fixes, all 74 Student 1 tests still pass.
