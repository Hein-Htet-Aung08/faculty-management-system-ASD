import os
from openai import OpenAI
 
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
 
client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
 
 
def generate_response(task_prompt: str, system_prompt: str = None, max_tokens: int = 150) -> str:
    """
    Calls the local Ollama model. If a system_prompt is supplied, it is sent
    as the 'system' role message (defines the agent's rules/behaviour);
    task_prompt is sent as the 'user' role message (the actual instructions
    with real data substituted in).
    """
    messages = []
 
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
 
    messages.append({"role": "user", "content": task_prompt})
 
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.1
    )
 
    return response.choices[0].message.content