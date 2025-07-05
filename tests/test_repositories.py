import pytest
from unittest.mock import patch, MagicMock
from main import OllamaRepository, OpenAIRepository
from swarm.agents.repositories import AnthropicRepository, GoogleRepository
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

def test_anthropic_import_error():
    # Test when anthropic library is not installed
    with patch('builtins.__import__') as mock_import:
        def side_effect(name, *args, **kwargs):
            if name == 'anthropic':
                raise ImportError("No module named 'anthropic'")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = side_effect
        
        with pytest.raises(ImportError, match="anthropic library is required"):
            AnthropicRepository("claude-3-sonnet-20240229", "test-key")

def test_google_import_error():
    # Test when google-generativeai library is not installed
    with patch('builtins.__import__') as mock_import:
        def side_effect(name, *args, **kwargs):
            if name == 'google.generativeai':
                raise ImportError("No module named 'google.generativeai'")
            return __import__(name, *args, **kwargs)
        mock_import.side_effect = side_effect
        
        with pytest.raises(ImportError, match="google-generativeai library is required"):
            GoogleRepository("gemini-1.5-pro", "test-key")

def test_anthropic_initialization():
    # Test that we can at least instantiate the class if anthropic is available
    # This will be skipped if anthropic is not installed
    try:
        import anthropic
        # If anthropic is available, test basic initialization
        repo = AnthropicRepository("claude-3-sonnet-20240229", "test-key")
        assert repo.model == "claude-3-sonnet-20240229"
        assert repo.client is not None
    except ImportError:
        pytest.skip("anthropic library not installed")

def test_google_initialization():
    # Test that we can at least instantiate the class if google-generativeai is available
    # This will be skipped if google-generativeai is not installed
    try:
        import google.generativeai as genai
        # If google-generativeai is available, test basic initialization
        repo = GoogleRepository("gemini-1.5-pro", "test-key")
        assert repo.model == "gemini-1.5-pro"
        assert repo.client is not None
    except ImportError:
        pytest.skip("google-generativeai library not installed") 