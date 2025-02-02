import pytest
from unittest.mock import patch, MagicMock
from main import OllamaRepository, OpenAIRepository
import openai

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

@patch('openai.OpenAI')
def test_openai_init_without_api_key(mock_openai):
    # Mock OpenAI to not raise its own error
    mock_openai.side_effect = None
    
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ValueError, match="OpenAI API key must be provided"):
            OpenAIRepository("test-model")

@patch('openai.OpenAI')
def test_openai_run_success(mock_openai_class):
    # Setup mock response
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "test response"
    
    # Setup mock client
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion
    mock_openai_class.return_value = mock_client
    
    # Create repository and test
    repository = OpenAIRepository("test-model", "test-key")
    result = repository.run("test prompt")
    
    assert result == "test response"
    mock_client.chat.completions.create.assert_called_once() 