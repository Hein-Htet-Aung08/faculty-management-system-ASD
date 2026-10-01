from collectors import (
    ai_mode_collector,
    architecture_collector,
    db_collector,
    development_integrity_collector,
    endpoints_collector,
    rag_collector,
)
from pathlib import Path
from collectors.common import find_student_dirs, student_label, student_number
from config.review_config import build_mode_config
from core import reporter
from core.ai_runner import AIRunner
from core.prompt_registry import PromptRegistry
from pipelines import (
    ai_mode_pipeline,
    architecture_pipeline,
    db_pipeline,
    development_integrity_pipeline,
    endpoints_pipeline,
    rag_pipeline,
)
import re

_PER_STUDENT_COLLECTORS = {
    "db": db_collector.collect,
    "endpoints": endpoints_collector.collect,
    "ai_mode": ai_mode_collector.collect,
    "development_integrity": development_integrity_collector.collect,
}

_PER_STUDENT_PIPELINES = {
    "db": db_pipeline,
    "endpoints": endpoints_pipeline,
    "ai_mode": ai_mode_pipeline,
    "development_integrity": development_integrity_pipeline,
}

_PER_STUDENT_TARGETS = {
    "db": "student {label}'s microservice database",
    "endpoints": "student {label}'s microservice HTTP API",
    "ai_mode": "student {label}'s AI-Mode integration",
    "development_integrity": "student {label}'s development goal lifecycle integrity",
}

_MODE_DISPLAY = {
    "db": "DB",
    "endpoints": "Endpoints",
    "architecture": "Architecture",
    "ai_mode": "AI-Mode",
    "development_integrity": "Student 5 Development Integrity",
    "rag": "RAG",
}

_ARCHITECTURE_TARGET = "the team's five-microservice system and its shared docker-compose stack"


def _log(tag, step, message):
    print(f"[{tag}][{step}] {message}")


def run_mode(mode_key, app_dir, repo_root, *, modes=None, registry=None, runner=None):
    modes = modes or build_mode_config()
    registry = registry or PromptRegistry(app_dir)
    runner = runner or AIRunner()

    cfg = modes.get(mode_key)
    if cfg is None:
        return f"OBSERVE FAILED: unknown mode {mode_key!r}"

    if mode_key == "rag":
        return _run_rag(
            cfg,
            app_dir,
            repo_root,
            registry,
            runner,
        )

    if cfg.per_student:
        return _run_per_student(cfg, app_dir, repo_root, registry, runner)
    return _run_architecture(cfg, app_dir, repo_root, registry, runner)


def _run_per_student(cfg, app_dir, repo_root, registry, runner):
    mode_key = cfg.key
    collector = _PER_STUDENT_COLLECTORS[mode_key]
    pipeline = _PER_STUDENT_PIPELINES[mode_key]
    target_template = _PER_STUDENT_TARGETS[mode_key]

    students = find_student_dirs(repo_root)
    if cfg.student_numbers:
        students = [
            student for student in students
            if student_number(student) in cfg.student_numbers
        ]
    if not students:
        return f"[{cfg.label}]\nOBSERVE FAILED: no student-* folders found at the repo root."

    system_prompt, task_prompt, context_prompt = (
        registry.read(cfg.prompt_family, rel) for rel in cfg.implementation_prompts
    )

    reporter.print_running_header(_MODE_DISPLAY[mode_key])

    summary_rows = []
    report_paths = []

    for student_dir in students:
        number = student_number(student_dir) or "?"
        label = student_label(student_dir)
        tag = f"{mode_key.upper()} - {student_dir.name}"

        if mode_key == "development_integrity":
            _log(tag, "PLAN", "Review development goal status/progress integrity.")
            _log(tag, "ACT", "Collecting evidence from Student 5 without changing its database.")
        else:
            _log(tag, "START", cfg.label)
            _log(tag, "OBSERVE", "Collecting evidence.")
        try:
            ok, evidence = collector(student_dir, number)
        except Exception as exc:
            _log(tag, "OBSERVE", f"crashed: {type(exc).__name__}")
            evidence = f"[COLLECTOR CRASHED: {type(exc).__name__}: {exc}]"
            review = "[SKIPPED - collector crashed, LLM not called]"
            reporter.print_student_result(label, evidence, review)
            report_paths.append(
                reporter.write_student_report(app_dir, mode_key, student_dir.name, number, evidence, review)
            )
            summary_rows.append((student_dir.name, "CRASHED", f"{type(exc).__name__}: {exc}"))
            continue

        if not ok:
            _log(tag, "OBSERVE", "FAILED - not calling the LLM.")
            review = "[SKIPPED - observe failed, LLM not called]"
            reporter.print_student_result(label, evidence, review)
            report_paths.append(
                reporter.write_student_report(app_dir, mode_key, student_dir.name, number, evidence, review)
            )
            summary_rows.append((student_dir.name, "OBSERVE FAILED", evidence.splitlines()[-1]))
            continue
        if mode_key == "development_integrity":
            _log(tag, "ACT", "Evidence collected.")
        else:
            _log(tag, "OBSERVE", "Evidence collected.")

        _log(tag, "PROMPTS", f"Loaded '{cfg.prompt_family}' prompt family.")
        target = target_template.format(label=f"{number} ({student_dir.name})")
        user_prompt = pipeline.build_user_prompt(task_prompt, context_prompt, target, evidence)

        if mode_key == "development_integrity":
            _log(tag, "OBSERVE", "Sending only the collected evidence to the LLM.")
        _log(tag, "LLM", f"Implementation model ({runner.model_for(False)}).")
        review, error = runner.call(system_prompt, user_prompt, review=False)
        _log(tag, "DONE", "error" if error else "ok")

        full_review = review if not error else f"[LLM ERROR: {error}]"
        reporter.print_student_result(label, evidence, full_review)

        if mode_key == "development_integrity":
            _log(tag, "ADAPT", "Recommendations recorded for human validation; no feature change applied.")
            report_path = reporter.write_development_integrity_report(
                app_dir, student_dir.name, number, evidence, full_review
            )
        else:
            report_path = reporter.write_student_report(
                app_dir, mode_key, student_dir.name, number, evidence, full_review
            )
        report_paths.append(report_path)

        summary_rows.append(
            (
                student_dir.name,
                "LLM ERROR" if error else "ok",
                full_review if error else reporter.truncate_words(full_review),
            )
        )

    summary = reporter.format_summary_table(cfg.label, summary_rows)
    files_note = "\n".join(f"  - {p}" for p in report_paths) or "  (none written)"
    return f"{summary}\n\nReports written:\n{files_note}"

def _build_rag_deterministic_summary(
    evidence,
):
    lines = [
        "Status: PASS",
        (
            "Functional validation: PASS "
            "(structure, tools, health, corpus refresh, "
            "retrieval, grounded answer, citations, confidence, "
            "insufficient-context handling, audit logging)"
        ),
    ]

    metrics_match = re.search(
        (
            r"mean P@5=([0-9.]+), "
            r"mean R@5=([0-9.]+), "
            r"minimum R@5=([0-9.]+)"
        ),
        evidence,
    )

    if metrics_match:
        mean_p = float(
            metrics_match.group(1)
        )

        mean_r = float(
            metrics_match.group(2)
        )

        minimum_r = float(
            metrics_match.group(3)
        )

        lines.append(
            "Retrieval quality: "
            f"mean P@5={mean_p:.3f}, "
            f"mean R@5={mean_r:.3f}, "
            f"minimum R@5={minimum_r:.3f}"
        )

        if minimum_r < 1.0:
            lines.append(
                "Observed recall limitation: "
                f"minimum R@5={minimum_r:.3f}, so at least "
                "one benchmark did not retrieve all expected "
                "relevant evidence at k=5."
            )

        else:
            lines.append(
                "Observed recall limitation: "
                "None in the recorded R@5 benchmarks."
            )

    else:
        lines.append(
            "Retrieval quality: "
            "Recorded in OBSERVE evidence; metrics could not "
            "be extracted for the deterministic summary."
        )

    return "\n".join(
        lines
    )

def _run_rag(
    cfg,
    app_dir,
    repo_root,
    registry,
    runner,
):
    tag = "RAG"

    reporter.print_running_header(
        "RAG"
    )

    _log(
        tag,
        "OBSERVE",
        "Collecting shared RAG evidence.",
    )

    try:
        ok, evidence = (
            rag_collector.collect(
                app_dir,
                repo_root,
            )
        )

    except Exception as exc:
        return (
            "OBSERVE FAILED: "
            f"{type(exc).__name__}: {exc}"
        )

    if not ok:
        return (
            "OBSERVE FAILED:\n"
            + evidence
        )

    deterministic_summary = (
        _build_rag_deterministic_summary(
            evidence
        )
    )

    _log(
        tag,
        "ACT",
        "Running implementation assessment.",
    )

    shared_prompts = (
        Path(app_dir)
        / "prompts"
    )

    task_prompt = (
        shared_prompts
        / "implementation"
        / "rag_implementation_prompt.txt"
    ).read_text(
        encoding="utf-8"
    ).strip()

    user_prompt = (
        rag_pipeline
        .build_implementation_prompt(
            task_prompt,
            evidence,
        )
    )

    system_prompt = (
        "You are a precise RAG implementation validator. "
        "Use only supplied evidence."
    )

    implementation, error = (
        runner.call(
            system_prompt,
            user_prompt,
            review=False,
        )
    )

    if error:
        implementation = (
            f"[LLM ERROR: {error}]"
        )

        review = (
            "[SKIPPED - implementation "
            "assessment failed]"
        )

    else:
        _log(
            tag,
            "ADAPT",
            "Running review model.",
        )

        review_prompt = (
            shared_prompts
            / "review"
            / "rag_review_prompt.txt"
        ).read_text(
            encoding="utf-8"
        ).strip()

        reasoning_prompt = (
            shared_prompts
            / "review"
            / "rag_reasoning_prompt.txt"
        ).read_text(
            encoding="utf-8"
        ).strip()

        review_system = (
            f"{review_prompt}\n\n"
            f"{reasoning_prompt}"
        )

        review_user = (
            rag_pipeline
            .build_review_prompt(
                implementation,
                evidence,
            )
        )

        review, review_error = (
            runner.call(
                review_system,
                review_user,
                review=True,
            )
        )

        if review_error:
            review = (
                f"[LLM ERROR: "
                f"{review_error}]"
            )

    print(
        "\nOBSERVE:\n"
        f"{evidence}\n"
    )

    print(
        "DETERMINISTIC VALIDATION:\n"
        f"{deterministic_summary}\n"
    )

    print(
        "IMPLEMENTATION:\n"
        f"{implementation}\n"
    )

    print(
        "REVIEW:\n"
        f"{review}\n"
    )

    report_path = (
        reporter
        .write_rag_validation_report(
            repo_root,
            evidence,
            deterministic_summary,
            implementation,
            review,
        )
    )

    _log(
        tag,
        "RECORD",
        f"Report written to {report_path}",
    )

    return (
        f"RAG validation run complete.\n"
        f"Report: {report_path}"
    )

def _run_architecture(cfg, app_dir, repo_root, registry, runner):
    tag = "ARCHITECTURE"

    reporter.print_running_header(_MODE_DISPLAY["architecture"])

    _log(tag, "START", cfg.label)
    _log(tag, "OBSERVE", "Collecting evidence across the whole repo.")
    try:
        ok, evidence = architecture_collector.collect(app_dir, repo_root)
    except Exception as exc:
        _log(tag, "OBSERVE", f"crashed: {type(exc).__name__}")
        evidence = f"[COLLECTOR CRASHED: {type(exc).__name__}: {exc}]"
        reporter.print_architecture_result(evidence)
        return f"[{cfg.label}]\nOBSERVE FAILED: {type(exc).__name__}: {exc}"

    if not ok:
        _log(tag, "OBSERVE", "FAILED - not calling the LLM.")
        reporter.print_architecture_result(evidence)
        return f"[{cfg.label}]\nOBSERVE FAILED: {evidence}"
    _log(tag, "OBSERVE", "Evidence collected.")

    _log(tag, "PROMPTS", f"Loading '{cfg.prompt_family}' prompt family.")
    system_prompt, task_prompt = (
        registry.read(cfg.prompt_family, rel) for rel in cfg.implementation_prompts
    )
    user_prompt = architecture_pipeline.build_implementation_prompt(
        task_prompt, _ARCHITECTURE_TARGET, evidence
    )

    _log(tag, "LLM", f"Implementation model ({runner.model_for(False)}): proposal.")
    proposal, error = runner.call(system_prompt, user_prompt, review=False)

    critique_text = None
    if error:
        _log(tag, "DONE", "implementation error")
        proposal_text = f"[LLM ERROR: {error}]"
    else:
        _log(tag, "LLM", "proposal ready")
        proposal_text = proposal
        review_system = registry.read(cfg.prompt_family, cfg.review_prompts[0])
        review_user = architecture_pipeline.build_review_prompt(evidence, proposal_text)

        _log(tag, "REVIEW", f"Review model ({runner.model_for(True)}): critique.")
        critique, review_error = runner.call(review_system, review_user, review=True)
        _log(tag, "DONE", "review error" if review_error else "ok")
        critique_text = critique if not review_error else f"[LLM ERROR: {review_error}]"

    reporter.print_architecture_result(evidence, proposal_text, critique_text)
    report_path = reporter.write_architecture_report(app_dir, evidence, proposal_text, critique_text)
    return f"Full report written: {report_path}"
