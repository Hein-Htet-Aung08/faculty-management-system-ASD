
"""Two-model prompt construction for testing review."""


def build_implementation_prompt(task_prompt, evidence):
    return f"""
{task_prompt}

ORIGINAL TESTING EVIDENCE:
{evidence}

Assess test results, security checks, CI configuration,
report completeness, and possible stale evidence.

A configured GitHub Actions workflow does not prove
that the workflow ran successfully.

Treat the deterministic verdict as authoritative.
Use only the evidence supplied above.
""".strip()


def build_review_prompt(implementation, evidence):
    return f"""
ORIGINAL TESTING EVIDENCE:
{evidence}

FIRST MODEL ASSESSMENT:
{implementation}

Independently identify:
- Incorrect test counts
- Missing or outdated evidence
- Unsupported CI success claims
- Overlooked security failures
- Unsupported release recommendations

Do not declare deployment readiness when the
deterministic evidence says NOT_READY.
""".strip()
