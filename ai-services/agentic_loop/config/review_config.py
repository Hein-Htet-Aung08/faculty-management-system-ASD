from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ModeConfig:
    key: str
    label: str
    prompt_family: str
    implementation_prompts: Tuple[str, ...]
    review_prompts: Tuple[str, ...] = field(default_factory=tuple)
    per_student: bool = False


def build_mode_config():
    service_impl = (
        "implementation/system_prompt.txt",
        "implementation/task_prompt.txt",
        "implementation/context_prompt.txt",
    )
    return {
        "db": ModeConfig(
            key="db",
            label="Database validation review",
            prompt_family="service",
            implementation_prompts=service_impl,
            per_student=True,
        ),
        "endpoints": ModeConfig(
            key="endpoints",
            label="Endpoint HTTP review",
            prompt_family="service",
            implementation_prompts=service_impl,
            per_student=True,
        ),
        "architecture": ModeConfig(
            key="architecture",
            label="Team architecture review",
            prompt_family="team",
            implementation_prompts=(
                "implementation/architecture_system_prompt.txt",
                "implementation/architecture_task_prompt.txt",
            ),
            review_prompts=("review/agent_review_prompt.txt",),
            per_student=False,
        ),
    }
