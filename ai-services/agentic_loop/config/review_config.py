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
    student_numbers: Tuple[str, ...] = field(default_factory=tuple)


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
        "ai_mode": ModeConfig(
            key="ai_mode",
            label="AI-Mode integration review",
            prompt_family="service",
            implementation_prompts=(
                "ai_mode/system_prompt.txt",
                "ai_mode/task_prompt.txt",
                "ai_mode/context_prompt.txt",
            ),
            per_student=True,
        ),
        "development_integrity": ModeConfig(
            key="development_integrity",
            label="Student 5 development goal integrity review",
            prompt_family="service",
            implementation_prompts=(
                "development_integrity/system_prompt.txt",
                "development_integrity/task_prompt.txt",
                "development_integrity/context_prompt.txt",
            ),
            per_student=True,
            student_numbers=("5",),
        ),
    }
