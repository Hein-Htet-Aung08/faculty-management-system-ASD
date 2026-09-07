from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PROMPTS_DIR = BASE_DIR / "prompts"


def load_prompt(path):
    prompt_path = PROMPTS_DIR / path

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8").strip()