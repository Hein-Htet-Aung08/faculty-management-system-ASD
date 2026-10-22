import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent

MENU_TO_MODE = {
    "1": "db",
    "2": "endpoints",
    "3": "architecture",
    "4": "ai_mode",
    "5": "development_integrity",
    "6": "mcp",
    "7": "rag",
    "9": "multi_agent_workflow_review",
    "10": "testing_report_review",
    "11": "cloud_deployment_report_review",
}

MODE_ORDER = [
    "db",
    "endpoints",
    "architecture",
    "ai_mode",
    "development_integrity",
    "mcp",
    "rag",
    "multi_agent_workflow_review",
    "testing_report_review",
    "cloud_deployment_report_review",
]


def _load_env(env_path: Path) -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
        return
    except ImportError:
        pass

    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _run_testing_mode(run_mode):
    print("\nTesting Report Review:")
    print("  1) Review saved results (quick; no tests or network)")
    print("  2) Run fresh local tests + check GitHub Actions (may take minutes)")
    try:
        choice = input("Choose 1 or 2 [1]> ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if choice not in {"1", "2"}:
        print("Cancelled: choose 1 or 2.")
        return

    # An explicit '2' is required before running any test subprocesses.
    previous = os.environ.get("AGENTIC_TEST_RUN_MODE")
    try:
        os.environ["AGENTIC_TEST_RUN_MODE"] = "fresh" if choice == "2" else "saved"
        print(run_mode("testing_report_review", str(APP_DIR), str(REPO_ROOT)))
    finally:
        if previous is None:
            os.environ.pop("AGENTIC_TEST_RUN_MODE", None)
        else:
            os.environ["AGENTIC_TEST_RUN_MODE"] = previous


def _ask_release_decision(result):
    from collectors.cloud_deployment_report_collector import (
        RELEASE_DECISIONS,
        write_release_decision,
    )

    report = next(
        (line.split(":", 1)[1].strip() for line in result.splitlines() if line.startswith("Report:")),
        None,
    )
    if report is None:
        return  # the review did not complete, so there is nothing to decide on

    print("\nHuman release decision (the review above is advisory only):")
    for number, label in enumerate(RELEASE_DECISIONS, start=1):
        print(f"  {number}) {label}")
    print("  Enter) Skip - decide later")
    try:
        choice = input("Choose> ").strip()
        if not choice:
            print("No release decision recorded.")
            return
        decision = RELEASE_DECISIONS[int(choice) - 1]
        reviewer = input("Reviewer name> ")
        notes = input("Notes / conditions> ")
    except (EOFError, KeyboardInterrupt):
        print("\nNo release decision recorded.")
        return
    except (ValueError, IndexError):
        print("Unknown choice; no release decision recorded.")
        return

    path = write_release_decision(REPO_ROOT, decision, reviewer, notes, report)
    print(f"Release decision recorded: {decision} -> {path}")


def _run_cloud_mode(run_mode):
    print("\nCloud Deployment Report Review:")
    print("  1) Review saved deployment evidence (quick; no network)")
    print("  2) Also probe the deployed URLs (live GET requests)")
    try:
        choice = input("Choose 1 or 2 [1]> ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if choice not in {"1", "2"}:
        print("Cancelled: choose 1 or 2.")
        return

    previous = os.environ.get("AGENTIC_CLOUD_PROBE_MODE")
    try:
        os.environ["AGENTIC_CLOUD_PROBE_MODE"] = "live" if choice == "2" else "saved"
        result = run_mode("cloud_deployment_report_review", str(APP_DIR), str(REPO_ROOT))
    finally:
        if previous is None:
            os.environ.pop("AGENTIC_CLOUD_PROBE_MODE", None)
        else:
            os.environ["AGENTIC_CLOUD_PROBE_MODE"] = previous

    print(result)
    _ask_release_decision(result)


def main() -> None:
    _load_env(APP_DIR / ".env")

    from config.review_config import build_mode_config
    from core import reporter
    from core.orchestrator import run_mode

    modes = build_mode_config()
    reporter.print_prompt_map(APP_DIR, modes)

    while True:
        reporter.print_menu()
        try:
            choice = input("Select an option> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "0":
            print("Exiting.")
            return

        if choice == "8":
            # Run All deliberately uses saved reports so a broad command
            # never starts fresh test subprocesses without explicit consent.
            previous = os.environ.get("AGENTIC_TEST_RUN_MODE")
            try:
                os.environ["AGENTIC_TEST_RUN_MODE"] = "saved"
                for mode_key in MODE_ORDER:
                    print(reporter.divider())
                    print(run_mode(mode_key, str(APP_DIR), str(REPO_ROOT)))
            finally:
                if previous is None:
                    os.environ.pop("AGENTIC_TEST_RUN_MODE", None)
                else:
                    os.environ["AGENTIC_TEST_RUN_MODE"] = previous
            print(reporter.divider())
            continue

        mode_key = MENU_TO_MODE.get(choice)
        if mode_key is None:
            print(f"Unknown option: {choice!r}")
            continue

        if mode_key == "testing_report_review":
            _run_testing_mode(run_mode)
            continue

        if mode_key == "cloud_deployment_report_review":
            _run_cloud_mode(run_mode)
            continue

        result = run_mode(mode_key, str(APP_DIR), str(REPO_ROOT))
        reporter.print_result(result)


if __name__ == "__main__":
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))
    main()
