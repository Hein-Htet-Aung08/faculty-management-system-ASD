import os

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "qwen2.5:0.5b"
DEFAULT_REVIEW_MODEL = "llama3.1:8b"


class AIRunner:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL)
        self.implementation_model = os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.review_model = os.getenv("OLLAMA_REVIEW_MODEL", DEFAULT_REVIEW_MODEL)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(base_url=self.base_url, api_key="ollama")
        return self._client

    def model_for(self, review):
        return self.review_model if review else self.implementation_model

    def call(self, system_prompt, user_prompt, review=False):
        model = self.model_for(review)
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=400,
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                return "", f"empty response from model {model!r}"
            return content, None
        except Exception as exc:
            return "", f"{type(exc).__name__}: {exc}"
