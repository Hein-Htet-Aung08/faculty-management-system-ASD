import os
import sqlite3

import requests

from collectors.common import find_db_dir, find_sqlite_files

MIN_RECORDS = 10
_HTTP_TIMEOUT = 3


def _probe_health(url):
    try:
        response = requests.get(url, timeout=_HTTP_TIMEOUT)
        body = response.text.strip().replace("\n", " ")
        return f"HTTP {response.status_code}; body: {body[:160]}"
    except requests.exceptions.ConnectionError:
        return "[CONNECTION REFUSED - service not running]"
    except requests.RequestException as exc:
        return f"[error: {type(exc).__name__}]"


def _inspect_sqlite(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        tables = [
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        counts = {}
        for table in tables:
            try:
                counts[table] = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            except sqlite3.Error as exc:
                counts[table] = f"error({exc})"
        return tables, counts
    finally:
        conn.close()


def _summarise_counts(counts):
    numeric = {t: c for t, c in counts.items() if isinstance(c, int)}
    if not numeric:
        return "no readable tables", False
    passing = [t for t, c in numeric.items() if c >= MIN_RECORDS]
    detail = ", ".join(f"{t}={c}" for t, c in counts.items())
    verdict = "meets >=10 rule" if len(passing) == len(numeric) else "BELOW >=10 rule"
    return f"{detail}  ({len(passing)}/{len(numeric)} tables {verdict})", len(passing) == len(numeric)


def collect(student_dir, number):
    db_dir = find_db_dir(student_dir)
    if db_dir is None:
        return False, (
            f"DATABASE VALIDATION EVIDENCE for {student_dir.name}:\n"
            "no database folder found (looked for database-service/, database/)."
        )

    lines = []

    has_service = (db_dir / "app.py").is_file()
    if has_service:
        url = os.getenv(f"STUDENT{number}_DB_URL", f"http://localhost:510{number}") + "/health"
        lines.append(f"live database-service check {url} -> {_probe_health(url)}")

    db_files = find_sqlite_files(db_dir, student_dir)
    if db_files:
        for db_file in db_files:
            rel = db_file.relative_to(student_dir)
            try:
                tables, counts = _inspect_sqlite(db_file)
            except sqlite3.Error as exc:
                lines.append(f"{rel} unreadable ({exc}).")
                continue
            if not tables:
                lines.append(f"{rel} has no user tables.")
                continue
            summary, _ok = _summarise_counts(counts)
            lines.append(f"{rel} -> {len(tables)} table(s): {summary}")
    elif has_service:
        init_scripts = sorted(
            p.name for p in db_dir.iterdir() if p.name in {"init_db.py", "seed.py", "schema.py"}
        )
        note = f"init scripts: {', '.join(init_scripts)}" if init_scripts else "no init scripts"
        lines.append(f"no .db file built yet ({note}).")
    else:
        lines.append(f"{db_dir.name}/ has no app.py and no .db file.")

    evidence = f"DATABASE VALIDATION EVIDENCE for {student_dir.name}:\n" + "\n".join(lines)
    return True, evidence
