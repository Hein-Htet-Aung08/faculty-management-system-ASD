# Student 5 security findings

The local commit hook runs Ruff security rules, detect-secrets and pip-audit.
The scan covers Student 5 source and tests, including the Student 5 evidence
contribution in the shared Multi-Agent server. Dependency auditing covers the
backend and database requirements.

The first dependency audit found these advisories:

| Package | Finding | Change |
| --- | --- | --- |
| Flask 3.0.3 | PYSEC-2026-2151 | Updated both services to Flask 3.1.3 |
| requests 2.32.3 | PYSEC-2026-1872 and PYSEC-2026-2275 | Updated the backend to requests 2.33.0 |

The initial Ruff output is saved in `ruff-initial.txt`. Its 12 findings were
reviewed and the following exceptions are limited to the named files in
`ruff.toml`:

| Rule | Location | Reason |
| --- | --- | --- |
| S104 | Backend and database `app.py` | Binding to 0.0.0.0 is needed for access from other containers. Debug remains off by default. |
| S608 | Database `app.py` | Table, primary-key and column names come from the fixed resource configuration and validated field list. User values use SQL parameters. |
| S608 | Database `database.py` | Seed and count queries use fixed table and column maps, with parameterised seed values. |

S104 and S608 remain enabled elsewhere. The SQL-looking title test verifies
that submitted text is stored as data and does not remove the goals table.
These accepted findings are not claims that all SQL or network risks are absent.

`precommit-results.txt` contains the actual hook output and identifies the
base commit and uncommitted working-tree snapshot. It is a manual run of the
installed hooks; the next commit also runs them automatically. A passing
snapshot does not prove that future changes have passed.
