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

class AnthropicRepository(AIRepository):
    def __init__(self, model: str, api_key: str):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic library is required. Install with: pip install anthropic")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)

    def run(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()

class GoogleRepository(AIRepository):
    def __init__(self, model: str, api_key: str):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai library is required. Install with: pip install google-generativeai")
        
        self.model = model
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    def run(self, prompt: str) -> str:
        response = self.client.generate_content(
            prompt,
            generation_config={"temperature": 0}
        )
        return response.text.strip()

    ... 