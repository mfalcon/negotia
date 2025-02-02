import unittest
from unittest.mock import patch, MagicMock
from main import AIRepository, OllamaRepository, OpenAIRepository

class TestOllamaRepository(unittest.TestCase):
    def setUp(self):
        self.repository = OllamaRepository("test-model")

    @patch('requests.post')
    def test_run_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test response"}
        mock_post.return_value = mock_response

        # Test the run method
        result = self.repository.run("test prompt")
        
        # Verify the result
        self.assertEqual(result, "test response")
        
        # Verify the API was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args['json']['model'], "test-model")
        self.assertEqual(call_args['json']['prompt'], "test prompt")

    @patch('requests.post')
    def test_run_error(self, mock_post):
        # Setup mock to raise an exception
        mock_post.side_effect = Exception("API Error")

        # Test the run method with error
        with self.assertRaises(Exception):
            self.repository.run("test prompt")

class TestOpenAIRepository(unittest.TestCase):
    def setUp(self):
        self.api_key = "test-key"
        self.repository = OpenAIRepository("test-model", self.api_key)

    def test_init_without_api_key(self):
        # Test initialization without API key
        with patch.dict('os.environ', clear=True):
            with self.assertRaises(ValueError):
                OpenAIRepository("test-model")

    @patch('openai.OpenAI')
    def test_run_success(self, mock_openai):
        # Setup mock response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_completion

        # Test the run method
        result = self.repository.run("test prompt")
        
        # Verify the result
        self.assertEqual(result, "test response")
        
        # Verify the API was called correctly
        mock_client.chat.completions.create.assert_called_once() 