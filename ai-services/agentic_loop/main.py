import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = APP_DIR.parent.parent

MENU_TO_MODE = {"1": "db", "2": "endpoints", "3": "architecture"}
MODE_ORDER = ["db", "endpoints", "architecture"]


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

        if choice == "4":
            for mode_key in MODE_ORDER:
                print(reporter.divider())
                print(run_mode(mode_key, str(APP_DIR), str(REPO_ROOT)))
            print(reporter.divider())
            continue

        mode_key = MENU_TO_MODE.get(choice)
        if mode_key is None:
            print(f"Unknown option: {choice!r}")
            continue

        result = run_mode(mode_key, str(APP_DIR), str(REPO_ROOT))
        reporter.print_result(result)


if __name__ == "__main__":
    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))
    main()
