from pathlib import Path


class PromptRegistry:
    def __init__(self, app_dir):
        self._prompts_root = Path(app_dir) / "prompts"

    def path_for(self, family, relative_file):
        return self._prompts_root / family / relative_file

    def read(self, family, relative_file):
        target = self.path_for(family, relative_file)
        if not target.is_file():
            rel = Path("prompts") / family / relative_file
            raise FileNotFoundError(f"Prompt file not found: {rel}")
        text = target.read_text(encoding="utf-8").strip()
        if not text:
            rel = Path("prompts") / family / relative_file
            raise FileNotFoundError(f"Prompt file is empty: {rel}")
        return text
