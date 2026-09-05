from pathlib import Path

import yaml

from collectors.common import (
    find_backend_app,
    find_db_dir,
    find_frontend_entry,
    find_student_dirs,
    student_number,
)


def _compose_services(raw_text):
    try:
        doc = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError:
        return None
    services = doc.get("services")
    return services if isinstance(services, dict) else {}


def collect(app_dir, repo_root):
    repo_root = Path(repo_root)
    students = find_student_dirs(repo_root)
    if not students:
        return False, "No student-* folders found at the repo root."

    lines = []

    for student_dir in students:
        number = student_number(student_dir) or "?"
        checks = {
            "frontend entrypoint": find_frontend_entry(student_dir),
            "backend app.py": find_backend_app(student_dir),
            "database service/folder": find_db_dir(student_dir),
        }
        present = [name for name, found in checks.items() if found]
        missing = [name for name, found in checks.items() if not found]
        lines.append(
            f"[student {number}] {student_dir.name}: "
            f"present={present or ['none']}; missing={missing or ['none']}"
        )

    compose_path = repo_root / "docker-compose.yml"
    if not compose_path.is_file():
        lines.append("shared docker-compose.yml: MISSING at repo root.")
        evidence = "ARCHITECTURE EVIDENCE:\n" + "\n".join(lines)
        return True, evidence

    raw = compose_path.read_text(encoding="utf-8")
    services = _compose_services(raw)
    if services is None:
        lines.append("shared docker-compose.yml: present but YAML failed to parse; using text scan.")
        services = {}
    service_names = list(services.keys())
    lines.append(
        f"shared docker-compose.yml: {len(service_names)} service(s) -> "
        f"{', '.join(service_names) or '(none parsed)'}"
    )

    ollama_found = "ollama" in service_names or "ollama:" in raw
    lines.append(f"  shared Ollama AI-Mode service: {'FOUND' if ollama_found else 'MISSING'}")

    for student_dir in students:
        number = student_number(student_dir)
        context_hit = f"./{student_dir.name}" in raw
        name_hit = any(
            f"student{number}" in name or f"student-{number}" in name for name in service_names
        )
        found = context_hit or name_hit
        lines.append(
            f"  compose entry for student {number} ({student_dir.name}): "
            f"{'FOUND' if found else 'MISSING'}"
        )

    evidence = "ARCHITECTURE EVIDENCE:\n" + "\n".join(lines)
    return True, evidence
