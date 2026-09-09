import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

_HTTP_TIMEOUT = 3


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_database_modules(database_dir):
    resource_config = _load_module(
        "student5_integrity_resource_config", database_dir / "resource_config.py"
    )

    previous = sys.modules.get("resource_config")
    sys.modules["resource_config"] = resource_config
    try:
        validation = _load_module(
            "student5_integrity_validation", database_dir / "validation.py"
        )
    finally:
        if previous is None:
            sys.modules.pop("resource_config", None)
        else:
            sys.modules["resource_config"] = previous

    schema = _load_module("student5_integrity_schema", database_dir / "schema.py")
    return resource_config, validation, schema


def _insert(connection, spec, values):
    columns = list(values)
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"INSERT INTO {spec['table']} ({', '.join(columns)}) VALUES ({placeholders})",
        [values[column] for column in columns],
    )


def _run_disposable_probes(resource_config, validation, schema):
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        schema.create_schema(connection)
        probes = [
            (
                "Completed development goal with progress=25",
                "development-goals",
                {
                    "staffID": 901,
                    "title": "Disposable integrity probe",
                    "progress": 25,
                    "status": "Completed",
                },
            ),
        ]

        results = []
        for label, resource, payload in probes:
            try:
                normalized = validation.validate_payload(resource, payload)
                _insert(connection, resource_config.RESOURCES[resource], normalized)
                connection.rollback()
                results.append(
                    f"ACCEPTED by validate_payload and SQLite: {label}."
                )
            except (ValueError, sqlite3.IntegrityError) as exc:
                connection.rollback()
                results.append(f"REJECTED: {label} ({type(exc).__name__}: {exc}).")
        return results
    finally:
        connection.close()


def _live_api_evidence(base_url):
    lines = []
    try:
        with urlopen(f"{base_url}/health", timeout=_HTTP_TIMEOUT) as response:
            lines.append(f"GET /health -> HTTP {response.status}.")

        with urlopen(
            f"{base_url}/development-goals", timeout=_HTTP_TIMEOUT
        ) as response:
            lines.append(f"GET /development-goals -> HTTP {response.status}.")
            goals = json.load(response)
        inconsistent = [
            row for row in goals
            if row.get("status") == "Completed" and row.get("progress") != 100
        ]
        lines.append(
            f"Live rows: {len(goals)} development goals; "
            f"{len(inconsistent)} Completed goal(s) have progress other than 100."
        )

    except HTTPError as exc:
        lines.append(f"Live database API check failed (HTTP {exc.code}).")
    except URLError:
        lines.append("Live database API unavailable; static and disposable probes still ran.")
    except (OSError, ValueError) as exc:
        lines.append(f"Live database API check failed ({type(exc).__name__}: {exc}).")
    return lines


def _format_enum(values):
    return ", ".join(sorted(values))


def collect(student_dir, number):
    student_dir = Path(student_dir)
    if str(number) != "5":
        return False, "Development integrity review is scoped to Student 5."

    database_dir = student_dir / "database-service"
    required_files = [
        database_dir / "schema.py",
        database_dir / "resource_config.py",
        database_dir / "validation.py",
    ]
    missing = [path.name for path in required_files if not path.is_file()]
    if missing:
        return False, (
            f"DEVELOPMENT RECORD INTEGRITY EVIDENCE for {student_dir.name}:\n"
            f"missing required evidence files: {', '.join(missing)}."
        )

    resource_config, validation, schema = _load_database_modules(database_dir)
    goal_statuses = validation.ENUMS[("development-goals", "status")]
    lines = [
        "PLAN concern: development-goal lifecycle integrity between status and progress.",
        "Source files inspected: database-service/schema.py, resource_config.py, validation.py.",
        f"DevelopmentGoals status values: {_format_enum(goal_statuses)}; progress range: 0 to 100.",
        "Disposable validation + in-memory SQLite probes (the real database was not modified):",
    ]
    lines.extend(f"- {result}" for result in _run_disposable_probes(
        resource_config, validation, schema
    ))

    base_url = os.getenv("STUDENT5_DB_URL", "http://localhost:5105").rstrip("/")
    lines.append(f"Read-only live API check at {base_url}:")
    lines.extend(f"- {result}" for result in _live_api_evidence(base_url))

    evidence = (
        f"DEVELOPMENT RECORD INTEGRITY EVIDENCE for {student_dir.name}:\n"
        + "\n".join(lines)
    )
    return True, evidence
