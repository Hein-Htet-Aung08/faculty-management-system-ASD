"""Two-model prompt construction for Cloud Deployment Review."""


def build_implementation_prompt(task_prompt, evidence):
    return f"""
{task_prompt}

ORIGINAL CLOUD DEPLOYMENT EVIDENCE:
{evidence}

Assess the deployment workflow run, deployment scripts, cloud configuration,
per-student service reachability and CRUD evidence, and whether AI-Mode, MCP,
RAG and Multi-Agent are disabled in the cloud.

A configured workflow or a recorded URL does not prove a working deployment.

Treat the deterministic verdict as authoritative.
Use only the evidence supplied above.
""".strip()


def build_review_prompt(implementation, evidence):
    return f"""
ORIGINAL CLOUD DEPLOYMENT EVIDENCE:
{evidence}

FIRST MODEL ASSESSMENT:
{implementation}

Independently identify:
- Unsupported claims that a service is reachable or CRUD works
- Overlooked release blockers or AI features left enabled
- Results for one student applied to another
- Unsupported release recommendations

Do not recommend release when the deterministic evidence says NOT_READY.
""".strip()
