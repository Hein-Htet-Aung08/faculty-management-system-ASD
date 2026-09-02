import json
import os

from openai import OpenAI

from services.prompt_loader import load_prompt


OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434/v1",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:0.5b",
)


client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama",
)


def extract_json(content):
    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]

    if content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())


def recommend_teaching_staff(context):
    system_prompt = load_prompt("allocation/system_prompt.txt")
    task_prompt = load_prompt(
        "allocation/staff_recommendation_prompt.txt"
    )

    user_prompt = (
        f"{task_prompt}\n\n"
        f"CONTEXT:\n"
        f"{json.dumps(context, indent=2)}"
    )

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    return extract_json(content)