import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def client():
    # Imported here so test_live_endpoints.py only needs pytest and requests.
    from app import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()
