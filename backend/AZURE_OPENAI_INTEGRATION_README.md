# Azure OpenAI Integration Guide

## Overview

AgentKit now supports Azure OpenAI as an LLM provider, enabling you to use GPT-4, GPT-3.5 Turbo, and other OpenAI models hosted on Azure. This integration follows the same provider architecture pattern as Ollama and Gemini.

## Architecture

The Azure OpenAI integration consists of:

```
API Routes (routes.py)
    ↓
ProviderClient (provider_client.py) → Aggregates all providers
    ↓
┌──────────┬──────────┬────────────┐
│ Ollama   │ Gemini   │ Azure      │
│ Client   │ Client   │ OpenAI     │
│          │          │ Client     │
└──────────┴──────────┴────────────┘
    ↓           ↓           ↓
┌──────────┬──────────┬────────────┐
│ Ollama   │ Gemini   │ Azure      │
│ Provider │ Provider │ OpenAI     │
│          │          │ Provider   │
└──────────┴──────────┴────────────┘
```

### Key Components

1. **AzureOpenAIProvider** (`llm/azure_openai_provider.py`)
   - LangChain wrapper for Azure OpenAI
   - Handles model initialization and streaming

2. **AzureOpenAIClient** (`llm/azure_openai_client.py`)
   - Lists available models and deployments
   - Returns pre-configured models from settings

3. **ProviderFactory** (`llm/provider_factory.py`)
   - Factory pattern for creating provider instances
   - Supports "azure-openai" provider type

4. **ProviderClient** (`llm/provider_client.py`)
   - Unified API for listing models across all providers
   - Aggregates Azure OpenAI models with Ollama and Gemini

## Setup Guide

### Prerequisites

1. **Azure Subscription**: Active Azure subscription
2. **Azure OpenAI Resource**: Created Azure OpenAI resource
3. **Model Deployment**: At least one model deployed (e.g., GPT-4)

### Step 1: Create Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new Azure OpenAI resource
3. Note your endpoint URL (e.g., `https://your-resource.openai.azure.com/`)

### Step 2: Deploy a Model

1. In your Azure OpenAI resource, go to **Model deployments**
2. Click **Create new deployment**
3. Select a model (e.g., `gpt-4`, `gpt-35-turbo`)
4. Give it a deployment name (e.g., `gpt-4-deployment`)
5. Complete the deployment

### Step 3: Get API Credentials

1. In your Azure OpenAI resource, go to **Keys and Endpoint**
2. Copy **KEY 1** or **KEY 2**
3. Copy the **Endpoint** URL

### Step 4: Configure Environment Variables

Create or update your `.env` file in the `backend/` directory:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-deployment
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional: Set as default provider
DEFAULT_PROVIDER=azure-openai
DEFAULT_MODEL=gpt-4
```

### Step 5: Install Dependencies

```bash
cd backend
source .venv/bin/activate  # On Linux/Mac
# or .venv\Scripts\activate on Windows

pip install -r requirements.txt
```

### Step 6: Restart Backend Server

```bash
cd backend
python main.py
```

## Configuration Options

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `abc123...` |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `https://my-resource.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT` | Deployment name in Azure | `gpt-4-deployment` |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `AZURE_OPENAI_MODEL` | Model name | `gpt-4` |
| `AZURE_OPENAI_API_VERSION` | API version | `2024-02-15-preview` |
| `DEFAULT_PROVIDER` | Default provider to use | `ollama` |
| `DEFAULT_MODEL` | Default model to use | `qwen:7b` |

## Understanding Azure OpenAI Deployments

### Deployments vs Models

Azure OpenAI uses **deployments** rather than direct model access:

- **Model**: The underlying AI model (e.g., `gpt-4`, `gpt-35-turbo`)
- **Deployment**: Your named instance of a model in Azure

**Example**:
- Model: `gpt-4`
- Deployment: `my-gpt4-deployment` (your custom name)

When using AgentKit with Azure OpenAI:
- You can specify either the deployment name or model name
- The deployment name takes precedence if configured
- Common model names are available in the UI for convenience

## API Endpoints

### List All Models

```bash
GET /models
```

Returns all providers and models:

```json
{
  "providers": [
    {"id": "ollama", "name": "Ollama", "available": true},
    {"id": "gemini", "name": "Gemini", "available": true},
    {"id": "azure-openai", "name": "Azure OpenAI", "available": true}
  ],
  "models": [
    {
      "id": "gpt-4-deployment",
      "name": "GPT-4 (Deployment)",
      "size": "Azure Cloud",
      "available": true,
      "provider": "azure-openai",
      "is_deployment": true
    },
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "size": "Azure Cloud",
      "available": true,
      "provider": "azure-openai",
      "is_deployment": false
    }
  ],
  "default_provider": "ollama",
  "default_model": "qwen:7b"
}
```

### List Azure OpenAI Models Only

```bash
GET /models/azure-openai
```

Returns only Azure OpenAI models.

### Chat with Azure OpenAI

```bash
POST /chat/chat
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "provider": "azure-openai",
  "model": "gpt-4"
}
```

## Available Models

AgentKit supports these common Azure OpenAI models:

| Model ID | Name | Description |
|----------|------|-------------|
| `gpt-4` | GPT-4 | Most capable GPT-4 model |
| `gpt-4-turbo` | GPT-4 Turbo | Faster GPT-4 with 128k context |
| `gpt-4o` | GPT-4o | Latest multimodal GPT-4 model |
| `gpt-35-turbo` | GPT-3.5 Turbo | Fast and efficient model |
| `gpt-4-32k` | GPT-4 32K | GPT-4 with extended context |

**Note**: Model availability depends on your Azure region and subscription.

## Frontend Integration

The frontend automatically supports Azure OpenAI through the existing provider/model selection UI.

### Provider Selector

The provider selector will show "Azure OpenAI" when configured:

```typescript
// components/ProviderSelector.tsx
const providerIcons = {
  ollama: Server,
  gemini: Cloud,
  'azure-openai': Cloud,
};
```

### Model Selector

The model selector will list Azure OpenAI models and deployments.

### Usage

1. Start the backend and frontend
2. Open the chat interface
3. Click the provider selector
4. Choose "Azure OpenAI"
5. Select a model from the dropdown
6. Start chatting!

## Error Handling

### Missing Credentials

If Azure OpenAI credentials are not configured:

```json
{
  "providers": [
    {"id": "azure-openai", "name": "Azure OpenAI", "available": false}
  ],
  "errors": [
    {
      "provider": "azure-openai",
      "error": "AZURE_OPENAI_ENDPOINT is not configured"
    }
  ]
}
```

### Invalid Endpoint

If the endpoint is incorrect:

```json
{
  "errors": [
    {
      "provider": "azure-openai",
      "error": "Connection error: Invalid endpoint URL"
    }
  ]
}
```

### Deployment Not Found

If the deployment doesn't exist:

```python
# Error from Azure OpenAI API
ValueError: Deployment 'invalid-deployment' not found
```

## Testing

### Test Configuration

```bash
# Test if Azure OpenAI is properly configured
curl http://localhost:8000/models/azure-openai
```

### Test Chat

```bash
curl -X POST http://localhost:8000/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "provider": "azure-openai",
    "model": "gpt-4"
  }'
```

### Unit Tests

Run the test suite:

```bash
cd backend
pytest tests/test_azure_openai_*.py
```

## Troubleshooting

### Issue: "AZURE_OPENAI_ENDPOINT is not configured"

**Solution**: Add `AZURE_OPENAI_ENDPOINT` to your `.env` file.

### Issue: "AZURE_OPENAI_API_KEY is not configured"

**Solution**: Add `AZURE_OPENAI_API_KEY` to your `.env` file.

### Issue: "Deployment not found"

**Solution**: 
1. Check your deployment name in Azure Portal
2. Update `AZURE_OPENAI_DEPLOYMENT` in `.env`
3. Restart the backend

### Issue: "Invalid API version"

**Solution**: Update `AZURE_OPENAI_API_VERSION` to a supported version (e.g., `2024-02-15-preview`).

### Issue: "Authentication failed"

**Solution**:
1. Verify your API key is correct
2. Check if the key is active in Azure Portal
3. Ensure you're using KEY 1 or KEY 2 (not both)

## Migration Guide

### From OpenAI to Azure OpenAI

If you're migrating from direct OpenAI API:

1. Deploy your models in Azure OpenAI
2. Update environment variables:
   ```bash
   # Remove (if using OpenAI)
   OPENAI_API_KEY=...
   
   # Add
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_DEPLOYMENT=...
   ```
3. Change provider in UI or set `DEFAULT_PROVIDER=azure-openai`

### From Ollama/Gemini to Azure OpenAI

No migration needed! Azure OpenAI works alongside other providers:

1. Add Azure OpenAI configuration to `.env`
2. Keep existing Ollama/Gemini settings
3. Switch providers in the UI as needed

## Best Practices

1. **Use Deployments**: Always create named deployments for production
2. **API Version**: Use stable API versions (avoid preview for production)
3. **Rate Limits**: Monitor Azure OpenAI rate limits in Azure Portal
4. **Cost Control**: Set up cost alerts in Azure
5. **Security**: Store API keys securely, never commit to version control
6. **Regions**: Deploy in regions close to your users for lower latency

## Cost Considerations

Azure OpenAI pricing varies by:
- Model type (GPT-4 is more expensive than GPT-3.5)
- Token usage (input + output tokens)
- Region

**Estimate costs**: Use [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/)

## Resources

- [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [LangChain Azure OpenAI](https://python.langchain.com/docs/integrations/chat/azure_chat_openai)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Azure Portal](https://portal.azure.com)

## Support

For issues or questions:

1. Check this documentation
2. Review Azure OpenAI documentation
3. Check logs: `backend/logs/`
4. Open an issue on GitHub

## License

This integration is part of AgentKit and follows the same license.
