import json
import time
from pathlib import Path

_WIDTH = 72
WORD_LIMIT = 45


def divider():
    return "=" * _WIDTH


def truncate_words(text, limit=WORD_LIMIT):
    words = text.split()
    if len(words) <= limit:
        return text
    return " ".join(words[:limit]) + " ..."


def print_menu():
    print(
        "\n".join(
            [
                "",
                divider(),
                "Agentic Loop",
                "  1) DB            - validate every student's database (real queries)",
                "  2) Endpoints     - test every student's live endpoints (real HTTP)",
                "  3) Architecture  - file layout + docker-compose (two-model review)",
                "  4) Run All",
                "  0) Exit",
                divider(),
            ]
        )
    )


def print_prompt_map(app_dir, modes):
    print(divider())
    print("Prompt path map:")
    for key, cfg in modes.items():
        family_dir = Path(app_dir) / "prompts" / cfg.prompt_family
        scope = "per-student" if cfg.per_student else "whole-codebase"
        print(f"  {key:<13} ({scope}) -> {family_dir}")
        for rel in tuple(cfg.implementation_prompts) + tuple(cfg.review_prompts):
            print(f"       - {cfg.prompt_family}/{rel}")


def print_result(result):
    print(divider())
    print(result)
    print(divider())


def print_running_header(mode_display):
    print(f"\nRunning {mode_display}\n")


def print_student_result(student_label, evidence, review):
    print(f"Observe - {student_label}:")
    print(evidence)
    print()
    print(f"Review - {student_label}:")
    print(review)
    print()


def print_architecture_result(evidence, proposal=None, critique=None):
    print("Observe:")
    print(evidence)
    print()
    if proposal is not None:
        print("Architecture Proposal:")
        print(proposal)
        print()
    if critique is not None:
        print("Review:")
        print(critique)
        print()


def format_summary_table(label, rows):
    name_width = max([len("student")] + [len(r[0]) for r in rows]) if rows else len("student")
    status_width = max([len("status")] + [len(r[1]) for r in rows]) if rows else len("status")

    lines = [divider(), f"Combined summary - {label}", divider()]
    header = f"{'student':<{name_width}}  {'status':<{status_width}}  note"
    lines.append(header)
    lines.append("-" * len(header))
    for student_name, status, note in rows:
        lines.append(f"{student_name:<{name_width}}  {status:<{status_width}}  {note}")
    lines.append(divider())
    return "\n".join(lines)


def _reports_dir(app_dir):
    reports_dir = Path(app_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def _timestamp():
    return time.strftime("%Y%m%d-%H%M%S")


def _write_pair(reports_dir, stem, markdown_body, json_payload):
    md_path = reports_dir / f"{stem}.md"
    json_path = reports_dir / f"{stem}.json"
    md_path.write_text(markdown_body, encoding="utf-8")
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    return md_path


def write_student_report(app_dir, mode_key, student_name, number, evidence, review):
    reports_dir = _reports_dir(app_dir)
    timestamp = _timestamp()
    stem = f"{mode_key}-student-{number}-{timestamp}"

    markdown = (
        f"# {mode_key.upper()} review - {student_name}\n\n"
        f"Generated: {timestamp}\n\n"
        "## OBSERVE (real evidence)\n\n"
        f"```\n{evidence}\n```\n\n"
        "## REVIEW (model output)\n\n"
        f"{review}\n"
    )
    payload = {
        "mode": mode_key,
        "student": student_name,
        "student_number": number,
        "timestamp": timestamp,
        "evidence": evidence,
        "review": review,
    }
    return _write_pair(reports_dir, stem, markdown, payload)


def write_architecture_report(app_dir, evidence, proposal, critique):
    reports_dir = _reports_dir(app_dir)
    timestamp = _timestamp()
    stem = f"architecture-{timestamp}"

    sections = [
        "# Architecture review - whole codebase\n",
        f"Generated: {timestamp}\n",
        "## OBSERVE (real evidence)\n",
        f"```\n{evidence}\n```\n",
        "## ARCHITECTURE PROPOSAL (implementation model)\n",
        f"{proposal}\n",
    ]
    if critique is not None:
        sections += ["## REVIEW (review model)\n", f"{critique}\n"]
    markdown = "\n".join(sections)

    payload = {
        "mode": "architecture",
        "timestamp": timestamp,
        "evidence": evidence,
        "proposal": proposal,
        "critique": critique,
    }
    return _write_pair(reports_dir, stem, markdown, payload)
