def build_user_prompt(task_prompt, context_prompt, review_target, evidence):
    task = task_prompt.replace("{{REVIEW_TARGET}}", review_target).replace(
        "{{VALIDATION_EVIDENCE}}", evidence
    )
    return f"{context_prompt}\n\n{task}"
