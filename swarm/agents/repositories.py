from abc import ABC, abstractmethod
import requests, openai, os

class AIRepository(ABC):
    @abstractmethod
    def run(self, prompt: str) -> str: ...

class OpenAIRepository(AIRepository):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)

    def run(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0)
        return resp.choices[0].message.content.strip()

class OllamaRepository(AIRepository):
    def __init__(self, model: str = "llama3"):
        self.model = model
    def run(self, prompt: str) -> str:
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": self.model,
                                "prompt": prompt,
                                "stream": False})
        r.raise_for_status()
        return r.json()["response"].strip()

    ... 