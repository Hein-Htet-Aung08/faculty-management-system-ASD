import re
from pathlib import Path

_SKIP_PARTS = {
    "venv",
    ".venv",
    "node_modules",
    "__pycache__",
    "site-packages",
    ".git",
}

_ROUTE_RE = re.compile(
    r"""@(\w+)\.(route|get|post|put|delete|patch)\(\s*["']([^"']+)["']([^)]*)\)""",
    re.IGNORECASE,
)
_METHODS_RE = re.compile(r"""methods\s*=\s*\[([^\]]*)\]""", re.IGNORECASE)
_PREFIX_RE = re.compile(r"""url_prefix\s*=\s*["']([^"']+)["']""")
_STUDENT_NUM_RE = re.compile(r"student-?(\d+)", re.IGNORECASE)


def _is_noise(path):
    return any(part in _SKIP_PARTS for part in path.parts)


def find_student_dirs(repo_root):
    root = Path(repo_root)
    return sorted(
        (p for p in root.iterdir() if p.is_dir() and p.name.lower().startswith("student-")),
        key=lambda p: p.name.lower(),
    )


def student_number(student_dir):
    match = _STUDENT_NUM_RE.search(Path(student_dir).name)
    return match.group(1) if match else None


_STUDENT_LABEL_RE = re.compile(r"^student-?\d+-?", re.IGNORECASE)


def student_label(student_dir):
    name = Path(student_dir).name
    number = student_number(student_dir) or "?"
    rest = _STUDENT_LABEL_RE.sub("", name, count=1)
    display_name = re.sub(r"[-_]+", " ", rest).strip()
    return f"Student {number} {display_name}".strip() if display_name else f"Student {number}"


def _first_existing(student_dir, candidates):
    student_dir = Path(student_dir)
    for rel in candidates:
        candidate = student_dir / rel
        if candidate.exists():
            return candidate
    return None


def find_backend_app(student_dir):
    return _first_existing(
        student_dir,
        ["backend/app.py", "backend-service/app.py", "backend/main.py", "app.py", "server.py"],
    )


def find_routes_dir(student_dir):
    return _first_existing(
        student_dir,
        ["backend/routes", "backend-service/routes", "backend/app/routes", "routes"],
    )


def find_db_dir(student_dir):
    return _first_existing(
        student_dir,
        ["database-service", "database", "db-service", "db"],
    )


def find_frontend_entry(student_dir):
    return _first_existing(
        student_dir,
        [
            "frontend/index.html",
            "frontend/app.py",
            "frontend-service/index.html",
            "frontend-service/templates",
            "frontend/templates",
            "frontend",
            "frontend-service",
        ],
    )


def find_sqlite_files(*roots):
    seen = []
    for root in roots:
        if root is None:
            continue
        for db_path in Path(root).rglob("*.db"):
            if _is_noise(db_path) or db_path in seen:
                continue
            seen.append(db_path)
    return sorted(seen)


def _methods_from_tail(verb, tail):
    verb = verb.lower()
    if verb != "route":
        return [verb.upper()]
    match = _METHODS_RE.search(tail)
    if not match:
        return ["GET"]
    methods = [m.strip().strip("\"'").upper() for m in match.group(1).split(",")]
    return [m for m in methods if m] or ["GET"]


def scan_routes(scan_dir):
    scan_dir = Path(scan_dir)
    if not scan_dir.exists():
        return []

    routes = []
    py_files = [scan_dir] if scan_dir.is_file() else sorted(scan_dir.rglob("*.py"))
    for py_file in py_files:
        if _is_noise(py_file):
            continue
        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        prefix_match = _PREFIX_RE.search(text)
        prefix = prefix_match.group(1).rstrip("/") if prefix_match else ""
        for _deco, verb, path, tail in _ROUTE_RE.findall(text):
            methods = _methods_from_tail(verb, tail)
            full_path = f"{prefix}/{path.lstrip('/')}" if prefix else path
            routes.append((full_path, methods, py_file.name))
    unique = []
    marker = set()
    for path, methods, src in routes:
        key = (path, tuple(methods))
        if key in marker:
            continue
        marker.add(key)
        unique.append((path, methods, src))
    return unique
