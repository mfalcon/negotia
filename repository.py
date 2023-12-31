import requests

class LLM(): #TODO: abm
    def run():
        pass

class OpenAIRepository(LLM):
    def __init__():
        pass

    def run():
        pass

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
    
def get_llm_instance(model_name):
    llm_instance = OllamaRepository(model_name = model_name)
    return llm_instance