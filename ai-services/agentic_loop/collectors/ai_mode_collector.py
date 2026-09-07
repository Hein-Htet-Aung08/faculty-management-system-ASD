import re
from pathlib import Path

from collectors.common import find_backend_app

_SKIP_PARTS = {"venv", ".venv", "node_modules", "__pycache__", "site-packages", ".git"}


def _is_noise(path):
    return any(part in _SKIP_PARTS for part in path.parts)

_OLLAMA_RE = re.compile(r"ollama|OLLAMA_BASE_URL|OLLAMA_MODEL", re.IGNORECASE)
_TRY_EXCEPT_RE = re.compile(r"try\s*:\s*\n(?:.|\n)*?except", re.MULTILINE)
_PERSIST_RE = re.compile(r"INSERT\s+INTO\s+[\"'`]?(\w*ai\w*)", re.IGNORECASE)
_TIMEOUT_RE = re.compile(r"timeout\s*=", re.IGNORECASE)


def _backend_dir(student_dir):
    app = find_backend_app(student_dir)
    return app.parent if app else None


def _find_llm_client_files(backend_dir):
    if backend_dir is None:
        return []
    return sorted(
        p for p in backend_dir.rglob("*.py")
        if not _is_noise(p) and _OLLAMA_RE.search(p.read_text(encoding="utf-8", errors="replace"))
    )


def _find_prompt_templates(student_dir):
    student_dir = Path(student_dir)
    candidates = []
    for sub in ("backend/prompts", "backend-service/prompts", "prompts"):
        d = student_dir / sub
        if d.is_dir():
            candidates.extend(sorted(p.name for p in d.glob("*.txt")))
    return candidates


def collect(student_dir, number):
    student_dir = Path(student_dir)
    backend_dir = _backend_dir(student_dir)

    if backend_dir is None:
        return False, (
            f"AI-MODE INTEGRATION EVIDENCE for {student_dir.name}:\n"
            "no backend app.py found - cannot assess AI-Mode integration."
        )

    llm_files = _find_llm_client_files(backend_dir)
    lines = []

    if not llm_files:
        lines.append("no file in the backend references Ollama/OLLAMA_BASE_URL/OLLAMA_MODEL.")
    else:
        for f in llm_files:
            rel = f.relative_to(student_dir)
            text = f.read_text(encoding="utf-8", errors="replace")
            has_try = bool(_TRY_EXCEPT_RE.search(text))
            has_timeout = bool(_TIMEOUT_RE.search(text))
            lines.append(
                f"{rel}: calls Ollama; "
                f"error handling {'present' if has_try else 'MISSING'}; "
                f"explicit timeout {'set' if has_timeout else 'MISSING'}."
            )

    templates = _find_prompt_templates(student_dir)
    if templates:
        lines.append(f"prompt templates found: {', '.join(templates)} (externalised, not hardcoded).")
    else:
        lines.append("no external prompt template files found (prompt likely hardcoded inline, if present).")

    backend_files_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in backend_dir.rglob("*.py") if not _is_noise(p)
    )
    if _PERSIST_RE.search(backend_files_text):
        lines.append("AI output appears to be persisted to a database table (INSERT into an *ai* table found).")
    else:
        lines.append("no evidence of AI-generated output being persisted to a database table.")

    evidence = f"AI-MODE INTEGRATION EVIDENCE for {student_dir.name}:\n" + "\n".join(f"- {l}" for l in lines)
    return True, evidence
