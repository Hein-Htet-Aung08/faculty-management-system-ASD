import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

STUDENT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = STUDENT_DIR.parent
BACKEND_DIR = STUDENT_DIR / "backend"
DATABASE_DIR = STUDENT_DIR / "database"

# tests/manual/ holds hand-run scripts (e.g. test_llm.py calls a live Ollama
# on import), not pytest tests -- keep them out of automated runs and CI.
collect_ignore = ["manual"]

# MCP/RAG are always off in tests; individual tests switch them on with
# the servers replaced by fakes, so no shared server is ever contacted.
os.environ["MCP_ENABLED"] = "false"
os.environ["RAG_ENABLED"] = "false"

for path in (
    BACKEND_DIR,
    REPO_ROOT / "ai-services" / "mcp-server",
    REPO_ROOT / "ai-services" / "rag-server",
):
    sys.path.insert(0, str(path))


@pytest.fixture(scope="session")
def seeded_db(tmp_path_factory):
    """Builds the database once using the real init_db.py and seed.py scripts."""
    db_path = tmp_path_factory.mktemp("seed") / "staff.db"
    env = {**os.environ, "DB_PATH": str(db_path)}

    for script in ("init_db.py", "seed.py"):
        subprocess.run(
            [sys.executable, script],
            cwd=DATABASE_DIR,
            env=env,
            check=True,
            capture_output=True,
        )

    return db_path


@pytest.fixture
def client(seeded_db, tmp_path, monkeypatch):
    """Flask test client backed by a fresh copy of the seeded database."""
    import app as app_module

    db_copy = tmp_path / "staff.db"
    shutil.copy(seeded_db, db_copy)
    monkeypatch.setattr(app_module, "DATA_DIR", str(db_copy))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client
