
"""Prompt construction for Multi-Agent Workflow Review."""


def build_implementation_prompt(task_prompt, evidence):
    return f"""
{task_prompt}

Review Scope:
Release 2 Multi-Agent Workflow Coordination

Collected Evidence:
{evidence}

Assess agent execution, evidence checks, human oversight,
audit completeness, and unresolved problems.

Do not invent additional workflow executions.
Use only the collected evidence.
""".strip()


def build_review_prompt(implementation_output, evidence):
    return f"""
Original collected evidence:
{evidence}

First model's assessment:
{implementation_output}

Independently review the assessment against the evidence.

Identify unsupported conclusions, missed validation failures,
incorrect approval claims, and missing audit information.

The deterministic evidence is authoritative.
Do not infer facts that are not recorded.
""".strip()
