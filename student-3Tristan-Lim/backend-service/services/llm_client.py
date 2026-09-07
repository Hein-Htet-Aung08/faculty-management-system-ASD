import json
import os
import re

from openai import OpenAI

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama", timeout=LLM_TIMEOUT)


def create_chat_completion(messages, max_tokens=600, temperature=0.2, model=None):
    response = client.chat.completions.create(
        model=model or OLLAMA_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def ask(system_prompt, user_prompt, max_tokens=600, temperature=0.2, model=None):
    answer = create_chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        model=model,
    )
    return (answer or "").strip()


def extract_json(text):
    """Pull the first JSON object out of a model response.

    Small local models often wrap JSON in prose or a fenced code block, so the
    raw string is rarely parseable as-is.
    """
    if not text:
        return None

    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    start = text.find("{")
    if start == -1:
        return None

    # Walk forward to the matching brace so trailing prose is ignored.
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:index + 1])
                except json.JSONDecodeError:
                    return None
    return None
