def build_implementation_prompt(
    task_prompt,
    evidence,
):
    return f"""
{task_prompt}

Review Scope:
Shared MCP Server Integration

Observed Evidence:
{evidence}

Assess whether the MCP implementation is operational,
spec-compliant and suitable for Release 1.

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
Identify unsupported conclusions, transport risks,
tool-registration risks or missing validation.

Stay strictly within the supplied evidence.
""".strip()
