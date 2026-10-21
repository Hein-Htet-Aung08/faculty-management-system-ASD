import re

from agents.worker_agent import OUTPUT_HEADINGS


# Deterministic checks on the Worker output, run before the Reviewer.
# They catch problems an LLM reviewer can miss (a missing section, a
# citation to a record that was never supplied) and are passed to the
# Reviewer and saved with the workflow for the human reviewer.

CITATION = re.compile(r"\[([A-Za-z0-9_-]+/[^\[\]\s]+)\]")


def _check(name, passed, detail):
    return {"check": name, "passed": bool(passed), "detail": detail}


def check_worker_output(worker_result, evidence):
    sources = {item["source"] for item in evidence}
    sections = worker_result.get("sections", {})
    cited = sorted(set(CITATION.findall(worker_result.get("output", ""))))
    unknown = [source for source in cited if source not in sources]
    missing = [heading for heading in OUTPUT_HEADINGS if heading not in sections]

    return [
        _check("evidence_available", evidence, f"{len(evidence)} evidence items supplied"),
        _check("sections_present", not missing, f"missing: {', '.join(missing)}" if missing else "all sections present"),
        _check("output_not_empty", sections.get("Output", "").strip(), "Output section has content"
               if sections.get("Output", "").strip() else "Output section is empty"),
        _check("cites_evidence", cited, f"{len(cited)} distinct sources cited"),
        _check("citations_exist", not unknown, f"not in evidence: {', '.join(unknown)}"
               if unknown else "every cited source was supplied"),
    ]


def format_checks(checks):
    return "\n".join(
        f"- {'PASS' if c['passed'] else 'FAIL'} {c['check']}: {c['detail']}" for c in checks
    )
