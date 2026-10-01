def build_implementation_prompt(
    task_prompt,
    evidence,
):
    return f"""
{task_prompt}

Review Scope:
Shared RAG Pipeline Integration

Observed Evidence:
{evidence}

Assess whether the RAG implementation is operational,
grounded, measurable and suitable for Release 1.

Stay strictly within the supplied evidence.
""".strip()


def build_review_prompt(
    implementation_output,
    evidence,
):
    return f"""
Implementation assessment:
{implementation_output}

Observed evidence:
{evidence}

Review the assessment against the evidence.
Identify unsupported conclusions, retrieval risks,
grounding risks or missing validation.

Stay strictly within the supplied evidence.
""".strip()