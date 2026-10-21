"""Run the multi-agent workflow from the terminal.

    python workflow_runner.py run --feature student3 "Which staff are overloaded?"
    python workflow_runner.py decide <workflow_id> --decision Accept --reviewer "Tristan"
    python workflow_runner.py status
    python workflow_runner.py history --feature student3

`run` prints each agent's output, then asks for the human decision
(skip with --no-review to decide later through `decide` or the UI).
"""

import argparse
import json
import sys

from coordinator import (
    ALLOWED_DECISIONS,
    DecisionConflict,
    WorkflowNotFound,
    list_workflows,
    record_decision,
    run_workflow,
    workflow_status,
)
from evidence import FEATURES


SHORTCUTS = {"a": "Accept", "p": "Partially Accept", "c": "Correct", "r": "Reject"}


def banner(title):
    print(f"\n=== {title} " + "=" * max(0, 60 - len(title)))


def print_workflow(result):
    banner(f"Workflow {result['workflow_id']}")
    print(f"Feature: {result['feature_name']} ({result['feature']})")
    print(f"Request: {result['user_request']}")
    print(f"Duration: {result['duration_ms']} ms")

    banner(f"Planner Agent [{result['planner_result']['status']}]")
    print(result["planner_result"]["plan"])

    worker = result["worker_result"]
    banner(f"Worker Agent [{worker['status']}] - {worker['evidence_count']} evidence items")
    if worker.get("evidence_error"):
        print(f"Evidence error: {worker['evidence_error']}")
    print(worker["output"])

    banner(f"Reviewer Agent [{result['reviewer_result']['status']}]")
    print(result["reviewer_result"]["review"])


def ask_decision():
    banner("Human Review")
    print("Decision: [A]ccept  [P]artially accept  [C]orrect  [R]eject  [S]kip (decide later)")
    while True:
        choice = input("> ").strip().lower()[:1]
        if choice == "s":
            return None
        if choice in SHORTCUTS:
            decision = SHORTCUTS[choice]
            reviewer = input("Reviewer name: ").strip()
            notes = input("Notes (optional): ").strip()
            correction = ""
            while decision == "Correct" and not correction:
                correction = input("Correction (required): ").strip()
            return decision, reviewer, notes, correction
        print("Enter A, P, C, R or S.")


def cmd_run(args):
    result = run_workflow(args.request, args.feature)
    print_workflow(result)

    answer = None if args.no_review else ask_decision()
    if answer is None:
        print(f"\nAwaiting human review. Decide later with:\n"
              f"  python workflow_runner.py decide {result['workflow_id']} --decision Accept")
        return

    decision, reviewer, notes, correction = answer
    final = record_decision(result["workflow_id"], decision, reviewer, notes, correction)
    print(f"\nRecorded: {final['human_decision']['decision']} -> {final['status']}")


def cmd_decide(args):
    final = record_decision(args.workflow_id, args.decision, args.reviewer, args.notes, args.correction)
    print(json.dumps(final["human_decision"], indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Faculty Management multi-agent workflow")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run Planner -> Worker -> Reviewer -> Human Review")
    run.add_argument("request", help="the user request")
    run.add_argument("--feature", required=True, choices=list(FEATURES))
    run.add_argument("--no-review", action="store_true", help="skip the interactive human decision")

    decide = sub.add_parser("decide", help="record the human decision for a workflow")
    decide.add_argument("workflow_id")
    decide.add_argument("--decision", required=True, help=" | ".join(ALLOWED_DECISIONS))
    decide.add_argument("--reviewer", default="")
    decide.add_argument("--notes", default="")
    decide.add_argument("--correction", default="")

    sub.add_parser("status", help="history and audit counts plus the latest workflow")

    history = sub.add_parser("history", help="recent workflows, newest first")
    history.add_argument("--feature")
    history.add_argument("--limit", type=int, default=10)

    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            cmd_run(args)
        elif args.command == "decide":
            cmd_decide(args)
        elif args.command == "status":
            print(json.dumps(workflow_status(), indent=2))
        else:
            print(json.dumps(list_workflows(args.feature, args.limit), indent=2))
    except (ValueError, WorkflowNotFound, DecisionConflict) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
