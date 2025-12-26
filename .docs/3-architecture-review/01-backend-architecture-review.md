# Backend Architecture Review

**Review Date:** December 26, 2025  
**Reviewer:** Backend Reviewer Agent (Principal Engineer Role)  
**Stack:** Python, FastAPI, LangGraph, AG-UI Protocol, Ollama

---

## 1. Architecture Summary (Inferred)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ENTRY POINTS                               │
│  main.py → FastAPI App with CORS Middleware                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                           API LAYER                                  │
│  api/routes.py  →  /api/chat/{agent_id} (unified SSE streaming)    │
│  api/models.py  →  Pydantic request/response models                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        AGENT LAYER                                   │
│  agents/base_agent.py      → Abstract BaseAgent class               │
│  agents/chat_agent.py      → ChatAgent (text conversations)         │
│  agents/canvas_agent.py    → CanvasAgent (artifact generation)      │
│  agents/agent_registry.py  → Global agent registry singleton        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       GRAPHS LAYER                                   │
│  graphs/chat_graph.py      → LangGraph workflow for chat            │
│  graphs/canvas_graph.py    → LangGraph workflow for canvas          │
│  (Note: Graphs are NOT used for streaming - agents are called       │
│   directly from routes)                                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        LLM LAYER                                     │
│  llm/provider_factory.py   → Factory for LLM providers              │
│  llm/ollama_provider.py    → Ollama implementation (LangChain)      │
│  llm/ollama_client.py      → Direct Ollama API client (model list)  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                              │
│  cache/artifact_cache.py   → In-memory TTL cache for artifacts      │
│  protocols/event_types.py  → AG-UI event type definitions           │
│  protocols/event_encoder.py→ Re-export AG-UI encoder                │
│  config.py                 → Pydantic Settings                       │
│  observability/            → EMPTY (no implementation)               │
└─────────────────────────────────────────────────────────────────────┘
```

### Current State

| Aspect | Status | Notes |
|--------|--------|-------|
| API Design | ⚠️ Mixed | Unified endpoint exists with deprecated legacy routes |
| Agent Abstraction | ✅ Good | Clear base class with async generator pattern |
| LangGraph Integration | ⚠️ Partial | Graphs defined but bypassed for streaming |
| LLM Providers | ⚠️ Limited | Only Ollama; no fallback, no retry logic |
| Observability | ❌ Missing | Empty module; no tracing/metrics |
| Caching | ⚠️ Basic | In-memory only; no persistence |
| Security | ⚠️ Gaps | No auth, broad CORS, no input sanitization |
| Testing | ⚠️ Limited | Manual test scripts, no pytest fixtures |

---

## 2. Top 10 Findings (Ranked)

### Finding 1: **No Observability / Tracing Implementation**
**Severity:** Critical  
**Impact:** Cannot debug production issues, no visibility into agent behavior, impossible to optimize LLM costs

**Evidence:**
```python
# backend/observability/__init__.py
# Observability and logging (optional)
```
Empty module with only a comment.

**Recommendation:**
1. Integrate Langfuse for full trace coverage
2. Add correlation IDs (request_id, user_id, session_id) propagated through entire request lifecycle
3. Trace every LLM call, tool invocation, and agent state transition

**Better Pattern:**
```python
# observability/tracing.py
from langfuse import Langfuse
from functools import wraps
import uuid

langfuse = Langfuse()

def trace_agent_run(func):
    @wraps(func)
    async def wrapper(self, state, *args, **kwargs):
        trace = langfuse.trace(
            name=f"{self.__class__.__name__}.run",
            id=state.get("run_id", str(uuid.uuid4())),
            metadata={
                "thread_id": state.get("thread_id"),
                "model": getattr(self, 'llm', {}).model if hasattr(self, 'llm') else None
            }
        )
        try:
            async for event in func(self, state, *args, **kwargs):
                yield event
        finally:
            trace.update(status="success")
    return wrapper
```

---

### Finding 2: **No Authentication or Authorization**
**Severity:** Critical  
**Impact:** Any client can access all endpoints, no user isolation, no rate limiting

**Evidence:**
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
No auth middleware, no API key validation, wide-open CORS.

**Recommendation:**
1. Add API key authentication middleware
2. Implement user/session context injection
3. Add rate limiting per user/API key
4. Restrict CORS origins in production

**Better Pattern:**
```python
# api/dependencies.py
from fastapi import Depends, HTTPException, Header
from typing import Optional

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key or not is_valid_key(x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return get_user_context(x_api_key)

# In routes.py
@router.post("/chat/{agent_id}")
async def chat_endpoint(
    agent_id: str, 
    input_data: RunAgentInput, 
    user: UserContext = Depends(verify_api_key)
):
    ...
```

---

### Finding 3: **LangGraph Workflows Are Not Used for Streaming**
**Severity:** High  
**Impact:** LangGraph is defined but bypassed; code duplication; inconsistent execution paths

**Evidence:**
```python
# backend/api/routes.py lines 107-133
if agent_id == "chat":
    from agents.chat_agent import ChatAgent
    chat_agent = ChatAgent(model=input_data.model)
    async for event in chat_agent.run(state):
        yield encoder.encode(event)
```
Agents are instantiated directly in routes, bypassing `create_chat_graph()` and `create_canvas_graph()`.

```python
# backend/graphs/chat_graph.py
def create_chat_graph(model: str = None):
    # This is never called from routes
```

**Recommendation:**
1. Either use LangGraph properly with streaming callbacks
2. Or remove the graphs entirely and simplify architecture
3. Don't maintain two execution paths

**Better Pattern (Option A - Use LangGraph):**
```python
# Route events through LangGraph with streaming callback
async def chat_endpoint(...):
    graph = create_chat_graph(model=input_data.model)
    
    async def event_callback(event):
        yield encoder.encode(event)
    
    config = {"configurable": {"event_callback": event_callback}}
    await graph.ainvoke(state, config)
```

---

### Finding 4: **In-Memory Cache Without Persistence or Distribution**
**Severity:** High  
**Impact:** Data loss on restart, won't scale to multiple instances, no cache invalidation strategy

**Evidence:**
```python
# backend/cache/artifact_cache.py
class ArtifactCache:
    def __init__(self, ttl_hours: int = 24):
        self._cache: Dict[str, CachedArtifact] = {}
```
Simple dict-based cache with TTL.

**Recommendation:**
1. Use Redis for distributed caching
2. Add persistence option for artifacts
3. Implement proper cache eviction policies
4. Consider artifact versioning

**Better Pattern:**
```python
# cache/artifact_cache.py
from redis import asyncio as aioredis
import json

class ArtifactCache:
    def __init__(self, redis_url: str = None, ttl_hours: int = 24):
        self._redis = aioredis.from_url(redis_url or settings.REDIS_URL)
        self._ttl = ttl_hours * 3600
    
    async def store(self, artifact: Artifact, thread_id: str, artifact_id: str = None) -> str:
        artifact_id = artifact_id or str(uuid.uuid4())
        key = f"artifact:{artifact_id}"
        await self._redis.setex(key, self._ttl, json.dumps(artifact))
        return artifact_id
```

---

### Finding 5: **No LLM Provider Fallback or Retry Logic**
**Severity:** High  
**Impact:** Single point of failure; no resilience when Ollama is down

**Evidence:**
```python
# backend/llm/ollama_provider.py
class OllamaProvider:
    def __init__(self, model: str = None):
        self.model = ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model or settings.OLLAMA_MODEL,
            streaming=True
        )
```
No timeout configuration, no retry logic, no fallback providers.

**Recommendation:**
1. Add timeout and retry configuration
2. Implement circuit breaker pattern
3. Support multiple provider fallbacks
4. Add model validation before use

**Better Pattern:**
```python
# llm/ollama_provider.py
from tenacity import retry, stop_after_attempt, wait_exponential
from langchain_ollama import ChatOllama

class OllamaProvider:
    def __init__(self, model: str = None, timeout: int = 60, max_retries: int = 3):
        self._timeout = timeout
        self._max_retries = max_retries
        self._model_name = model or settings.OLLAMA_MODEL
        self._client = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _get_client(self):
        if not self._client:
            self._client = ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=self._model_name,
                streaming=True,
                timeout=self._timeout
            )
        return self._client
```

---

### Finding 6: **Deprecated Endpoints Still Active**
**Severity:** Medium  
**Impact:** API surface confusion; maintenance burden; potential security exposure

**Evidence:**
```python
# backend/api/routes.py
@router.post("/chat")
async def chat_endpoint_legacy(input_data: RunAgentInput, request: Request):
    """
    DEPRECATED: Legacy chat endpoint without agent_id in path.
    ...
    """
    logger.warning("DEPRECATED: /chat endpoint called.")

@router.post("/canvas/stream")
async def canvas_stream_endpoint(input_data: CanvasMessageRequest, request: Request):
    """
    DEPRECATED: Canvas agent endpoint...
    """
```
Two deprecated endpoints still fully functional with ~200 lines of code.

**Recommendation:**
1. Add deprecation timeline to API responses
2. Return deprecation warning headers
3. Plan removal with version bump
4. Document migration path for clients

**Better Pattern:**
```python
@router.post("/chat", deprecated=True)
async def chat_endpoint_legacy(...):
    response = await chat_endpoint("chat", input_data, request)
    # Add deprecation header
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2025-03-01"
    return response
```

---

### Finding 7: **Inline Imports in Request Handlers**
**Severity:** Medium  
**Impact:** Potential circular imports; harder to test; performance overhead per request

**Evidence:**
```python
# backend/api/routes.py lines 107-109
if agent_id == "chat":
    from agents.chat_agent import ChatAgent  # Inline import
    chat_agent = ChatAgent(model=input_data.model)
```
Agents are imported inside the request handler function.

**Recommendation:**
1. Move imports to module level
2. Use dependency injection for agent instances
3. Consider agent pooling for performance

**Better Pattern:**
```python
# At module level
from agents.chat_agent import ChatAgent
from agents.canvas_agent import CanvasAgent

# Using factory pattern
AGENT_CLASSES = {
    "chat": ChatAgent,
    "canvas": CanvasAgent
}

@router.post("/chat/{agent_id}")
async def chat_endpoint(agent_id: str, input_data: RunAgentInput, ...):
    agent_class = AGENT_CLASSES.get(agent_id)
    if not agent_class:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent = agent_class(model=input_data.model)
```

---

### Finding 8: **No Input Validation for Prompt Injection**
**Severity:** Medium  
**Impact:** Potential prompt injection attacks; LLM manipulation

**Evidence:**
```python
# backend/agents/canvas_agent.py
async def _create_artifact(self, state: CanvasGraphState):
    messages = state["messages"]
    last_message = messages[-1]["content"]  # Direct use
    
    llm_messages = [
        {"role": "system", "content": system_prompt},
        *messages  # User messages passed directly
    ]
```
User input is passed directly to LLM without sanitization.

**Recommendation:**
1. Add input sanitization layer
2. Implement content policy checking
3. Add output filtering for sensitive data
4. Log and monitor suspicious inputs

**Better Pattern:**
```python
# utils/sanitization.py
import re

def sanitize_user_input(content: str) -> str:
    """Remove potentially dangerous patterns from user input"""
    # Remove system prompt injection attempts
    patterns = [
        r"ignore previous instructions",
        r"disregard all prior",
        r"you are now",
    ]
    for pattern in patterns:
        content = re.sub(pattern, "[FILTERED]", content, flags=re.IGNORECASE)
    return content

# In agent
messages = [sanitize_user_input(msg["content"]) for msg in state["messages"]]
```

---

### Finding 9: **Missing Request ID Propagation**
**Severity:** Medium  
**Impact:** Cannot correlate logs across services; debugging is difficult

**Evidence:**
```python
# backend/api/routes.py
async def chat_endpoint(agent_id: str, input_data: RunAgentInput, request: Request):
    # No request_id extraction or generation
    # No logging with request context
```
No request ID middleware or context propagation.

**Recommendation:**
1. Add request ID middleware
2. Propagate through all layers
3. Include in all log messages
4. Return in response headers

**Better Pattern:**
```python
# middleware/request_id.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import contextvars

request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

---

### Finding 10: **Test Files Are Manual Scripts, Not Proper Tests**
**Severity:** Medium  
**Impact:** No CI/CD integration; no automated validation; tests can't fail builds

**Evidence:**
```python
# backend/tests/test_agent_registry.py
import sys
sys.path.insert(0, '/home/phihuynh/projects/agenkit/backend')

# Test 1: List all agents
print("Test 1: List all agents")
print("=" * 50)
agents = agent_registry.list_agents()
```
Manual print-based testing with hardcoded paths.

**Recommendation:**
1. Convert to pytest test cases
2. Add fixtures for common setup
3. Use proper assertions
4. Add test coverage reporting

**Better Pattern:**
```python
# tests/test_agent_registry.py
import pytest
from agents.agent_registry import AgentRegistry

@pytest.fixture
def registry():
    return AgentRegistry()

def test_list_agents_returns_all_registered(registry):
    agents = registry.list_agents(available_only=False)
    assert len(agents) >= 2
    agent_ids = [a.id for a in agents]
    assert "chat" in agent_ids
    assert "canvas" in agent_ids

def test_get_agent_returns_metadata(registry):
    agent = registry.get_agent("chat")
    assert agent is not None
    assert agent.name == "Chat Agent"
    assert agent.available is True
```

---

## 3. Refactor Plan

### Phase 1: Quick Wins (1-3 PRs, 1-2 weeks)

| Task | Effort | Impact | Files |
|------|--------|--------|-------|
| Add request ID middleware | S | High | `middleware/request_id.py`, `main.py` |
| Convert tests to pytest | S | Medium | `tests/*.py` |
| Remove deprecated endpoints | S | Medium | `api/routes.py` |
| Add basic auth middleware | M | Critical | `api/dependencies.py`, `main.py` |
| Move inline imports to module level | S | Low | `api/routes.py` |

### Phase 2: Medium Refactors (2-4 weeks)

| Task | Effort | Impact | Files |
|------|--------|--------|-------|
| Implement Langfuse tracing | M | Critical | `observability/`, agents, routes |
| Add Redis cache support | M | High | `cache/artifact_cache.py` |
| Add LLM retry/fallback logic | M | High | `llm/*.py` |
| Implement input sanitization | M | Medium | `utils/sanitization.py` |
| Resolve LangGraph vs direct agent usage | L | High | `graphs/`, `api/routes.py` |

### Phase 3: Strategic Improvements (1-2 months)

| Task | Effort | Impact | Files |
|------|--------|--------|-------|
| Multi-provider LLM support | L | High | `llm/` module |
| User/tenant isolation | L | Critical | All layers |
| Proper streaming with LangGraph | L | Medium | Architecture redesign |
| Evaluation framework setup | L | High | New `evaluation/` module |
| OpenTelemetry integration | M | High | `observability/` |

---

## 4. Security Audit

### Threat Model Summary

| Asset | Threat Actor | Attack Vector |
|-------|--------------|---------------|
| LLM API | External users | Prompt injection |
| Artifacts | Any client | Unauthorized access |
| Server | Internet | DoS via expensive LLM calls |
| Configuration | Attacker | Secret exposure |

### Identified Vulnerabilities

| ID | Vulnerability | Severity | Status |
|----|--------------|----------|--------|
| SEC-01 | No authentication | Critical | Open |
| SEC-02 | No rate limiting | High | Open |
| SEC-03 | Broad CORS policy | Medium | Open |
| SEC-04 | No input sanitization | Medium | Open |
| SEC-05 | No PII redaction in logs | Medium | Open |
| SEC-06 | Secrets in plain settings | Low | Partial (env vars) |

### Mitigations

1. **SEC-01**: Implement API key authentication immediately
2. **SEC-02**: Add rate limiting middleware (slowapi or custom)
3. **SEC-03**: Restrict CORS to specific domains in production
4. **SEC-04**: Add input sanitization layer before LLM calls
5. **SEC-05**: Implement log scrubbing for PII patterns
6. **SEC-06**: Use secrets manager for production

### Security Checklist

- [ ] API authentication implemented
- [ ] Rate limiting per user/IP
- [ ] CORS restricted to known origins
- [ ] Input validation on all endpoints
- [ ] Prompt injection defenses
- [ ] PII redaction in logs
- [ ] Secrets in environment variables
- [ ] HTTPS enforced
- [ ] Security headers (HSTS, CSP, etc.)
- [ ] Audit logging for sensitive operations

---

## 5. Performance & Cost Audit

### Bottlenecks

| Location | Issue | Impact |
|----------|-------|--------|
| Agent instantiation | New agent per request | Memory churn |
| No connection pooling | New HTTP client per Ollama call | Connection overhead |
| No response caching | Identical prompts re-processed | Wasted LLM tokens |
| Sync cleanup in cache | Blocking TTL cleanup | Request latency spikes |

### Token Optimization

```python
# Current: No token tracking
async for chunk in self.llm.astream(messages):
    content = chunk.content

# Better: Track and limit tokens
token_count = 0
MAX_TOKENS = 4096

async for chunk in self.llm.astream(messages):
    content = chunk.content
    token_count += estimate_tokens(content)
    if token_count > MAX_TOKENS:
        logger.warning(f"Token limit reached: {token_count}")
        break
```

### Caching & Rate Limiting Recommendations

1. **Add semantic caching** for similar prompts (using embeddings)
2. **Implement request deduplication** for concurrent identical requests
3. **Add rate limiting** per user: 10 req/min, 100 req/hour
4. **Cache model list** from Ollama (15-minute TTL)

---

## 6. Observability & Langfuse Audit

### Tracing Gaps

| Layer | Current State | Required |
|-------|--------------|----------|
| API routes | ❌ No spans | Request span with metadata |
| Agent execution | ❌ No traces | Agent run trace |
| LLM calls | ❌ No tracking | LLM span with token counts |
| Tool execution | ❌ No visibility | Tool invocation spans |
| Cache operations | ❌ No metrics | Hit/miss tracking |

### Metrics to Add

```python
# Required metrics
- request_count (labels: endpoint, agent_id, status)
- request_duration_seconds (labels: endpoint, agent_id)
- llm_token_count (labels: model, operation)
- llm_call_duration_seconds (labels: model)
- cache_operations (labels: operation, hit_miss)
- agent_errors (labels: agent_id, error_type)
```

### Logging Improvements

```python
# Current logging lacks structure
logger.info(f"Creating new artifact, message length: {len(last_message)}")

# Better: Structured logging with context
logger.info(
    "artifact_creation_started",
    extra={
        "event": "artifact_creation_started",
        "thread_id": thread_id,
        "run_id": run_id,
        "message_length": len(last_message),
        "request_id": request_id_var.get()
    }
)
```

### Evaluation Strategy

1. **Offline Evaluation**: Store all LLM inputs/outputs in Langfuse for later evaluation
2. **Regression Testing**: Create evaluation datasets from production traces
3. **Quality Metrics**: Track response quality scores over time
4. **Cost Analysis**: Monitor token usage and cost per request

---

## 7. Testing & Quality Gates

### Current Test Pyramid

```
          /\
         /!!\     E2E Tests: 0 (none)
        /----\
       /  !!  \   Integration Tests: 0 (none)
      /--------\
     /          \  Unit Tests: ~14 (manual scripts)
    --------------
```

### Recommended Test Pyramid

```
          /\
         /  \     E2E Tests: 5-10 (API flows)
        /----\
       /      \   Integration Tests: 15-20 (agent + LLM mock)
      /--------\
     /          \  Unit Tests: 50+ (pure functions, schema validation)
    --------------
```

### CI/CD Gates

1. **Pre-commit**:
   - Linting (ruff, black)
   - Type checking (mypy)
   - Unit tests

2. **PR Gate**:
   - All unit tests pass
   - Integration tests pass
   - Coverage > 70%
   - Security scan (bandit)

3. **Deploy Gate**:
   - E2E tests pass
   - Performance benchmark within threshold
   - Manual approval for production

### Mocking Strategy

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable responses"""
    mock = AsyncMock()
    mock.astream.return_value = async_generator_mock([
        MockChunk("Hello"),
        MockChunk(" World")
    ])
    return mock

@pytest.fixture
def chat_agent(mock_llm):
    agent = ChatAgent()
    agent.llm = mock_llm
    return agent
```

---

## 8. Code Examples

### Example 1: Proper Request ID Middleware

```python
# middleware/request_id.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid
import contextvars
import logging

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_ctx.set(request_id)
        
        # Add to logging context
        logging.getLogger().handlers[0].addFilter(
            lambda record: setattr(record, 'request_id', request_id) or True
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# Usage in main.py
app.add_middleware(RequestIdMiddleware)
```

### Example 2: Basic Langfuse Integration

```python
# observability/langfuse_tracer.py
from langfuse import Langfuse
from langfuse.decorators import observe
from functools import wraps
from config import settings

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)

def trace_llm_call(func):
    @wraps(func)
    async def wrapper(self, messages, *args, **kwargs):
        generation = langfuse.generation(
            name="llm_call",
            model=self.llm.model,
            input=messages,
        )
        try:
            result = []
            async for chunk in func(self, messages, *args, **kwargs):
                result.append(chunk.content if hasattr(chunk, 'content') else chunk)
                yield chunk
            generation.end(output="".join(filter(None, result)))
        except Exception as e:
            generation.end(error=str(e))
            raise
    return wrapper
```

### Example 3: Proper pytest Test

```python
# tests/test_chat_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from agents.chat_agent import ChatAgent
from ag_ui.core import EventType

@pytest.fixture
def mock_chunk():
    """Factory for mock LLM chunks"""
    def _create(content: str):
        chunk = MagicMock()
        chunk.content = content
        return chunk
    return _create

@pytest.fixture
async def chat_agent(mock_chunk):
    """ChatAgent with mocked LLM"""
    agent = ChatAgent()
    
    async def mock_stream(messages):
        for text in ["Hello", " ", "World"]:
            yield mock_chunk(text)
    
    agent.llm.astream = mock_stream
    return agent

@pytest.mark.asyncio
async def test_chat_agent_emits_correct_events(chat_agent):
    state = {
        "messages": [{"role": "user", "content": "Hi"}],
        "thread_id": "test-thread",
        "run_id": "test-run"
    }
    
    events = [event async for event in chat_agent.run(state)]
    
    assert events[0].type == EventType.TEXT_MESSAGE_START
    assert events[-1].type == EventType.TEXT_MESSAGE_END
    
    content_events = [e for e in events if e.type == EventType.TEXT_MESSAGE_CONTENT]
    full_content = "".join(e.delta for e in content_events)
    assert full_content == "Hello World"
```

---

## Summary

The backend architecture has a solid foundation with clear separation between API, agents, and LLM layers. However, there are **critical gaps in observability, security, and resilience** that must be addressed before production deployment.

### Priority Actions

1. 🔴 **CRITICAL**: Add authentication and observability (Langfuse)
2. 🟠 **HIGH**: Implement LLM retry logic and cache persistence
3. 🟡 **MEDIUM**: Convert tests to pytest, remove deprecated endpoints
4. 🟢 **LOW**: Refactor LangGraph integration, add semantic caching

The architecture is well-suited for a prototype but requires significant hardening for production use.
