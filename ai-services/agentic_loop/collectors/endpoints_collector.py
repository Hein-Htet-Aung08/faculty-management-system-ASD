import os
import re
import time

import requests

from collectors.common import find_backend_app, find_routes_dir, scan_routes

_HTTP_TIMEOUT = 4
_PATH_PARAM_RE = re.compile(r"<[^>]+>")


def _concrete_path(path):
    return _PATH_PARAM_RE.sub("1", path)


def _test_endpoint(base_url, path, method):
    concrete = _concrete_path(path)
    if method not in ("GET", "POST"):
        return f"{method} {concrete} was discovered but not exercised (non GET/POST)", False

    url = base_url.rstrip("/") + "/" + concrete.lstrip("/")
    started = time.perf_counter()
    try:
        if method == "GET":
            response = requests.get(url, timeout=_HTTP_TIMEOUT)
        else:
            response = requests.post(url, json={}, timeout=_HTTP_TIMEOUT)
        elapsed_ms = (time.perf_counter() - started) * 1000
        return f"{method} {concrete} responded {response.status_code} ({elapsed_ms:.0f} ms)", True
    except requests.exceptions.ConnectionError:
        return f"{method} {concrete} got connection refused - app not running", False
    except requests.RequestException as exc:
        return f"{method} {concrete} errored ({type(exc).__name__})", False


def collect(student_dir, number):
    base_url = os.getenv(f"STUDENT{number}_BASE_URL", f"http://localhost:500{number}")
    header = f"{student_dir.name} @ {base_url}"

    routes_dir = find_routes_dir(student_dir)
    if routes_dir is not None:
        routes = scan_routes(routes_dir)
    else:
        backend_app = find_backend_app(student_dir)
        routes = scan_routes(backend_app.parent) if backend_app else []

    if not routes:
        return False, f"ENDPOINT HTTP TEST EVIDENCE for {header}: no Flask routes discovered."

    sources = ", ".join(sorted({source for _path, _methods, source in routes}))
    clauses = []
    for path, methods, _source in routes:
        exercise = [m for m in methods if m in ("GET", "POST")] or methods[:1]
        for method in exercise:
            clause, _ok = _test_endpoint(base_url, path, method)
            clauses.append(clause)

    evidence = (
        f"ENDPOINT HTTP TEST EVIDENCE for {header}: {len(routes)} route(s) discovered in "
        f"{sources} - " + "; ".join(clauses) + "."
    )
    return True, evidence
