import os
from openai import OpenAI

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")

client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")

def generate_response(prompt: str) -> str:

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content