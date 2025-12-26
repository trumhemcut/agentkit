# Azure OpenAI Integration - Installation Guide

## Quick Start

### Step 1: Install Dependencies

```bash
cd backend
source .venv/bin/activate  # On Linux/Mac
# or .venv\Scripts\activate on Windows

pip install -r requirements.txt
```

This will install:
- `langchain-openai>=0.2.0`
- `openai>=1.0.0`
- `azure-identity>=1.15.0`

### Step 2: Configure Environment Variables

Create or update your `.env` file in `backend/` directory:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Step 3: Get Azure Credentials

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Go to **Keys and Endpoint**
4. Copy:
   - **KEY 1** or **KEY 2** → `AZURE_OPENAI_API_KEY`
   - **Endpoint** → `AZURE_OPENAI_ENDPOINT`
5. Go to **Model deployments**
6. Note your deployment name → `AZURE_OPENAI_DEPLOYMENT`

### Step 4: Start Backend

```bash
cd backend
python main.py
```

### Step 5: Verify Installation

Test Azure OpenAI is working:

```bash
# List Azure OpenAI models
curl http://localhost:8000/models/azure-openai

# Test chat with Azure OpenAI
curl -X POST http://localhost:8000/chat/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from Azure OpenAI!",
    "provider": "azure-openai",
    "model": "gpt-4"
  }'
```

## Troubleshooting

### Import Error: "langchain_openai" could not be resolved

**Solution**: Install dependencies
```bash
pip install langchain-openai openai azure-identity
```

### "AZURE_OPENAI_ENDPOINT is not configured"

**Solution**: Add endpoint to `.env` file
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### "AZURE_OPENAI_API_KEY is not configured"

**Solution**: Add API key to `.env` file
```bash
AZURE_OPENAI_API_KEY=your_key_here
```

### "Deployment not found"

**Solution**: 
1. Check deployment name in Azure Portal
2. Update `.env` file with correct deployment name
3. Restart backend

## Optional: Set as Default Provider

To make Azure OpenAI the default provider, add to `.env`:

```bash
DEFAULT_PROVIDER=azure-openai
DEFAULT_MODEL=gpt-4
```

## Frontend Usage

Once backend is configured:

1. Open frontend app
2. Click provider selector
3. Choose "Azure OpenAI"
4. Select a model
5. Start chatting!

## Testing

Run the test suite:

```bash
cd backend
pytest tests/test_azure_openai_integration.py -v
```

## Documentation

- [Azure OpenAI Integration README](../../backend/AZURE_OPENAI_INTEGRATION_README.md)
- [Provider Documentation](../../.docs/2-knowledge-base/backend/llm/providers.md)
- [Implementation Summary](013-azure-openai-support-summary.md)
