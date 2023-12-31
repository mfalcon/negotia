import requests
import os
from openai import OpenAI


class LLM(): #TODO: add absract method
    def run():
        pass


class LLMSelector():
    def __init__(self, model_name):
        if 'gpt' in model_name:
            self.llm_instance = OpenAIRepository(model_name)
        else:
            self.llm_instance = OllamaRepository(model_name)


class OpenAIRepository(LLM):
    def __init__(self, model_name):
        self.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        self.model_name = model_name

    def run(self, prompt):

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                }
            ],
            model = self.model_name,
        )

        return response.choices[0].message.content


class OllamaRepository(LLM):
    def __init__(self, model_name):
        self.url = 'http://localhost:11434/api/generate'
        self.model_name = model_name

    def run(self, prompt):
        data = {
            'model': self.model_name, 
            'prompt': prompt, 
            'stream': False,
            'options': {
                'temperature': 0
            }
        }

        response = requests.post(self.url, json=data)

        return response.json()['response']