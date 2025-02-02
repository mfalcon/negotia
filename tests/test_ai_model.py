import unittest
from unittest.mock import patch, MagicMock
from main import AIModel

class TestAIModel(unittest.TestCase):
    def test_init_ollama(self):
        model = AIModel(repository_type="ollama", model_name="test-model")
        self.assertEqual(model.repository.model_name, "test-model")

    def test_init_openai(self):
        with patch('openai.OpenAI'):
            model = AIModel(
                repository_type="openai",
                model_name="test-model",
                api_key="test-key"
            )
            self.assertEqual(model.repository.model_name, "test-model")

    def test_init_invalid_repository(self):
        with self.assertRaises(ValueError):
            AIModel(repository_type="invalid")

    def test_generate_text_success(self):
        model = AIModel(repository_type="ollama", model_name="test-model")
        model.repository.run = MagicMock(return_value="test response")
        
        result = model.generate_text("test prompt")
        self.assertEqual(result, "test response")

    def test_generate_text_error(self):
        model = AIModel(repository_type="ollama", model_name="test-model")
        model.repository.run = MagicMock(side_effect=Exception("API Error"))
        
        result = model.generate_text("test prompt")
        self.assertEqual(result, "Error") 