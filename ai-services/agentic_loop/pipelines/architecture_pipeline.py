def build_implementation_prompt(task_prompt, review_target, evidence):
    return task_prompt.replace("{{REVIEW_TARGET}}", review_target).replace(
        "{{VALIDATION_EVIDENCE}}", evidence
    )


def build_review_prompt(evidence, implementation_output):
    return (
        "ORIGINAL EVIDENCE (ground truth - collected from the real repo):\n"
        f"{evidence}\n\n"
        "FIRST MODEL'S ARCHITECTURE ASSESSMENT (to be critiqued):\n"
        f"{implementation_output}\n\n"
        "Critique the assessment above strictly against the original evidence."
    )
