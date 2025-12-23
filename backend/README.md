# AgentKit Backend

## Overview

Backend skeleton for Agentic AI solution using LangGraph and AG-UI protocol.

## Technologies

- **LangGraph**: Multi-agent workflow orchestration
- **AG-UI Protocol**: Real-time agent-frontend communication (official SDK: `ag-ui-protocol`)
- **FastAPI**: HTTP server with streaming endpoints
- **Ollama**: LLM provider with `qwen:7b` model
- **Python**: Backend implementation

## Setup

### Prerequisites

1. Python 3.10 or higher
2. Ollama installed and running

### Installation

1. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Ensure Ollama is running:
   ```bash
   ollama serve
   ollama pull qwen:7b
   ```

### Run Server

```bash
python -m backend.main
```

The server will start at `http://localhost:8000`

## API Endpoints

### POST /api/chat
Chat with agent using AG-UI protocol

**Request Body**:
```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

**Response**: SSE stream with AG-UI events

**Example with curl**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'
```

### GET /health
Health check endpoint

**Response**:
```json
{
  "status": "healthy"
}
```

## Project Structure

```
/backend
  /agents          # Agent implementations
  /api             # API endpoints
  /graphs          # LangGraph workflow definitions
  /llm             # LLM provider integrations
  /protocols       # AG-UI protocol implementation
  main.py          # FastAPI application entry point
  config.py        # Configuration management
  requirements.txt # Python dependencies
```

## AG-UI Protocol

This backend implements the AG-UI protocol for real-time agent-frontend communication:

- **RUN_STARTED**: Emitted when agent run begins
- **TEXT_MESSAGE_START**: Emitted when agent starts generating a message
- **TEXT_MESSAGE_CONTENT**: Emitted for each content chunk (streaming)
- **TEXT_MESSAGE_END**: Emitted when message generation completes
- **RUN_FINISHED**: Emitted when agent run completes successfully
- **RUN_ERROR**: Emitted when an error occurs

## Development

### Adding New Agents

1. Create agent class in `/agents` that inherits from `BaseAgent`
2. Implement the `run()` method with AG-UI event emissions
3. Create corresponding LangGraph workflow in `/graphs`
4. Add route in `/api/routes.py`

### Adding LLM Providers

1. Create provider class in `/llm` that follows the provider interface
2. Add to `LLMProviderFactory` in `/llm/provider_factory.py`
3. Update configuration in `config.py`

## License

MIT
