import pytest
from unittest.mock import patch, MagicMock
from main import OllamaRepository, OpenAIRepository

def test_ollama_run_success():
    repository = OllamaRepository("test-model")
    
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test response"}
        mock_post.return_value = mock_response
        
        result = repository.run("test prompt")
        
        assert result == "test response"
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        assert call_args['json']['model'] == "test-model"
        assert call_args['json']['prompt'] == "test prompt"

def test_ollama_run_error():
    repository = OllamaRepository("test-model")
    
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            repository.run("test prompt")

def test_openai_init_without_api_key():
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ValueError):
            OpenAIRepository("test-model")

def test_openai_run_success():
    with patch('openai.OpenAI') as mock_openai:
        repository = OpenAIRepository("test-model", "test-key")
        
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "test response"
        mock_client.chat.completions.create.return_value = mock_completion
        
        result = repository.run("test prompt")
        
        assert result == "test response"
        mock_client.chat.completions.create.assert_called_once() 