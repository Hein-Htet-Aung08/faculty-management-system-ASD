import os
import re
from functools import lru_cache
from pathlib import Path

from openai import OpenAI


# All three agents talk to the host's Ollama through its
# OpenAI-compatible endpoint, the same one AI-Mode uses.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")

# Planning is light work, so the small model is enough. The Worker
# must answer only from evidence and cite it; qwen2.5:0.5b tended to
# echo the evidence or mislabel records, so it uses llama3.1:8b.
PLANNER_MODEL = os.getenv("OLLAMA_PLANNER_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"))
WORKER_MODEL = os.getenv("OLLAMA_WORKER_MODEL", "llama3.1:8b")
REVIEW_MODEL = os.getenv("OLLAMA_REVIEW_MODEL", "llama3.1:8b")

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"


def env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return float(default)


def env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return int(default)


# llama3.1:8b can take a while to load on a CPU, so the review step gets longer.
AGENT_TIMEOUT_SECONDS = env_float("OLLAMA_TIMEOUT_SECONDS", "90")
REVIEW_TIMEOUT_SECONDS = env_float("OLLAMA_REVIEW_TIMEOUT_SECONDS", "180")


def load_prompt(name):
    return (PROMPT_DIR / name).read_text(encoding="utf-8").strip()


@lru_cache(maxsize=4)
def _client(timeout):
    # Ollama ignores the key, but the OpenAI client requires one; "ollama" is a placeholder.
    return OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama", timeout=timeout, max_retries=0)  # pragma: allowlist secret


def chat(model, prompt, *, max_tokens, timeout):
    """Single-turn completion. Raises openai.APIError if Ollama fails or times out."""
    response = _client(timeout).chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


def parse_sections(text, headings):
    """Split 'Heading: body' blocks into a dict. Missing headings are simply absent."""
    pattern = r"^\s*\**\s*(" + "|".join(re.escape(h) for h in headings) + r")\s*\**\s*:\s*\**"
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE))
    sections = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        canonical = next(h for h in headings if h.lower() == match.group(1).lower())
        sections[canonical] = text[match.end():end].strip()
    return sections
