# negotia

AI-powered negotiation system supporting multiple language model providers.

## Supported AI Providers

This system supports multiple AI model providers for running negotiations:

- **OpenAI**: GPT models (gpt-4, gpt-4o-mini, gpt-3.5-turbo, etc.)
- **Anthropic**: Claude models (claude-3-5-sonnet-20241022, claude-3-haiku-20240307, etc.)
- **Google**: Gemini models (gemini-1.5-pro, gemini-1.5-flash, etc.)
- **Ollama**: Local models (llama3, phi4, mistral, etc.)

## Setup

### 1. Install Dependencies

```bash
poetry install
```

### 2. Configure API Keys

Set the appropriate environment variables for the AI providers you want to use:

```bash
# For OpenAI models
export OPENAI_API_KEY='your-openai-api-key'

# For Anthropic Claude models
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# For Google Gemini models
export GOOGLE_API_KEY='your-google-api-key'

# Ollama requires no API key - just install and run Ollama locally
```

### 3. Run Negotiations

```bash
# Run with default config (uses multiple providers)
poetry run python main.py

# Run swarm system with custom config
poetry run python -m swarm.main --config your-config.yaml
```

## Configuration

Configure your agents in the YAML config file to use different model providers:

```yaml
agents:
  sellers:
    seller1:
      prompt: prompts/seller_prompt.j2
      model: claude-3-5-sonnet-20241022    # Anthropic model
      repo: anthropic                      # Provider type
      urgency: 0.9
      term_weights: {price: 0.6, delivery_days: 0.2, upfront_pct: 0.2}

  buyers:
    buyer1:
      prompt: prompts/buyer_prompt.j2
      model: gpt-4o-mini                   # OpenAI model
      repo: openai                         # Provider type
      urgency: 0.6
      term_weights: {price: 0.7, delivery_days: 0.2, upfront_pct: 0.1}

    buyer2:
      prompt: prompts/buyer_prompt.j2
      model: gemini-1.5-flash              # Google model
      repo: google                         # Provider type
      urgency: 0.7
      term_weights: {price: 0.65, delivery_days: 0.25, upfront_pct: 0.1}
```

## Model Recommendations

### Performance Tiers

**High Performance (Best reasoning, higher cost):**
- `claude-3-5-sonnet-20241022` (Anthropic)
- `gpt-4` (OpenAI)
- `gemini-1.5-pro` (Google)

**Balanced (Good performance, moderate cost):**
- `gpt-4o-mini` (OpenAI)
- `claude-3-haiku-20240307` (Anthropic)
- `gemini-1.5-flash` (Google)

**Local/Free:**
- `llama3` (Ollama)
- `phi4` (Ollama)
- `mistral` (Ollama)

### Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Google**: https://makersuite.google.com/app/apikey
- **Ollama**: Install from https://ollama.ai/
