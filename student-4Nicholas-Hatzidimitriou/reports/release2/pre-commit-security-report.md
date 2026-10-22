# Student 4 Pre-Commit Security Testing Report

Date: 2026-10-22
Commit: 7cf1725ec0db5cafa191ced8617f378b44134b8c
Student: Nicholas Hatzidimitriou (Student 4, Research & Grant Management)

## Current design: scoped to my own code only

The hook config lives at `student-4Nicholas-Hatzidimitriou/.pre-commit-config.yaml`
(moved there from the repo root to match students 1 and 2's layout). Because
`pre-commit install` only ever reads `.pre-commit-config.yaml` from the repo root, it
was reinstalled with:

```bash
pre-commit install -c student-4Nicholas-Hatzidimitriou/.pre-commit-config.yaml
```

— confirmed by reading the generated `.git/hooks/pre-commit` script, which now hardcodes
that `--config` path. Three hooks (`student4-ruff-security`, `student4-detect-secrets`,
`student4-pip-audit`), each scanning only:

- `student-4Nicholas-Hatzidimitriou/backend`
- `student-4Nicholas-Hatzidimitriou/database-service`
- `student-4Nicholas-Hatzidimitriou/frontend`
- `student-4Nicholas-Hatzidimitriou/tests`

Supporting files also moved into this folder: `tests/pre_commit/{test_ruff_scan,
test_secrets_scan,test_dependency_audit}.py`, `scripts/pre_commit_pytest.py`. The
shared root-level `pyproject.toml` was removed - ruff's `--select S` and
`--per-file-ignores` are now passed directly on the command line (same pattern as
students 1 and 2), so no shared ruff config is needed at all.

This replaced an earlier repo-wide design (one root `pyproject.toml` + `.pre-commit-config.yaml`
scanning all five stacks via `rglob`). That version correctly caught real findings (below),
but also meant `pre-commit run --all-files` failed on every commit attempt until all five
students fixed their own pre-existing issues - which defeats the ownership model in the
brief ("each student runs and reports on their own code"). Scoping it to my own folder
means my commits are gated by my own code's security posture only, not blocked by
findings I don't own and can't fix.

## Fresh output (today, this scope)

```bash
pre-commit install -c student-4Nicholas-Hatzidimitriou/.pre-commit-config.yaml
pre-commit run -c student-4Nicholas-Hatzidimitriou/.pre-commit-config.yaml --all-files
```

```
Student 4 - Ruff Security Scan...........................................Passed
Student 4 - Secret Detection.............................................Passed
Student 4 - Dependency Audit.............................................Passed
```

Individually, for the record (same real run, split out):

```
$ ruff check --select S --per-file-ignores 'student-4Nicholas-Hatzidimitriou/**/tests/**:S101' \
    student-4Nicholas-Hatzidimitriou/{backend,database-service,frontend,tests}
All checks passed!

$ pip-audit -r student-4Nicholas-Hatzidimitriou/backend/requirements.txt
No known vulnerabilities found

$ pip-audit -r student-4Nicholas-Hatzidimitriou/database-service/requirements.txt
No known vulnerabilities found

$ pip-audit -r student-4Nicholas-Hatzidimitriou/frontend/requirements.txt
No known vulnerabilities found

$ detect-secrets scan student-4Nicholas-Hatzidimitriou
{"results": {}}
```

Zero findings, scoped scan. This isn't the absence of a check - it reflects real fixes
already applied (below) plus the fact a scoped scan no longer sees other students' or
teammates' shared-file findings, by design.

## Real findings fixed (from the original repo-wide run, still true)

In **my own code**, all fixed:

| File | Finding | Fix |
|---|---|---|
| `student-4Nicholas-Hatzidimitriou/backend/app.py:36` | S104 (bind `0.0.0.0`) + S201 (`debug=True`) | `debug` now reads `FLASK_DEBUG` env var (default `false`); `noqa: S104` with reason - container needs to bind all interfaces |
| `student-4Nicholas-Hatzidimitriou/database-service/app.py:614` | Same | Same fix |
| `student-4Nicholas-Hatzidimitriou/frontend/app.py:37` | Same | Same fix |

**Before/after, `student-4Nicholas-Hatzidimitriou/backend/app.py`:**
```python
# Before
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=True)

# After
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5004)), debug=debug_mode)  # noqa: S104 - container needs to bind all interfaces
```

In **shared `ai-services/` code I maintain** (not scanned by my scoped hook any more,
but still fixed in those files - this is independent of scoping, since the fixes are
in the files themselves):

| File | Finding | Fix |
|---|---|---|
| `ai-services/mcp-server/server.py:12` | S104 (bind `0.0.0.0`) | `noqa: S104` - this host process must bind all interfaces so containerised backends can reach it via `host.docker.internal` |
| `ai-services/rag-server/rag_http_server.py:310` | Same | Same fix |
| `ai-services/rag-server/rag_pipeline.py:2357` | S110 (`except: pass`) | Replaced with `logger.warning(...)` - a real fix, not a suppression |
| `ai-services/agentic_loop/collectors/db_collector.py:35` | S608 (possible SQL injection) | `noqa: S608` - the table name comes from `sqlite_master`, not external input |
| `ai-services/agentic_loop/collectors/development_integrity_collector.py:47` | S608 | `noqa: S608` - table/columns come from the module's own fixed `RESOURCES` config, not external input |
| `ai-services/agentic_loop/collectors/development_integrity_collector.py:90, 93` | S310 (`urlopen` scheme) | `noqa: S310` - fixed internal service URL, not external input |

## detect-secrets

Current scoped scan: zero results (see above). `.secrets.baseline` (repo root, shared)
still contains one older entry from before this scope change, in a teammate's Ollama
client file - the required placeholder value for an OpenAI-compatible client pointed at
a local Ollama server, not a credential - audited as `"is_secret": false`. My scoped
scan no longer reads that file at all, so this entry is inert for my own hook now, but
it's left in place since the baseline is a shared ledger other students' own scoped
hooks may still reference.

## pip-audit

**Fixed in my own three `requirements.txt` files** (still true, re-verified today - see
fresh output above, all three now clean):

| Package | Before | After | CVEs fixed |
|---|---|---|---|
| Flask | 3.0.3 | 3.1.3 | PYSEC-2026-2151 |
| flask-cors | 4.0.1 | 6.0.0 | PYSEC-2024-71, PYSEC-2026-1383/1384/1385 |
| requests | 2.32.3 | 2.33.0 | PYSEC-2026-1872, PYSEC-2026-2275 |
| python-dotenv | 1.0.1 | 1.2.2 | PYSEC-2026-2270 |

This was a real upgrade, not just an edit - `flask-cors` 4→6 is a major version bump, so
all three Docker images were rebuilt and tested against the real database container
before trusting the change (`/health`, `/projects`, and a real CORS preflight request all
verified, then the containers removed).

**Not fixed - no fix available upstream:** `ai-services/rag-server/requirements.txt` pins
`chromadb` (unpinned, resolves to 1.5.9, the current latest release). `pip-audit` flags 4
CVEs against it (PYSEC-2026-311, -3813, -3814, -3815), none with a fix version yet.
Documented openly rather than suppressed; this is shared code, not mine to fix.

My scoped `pip-audit` hook no longer checks other students' `requirements.txt` files -
under the ownership model, that's each student's own responsibility, run through their
own scoped hook once they set one up (students 1 and 2 already have, independently).

## Blocked-commit verification (re-run today, under the current scoped config)

Planted a fake AWS access key in a throwaway file inside my own scoped folder,
staged it, and attempted a real commit:

```bash
git add student-4Nicholas-Hatzidimitriou/fake_secret_test.py
git commit -m "test: deliberately planted fake secret to verify pre-commit blocks it"
```

Result: **blocked**. The scoped `student4-detect-secrets` hook caught it as both an
`AWS Access Key` and a `Secret Keyword` finding, flagged it as unaudited, and the commit
failed. `git log -1` confirmed no new commit was created. The file was then removed from
the index and the working tree.

## Summary

- Pre-commit scanning relocated from a repo-wide root config to one scoped entirely to
  `student-4Nicholas-Hatzidimitriou/`, matching students 1 and 2's layout, while remaining
  a real, auto-triggering git hook (verified via the installed hook script, not just
  manual runs).
- All three hooks pass cleanly today, scoped scan, fresh output captured above.
- 3 real findings fixed in my own code (S104 + S201, ×3 files) - unchanged from before.
- 5 real/false-positive findings resolved in shared `ai-services/` code I maintain -
  unchanged from before, still true, just no longer covered by my own scoped hook.
- 4 real dependency vulnerabilities fixed across my own 3 `requirements.txt` files,
  re-verified clean today.
- 1 dependency vulnerability (chromadb) remains, documented as currently unfixable
  upstream, not mine to fix.
- Commit-blocking behaviour re-verified today with a real planted secret under the
  current scoped config, then reverted.
