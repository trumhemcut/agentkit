# Backend Architecture Review - AgentKit

**Review Date:** January 1, 2026  
**Reviewer:** Principal Engineer (Backend Reviewer Mode)  
**Stack:** Python 3.x, FastAPI, LangGraph, AG-UI, Ollama/Gemini/Azure OpenAI  
**Review Scope:** Backend architecture, code quality, security, performance, observability

---

## 1. Architecture Summary

### Inferred Architecture Map

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI Layer                             │
│  main.py, api/routes.py, api/models.py                           │
│  - CORS middleware                                                │
│  - SSE streaming endpoints                                        │
│  - No centralized exception handling                              │
│  - No request ID propagation                                      │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                    Agent Registry Layer                           │
│  agents/agent_registry.py                                         │
│  - 6 registered agents (chat, canvas, a2ui, a2ui-loop,          │
│    insurance-supervisor, salary-viewer)                           │
│  - Static metadata management                                     │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                    Graph Factory Layer                            │
│  graphs/graph_factory.py                                          │
│  - Dynamic graph creation based on agent_id                       │
│  - Static registry of graph creators                              │
│  - Model/provider parameter injection                             │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                    LangGraph Workflows                            │
│  graphs/{chat,canvas,a2ui,insurance_supervisor,etc}_graph.py     │
│  - StateGraph definitions                                         │
│  - Conditional routing                                            │
│  - Async node execution                                           │
│  - Event callback pattern for streaming                           │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                       Agent Layer                                 │
│  agents/{chat,canvas,a2ui,salary_viewer}_agent.py                │
│  - BaseAgent abstract class                                       │
│  - AsyncGenerator-based event streaming                           │
│  - AG-UI/A2UI protocol emission                                   │
│  - Minimal abstraction (BaseAgent is near-empty)                  │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                    LLM Provider Layer                             │
│  llm/{provider_factory,provider_client}.py                        │
│  llm/{ollama,gemini,azure_openai}_provider.py                    │
│  - Factory pattern for provider selection                         │
│  - LangChain integration (ChatOllama, ChatGoogleGenerativeAI)    │
│  - No fallback strategy                                           │
│  - No rate limiting                                               │
└────────────────────┬─────────────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────────────┐
│                    External Services                              │
│  - Ollama (local): http://localhost:11434                        │
│  - Gemini API: via google-generativeai SDK                        │
│  - Azure OpenAI: via langchain-openai SDK                         │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                  Cross-Cutting Concerns                           │
│  - Protocols: AG-UI (event streaming), A2UI (UI components)      │
│  - Caching: artifact_cache (in-memory dict, no TTL, no eviction) │
│  - Logging: Python logging module (no structured logs)           │
│  - Observability: LangFuse integration (mentioned, not visible)  │
│  - Tools: A2UI component generators, search tools                │
└───────────────────────────────────────────────────────────────────┘
```

### Key Design Patterns
1. **Factory Pattern**: GraphFactory, LLMProviderFactory
2. **Registry Pattern**: AgentRegistry (static, metadata-driven)
3. **Strategy Pattern**: Agent implementations with BaseAgent interface
4. **Event Streaming**: AsyncGenerator + callback pattern for SSE
5. **State Machines**: LangGraph StateGraph with conditional routing
6. **Dependency Injection**: model/provider parameters passed at runtime

---

## 2. Top 10 Critical Findings

### 🔴 CRITICAL - Severity 1

#### **1. Missing Correlation IDs and Request Tracing**
**Severity:** CRITICAL | **Impact:** HIGH | **Effort:** MEDIUM

**Evidence:**
```python
# api/routes.py - No request ID generation or propagation
@router.post("/chat/{agent_id}")
async def chat_endpoint(agent_id: str, input_data: RunAgentInput, request: Request):
    # No correlation ID, no trace context
    yield encoder.encode(RunStartedEvent(...))  # Missing correlation metadata
```

**Problem:**  
- Cannot correlate logs, errors, and events across async execution
- Debugging production issues requires manual log correlation
- No way to trace a single request through multiple agents/nodes
- LangFuse traces (if enabled) not linked to API requests

**Recommendation:**  
1. Generate `request_id` at API entry (middleware or route handler)
2. Add to all AG-UI events via metadata field
3. Propagate through LangGraph config: `config["metadata"]["request_id"]`
4. Include in all log statements via contextvars
5. Link to LangFuse trace_id

**Code Example:**
```python
# middleware/correlation.py
from contextvars import ContextVar
import uuid

request_id_ctx: ContextVar[str] = ContextVar('request_id', default=None)

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_id_ctx.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Usage in routes.py
from middleware.correlation import request_id_ctx

yield encoder.encode(RunStartedEvent(
    type=EventType.RUN_STARTED,
    thread_id=input_data.thread_id,
    run_id=input_data.run_id,
    metadata={"request_id": request_id_ctx.get()}
))
```

---

#### **2. Secrets Management - Plain Text API Keys**
**Severity:** CRITICAL | **Impact:** HIGH | **Effort:** LOW

**Evidence:**
```python
# config.py - Secrets loaded directly from environment
class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    # No validation, no encryption, logged in plain text
```

**Problem:**  
- API keys stored in plain text in .env files
- Keys potentially logged during debug sessions
- No rotation mechanism
- No secrets validation at startup
- Risk of exposure in logs, errors, tracebacks

**Recommendation:**  
1. Use Pydantic's `SecretStr` for all sensitive fields
2. Validate secrets at startup (non-empty, format checks)
3. Implement secrets provider pattern (Azure Key Vault, AWS Secrets Manager)
4. Add `repr=False` to sensitive Pydantic fields
5. Redact secrets in error messages and logs

**Migration Steps:**
```python
# config.py
from pydantic import SecretStr, field_validator

class Settings(BaseSettings):
    GEMINI_API_KEY: SecretStr = SecretStr("")
    AZURE_OPENAI_API_KEY: SecretStr = SecretStr("")
    
    @field_validator("GEMINI_API_KEY", "AZURE_OPENAI_API_KEY")
    def validate_api_key(cls, v: SecretStr):
        if v.get_secret_value() == "":
            raise ValueError("API key cannot be empty")
        return v

# Usage
api_key = settings.GEMINI_API_KEY.get_secret_value()
```

---

#### **3. No Centralized Exception Handling**
**Severity:** CRITICAL | **Impact:** HIGH | **Effort:** LOW

**Evidence:**
```python
# api/routes.py - Exception handling duplicated in every endpoint
except Exception as e:
    import traceback
    logger.error(f"Error occurred: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    yield encoder.encode(RunErrorEvent(...))
```

**Problem:**  
- Exception handling logic duplicated across 5+ endpoints
- Inconsistent error responses
- Full tracebacks sent to client (info leakage)
- No structured error logging
- No error classification (retryable vs fatal)

**Recommendation:**  
1. Create FastAPI exception handler for common exceptions
2. Define custom exception hierarchy (RetryableError, ValidationError, etc.)
3. Use dependency injection for error handling
4. Implement error middleware for consistent responses
5. Redact sensitive info in error messages

**Pattern:**
```python
# exceptions/handlers.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

class AgentExecutionError(Exception):
    """Base exception for agent execution errors"""
    pass

class RetryableAgentError(AgentExecutionError):
    """Errors that can be retried"""
    pass

@app.exception_handler(AgentExecutionError)
async def agent_error_handler(request: Request, exc: AgentExecutionError):
    return JSONResponse(
        status_code=500,
        content={
            "error": "agent_execution_failed",
            "message": str(exc),
            "request_id": request_id_ctx.get(),
            "retryable": isinstance(exc, RetryableAgentError)
        }
    )
```

---

### 🟠 HIGH - Severity 2

#### **4. In-Memory Artifact Cache - No Eviction, No TTL**
**Severity:** HIGH | **Impact:** HIGH | **Effort:** MEDIUM

**Evidence:**
```python
# cache/artifact_cache.py
class ArtifactCache:
    def __init__(self):
        self._cache = {}  # No size limit, no TTL, no eviction policy
    
    def set(self, artifact_id: str, artifact: dict, thread_id: str = None):
        self._cache[artifact_id] = artifact  # Unbounded growth
```

**Problem:**  
- Memory leak risk - cache grows indefinitely
- No TTL - stale artifacts never expire
- No eviction policy (LRU, LFU)
- Single-instance cache (not distributed) - won't scale
- Thread-unsafe dictionary operations

**Recommendation:**  
1. Implement TTL-based eviction (e.g., 1 hour default)
2. Add size limits with LRU eviction
3. Use Redis for distributed caching (multi-instance support)
4. Add cache metrics (hit rate, size, evictions)
5. Thread-safe operations (use `threading.Lock` or Redis)

**Refactor:**
```python
# cache/artifact_cache.py
from cachetools import TTLCache
import threading

class ArtifactCache:
    def __init__(self, maxsize=1000, ttl=3600):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()
    
    def set(self, artifact_id: str, artifact: dict, thread_id: str = None):
        with self._lock:
            self._cache[artifact_id] = artifact
    
    def get(self, artifact_id: str) -> Optional[dict]:
        with self._lock:
            return self._cache.get(artifact_id)
```

---

#### **5. BaseAgent Abstraction Provides No Value**
**Severity:** HIGH | **Impact:** MEDIUM | **Effort:** LOW

**Evidence:**
```python
# agents/base_agent.py
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, state: AgentState) -> AsyncGenerator:
        """Execute agent logic and stream events"""
        pass
```

**Problem:**  
- BaseAgent has no shared logic, only abstract method
- No common initialization, error handling, or logging
- Agents implement LLM setup redundantly
- No enforcement of event protocol compliance
- Missed opportunity for cross-cutting concerns

**Recommendation:**  
1. Move common initialization (provider setup) to BaseAgent
2. Add template methods for lifecycle hooks (setup, teardown, error)
3. Implement event validation and protocol enforcement
4. Add logging/metrics instrumentation
5. Create mixins for common capabilities (streaming, tools, etc.)

**Refactor:**
```python
# agents/base_agent.py
class BaseAgent(ABC):
    def __init__(self, model: str = None, provider: str = None):
        self.provider_type = provider or settings.DEFAULT_PROVIDER
        self.model_name = model or settings.DEFAULT_MODEL
        self.llm = self._initialize_llm()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _initialize_llm(self):
        """Common LLM initialization"""
        provider_instance = LLMProviderFactory.get_provider(
            provider_type=self.provider_type,
            model=self.model_name
        )
        return provider_instance.get_model()
    
    @abstractmethod
    async def run(self, state: AgentState) -> AsyncGenerator[BaseEvent, None]:
        pass
    
    async def on_error(self, error: Exception) -> BaseEvent:
        """Default error handling"""
        self.logger.error(f"Agent error: {error}", exc_info=True)
        return RunErrorEvent(message=str(error))
```

---

#### **6. No LLM Rate Limiting or Retry Logic**
**Severity:** HIGH | **Impact:** MEDIUM | **Effort:** MEDIUM

**Evidence:**
```python
# agents/chat_agent.py
async for chunk in self.llm.astream(messages):
    content = chunk.content  # No error handling, no retry, no rate limit
```

**Problem:**  
- No rate limiting for LLM API calls (risk of quota exhaustion)
- No retry logic for transient failures (network errors, 429s)
- No exponential backoff
- No circuit breaker pattern
- Cost monitoring absent

**Recommendation:**  
1. Implement retry decorator with exponential backoff
2. Add rate limiter (token bucket algorithm)
3. Circuit breaker for repeated failures
4. Cost tracking per request
5. Fallback to alternative providers

**Pattern:**
```python
# llm/resilience.py
from tenacity import retry, stop_after_attempt, wait_exponential
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def call_llm_with_retry(llm, messages):
    return await llm.astream(messages)

# Usage in agents
async for chunk in call_llm_with_retry(self.llm, messages):
    ...
```

---

#### **7. TypedDict State Schemas - No Runtime Validation**
**Severity:** HIGH | **Impact:** MEDIUM | **Effort:** LOW

**Evidence:**
```python
# agents/base_agent.py
class AgentState(TypedDict, total=False):
    messages: List[Dict[str, str]]  # No validation, can be malformed
    thread_id: str
    run_id: str
```

**Problem:**  
- TypedDict provides typing hints but no runtime validation
- Malformed state can propagate through graph nodes
- No schema versioning
- No migration path for state changes
- Debugging issues with unexpected state structure

**Recommendation:**  
1. Replace TypedDict with Pydantic BaseModel for runtime validation
2. Add schema versioning
3. Validate state at graph entry points
4. Implement state migration helpers
5. Add unit tests for state validation

**Refactor:**
```python
# agents/base_agent.py
from pydantic import BaseModel, Field, validator

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1)

class AgentState(BaseModel):
    messages: List[Message]
    thread_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    user_action: Optional[Dict[str, Any]] = None
    
    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        return v
```

---

### 🟡 MEDIUM - Severity 3

#### **8. Unstructured Logging**
**Severity:** MEDIUM | **Impact:** MEDIUM | **Effort:** LOW

**Evidence:**
```python
# main.py, various files
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger.info(f"Starting chat agent run")  # No structured fields
```

**Problem:**  
- Plain text logs are hard to query and analyze
- No structured fields (agent_id, model, provider, duration)
- No log aggregation setup
- Difficult to filter/search in production
- No performance metrics in logs

**Recommendation:**  
1. Use structlog or Python's JSON logging
2. Add structured fields: agent_id, model, thread_id, request_id
3. Implement log aggregation (ELK, Datadog, CloudWatch)
4. Add performance metrics (latency, token count)
5. Consistent log levels across modules

**Implementation:**
```python
# logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Usage
logger.info(
    "agent_started",
    agent_id=agent_id,
    model=model,
    provider=provider,
    thread_id=thread_id,
    request_id=request_id_ctx.get()
)
```

---

#### **9. Missing Input Validation at API Layer**
**Severity:** MEDIUM | **Impact:** MEDIUM | **Effort:** LOW

**Evidence:**
```python
# api/models.py
class RunAgentInput(BaseModel):
    messages: List[Message]
    thread_id: str
    run_id: str
    model: Optional[str] = None  # No validation, can be arbitrary string
```

**Problem:**  
- No validation for model names (can be typos or invalid)
- No max message length validation (DoS risk)
- No rate limiting per thread_id
- Provider parameter not validated against available providers

**Recommendation:**  
1. Add Pydantic validators for all input fields
2. Validate model exists before graph execution
3. Implement max message length/count limits
4. Add enum constraints for provider parameter
5. Rate limit by thread_id/IP

**Code:**
```python
# api/models.py
class RunAgentInput(BaseModel):
    messages: List[Message] = Field(..., max_items=100)
    thread_id: str = Field(..., min_length=1, max_length=128)
    run_id: str = Field(..., min_length=1, max_length=128)
    model: Optional[str] = Field(None, max_length=128)
    provider: Optional[Literal["ollama", "gemini", "azure-openai"]] = None
    
    @validator("messages")
    def validate_messages(cls, v):
        total_length = sum(len(m.content) for m in v)
        if total_length > 100000:  # 100KB limit
            raise ValueError("Total message content exceeds 100KB limit")
        return v
```

---

#### **10. No Observability for LangGraph Node Execution**
**Severity:** MEDIUM | **Impact:** MEDIUM | **Effort:** MEDIUM

**Evidence:**
```python
# graphs/canvas_graph.py
async def canvas_agent_node(state: CanvasGraphState, config=None):
    logger.info(f"Canvas agent node executing")  # Only basic logs
    async for event in canvas_agent.run(state):
        if event_callback:
            await event_callback(event)
    logger.info(f"Canvas agent node completed")  # No metrics
```

**Problem:**  
- No metrics for node execution time
- No visibility into conditional routing decisions
- Cannot track which nodes are slow/failing
- No graph execution traces
- Missing LangFuse integration in node wrappers

**Recommendation:**  
1. Instrument all nodes with timing metrics
2. Log routing decisions with context
3. Add span tracing (LangFuse, OpenTelemetry)
4. Create graph execution dashboard
5. Track success/failure rates per node

**Pattern:**
```python
# graphs/observability.py
import time
from functools import wraps

def observe_node(node_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(state, config=None):
            start_time = time.time()
            request_id = request_id_ctx.get()
            
            logger.info("node_started", node=node_name, request_id=request_id)
            
            try:
                result = await func(state, config)
                duration = time.time() - start_time
                
                logger.info(
                    "node_completed",
                    node=node_name,
                    duration_ms=duration * 1000,
                    request_id=request_id
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "node_failed",
                    node=node_name,
                    error=str(e),
                    duration_ms=duration * 1000,
                    request_id=request_id
                )
                raise
        return wrapper
    return decorator

# Usage
@observe_node("canvas_agent")
async def canvas_agent_node(state: CanvasGraphState, config=None):
    ...
```

---

## 3. Refactor Plan

### Phase 1: Quick Wins (1-2 weeks)
**Goal:** Address critical security and operational issues with minimal code changes.

1. **Secrets Management** (2 days)
   - Migrate to Pydantic `SecretStr` for all API keys
   - Add validation at startup
   - Audit logs for secret leakage
   - **Files:** `config.py`, all provider files

2. **Centralized Exception Handling** (2 days)
   - Create exception hierarchy
   - Implement FastAPI exception handlers
   - Add error middleware
   - **Files:** New `exceptions/` module, `api/routes.py`

3. **Input Validation** (1 day)
   - Add Pydantic validators to API models
   - Implement max length/count constraints
   - **Files:** `api/models.py`

4. **Structured Logging** (3 days)
   - Integrate structlog or JSON logging
   - Add structured fields to all log statements
   - **Files:** `main.py`, `logging_config.py`, all modules

5. **Artifact Cache TTL** (1 day)
   - Replace dict with `cachetools.TTLCache`
   - Add thread-safety
   - **Files:** `cache/artifact_cache.py`

**Impact:** Reduces immediate security/operational risks, improves debuggability.

---

### Phase 2: Medium-Term Improvements (3-4 weeks)
**Goal:** Improve architecture quality, performance, and maintainability.

1. **Request Correlation** (1 week)
   - Implement correlation middleware
   - Add request_id to all events and logs
   - Integrate with LangFuse traces
   - **Files:** New `middleware/`, `api/routes.py`, all agents

2. **LLM Resilience** (1 week)
   - Implement retry decorator with exponential backoff
   - Add circuit breaker pattern
   - Cost tracking
   - **Files:** New `llm/resilience.py`, all agents

3. **State Validation** (3 days)
   - Replace TypedDict with Pydantic models
   - Add runtime validation
   - Schema versioning
   - **Files:** `agents/base_agent.py`, all graph files

4. **BaseAgent Refactor** (4 days)
   - Move common initialization to BaseAgent
   - Add template methods
   - Implement event protocol enforcement
   - **Files:** `agents/base_agent.py`, all agent implementations

5. **Node Observability** (1 week)
   - Instrument nodes with timing metrics
   - Add span tracing
   - Create execution dashboard
   - **Files:** All graph files, new `graphs/observability.py`

**Impact:** Significantly improves code quality, reliability, and maintainability.

---

### Phase 3: Strategic Refactors (1-2 months)
**Goal:** Scalability, distributed systems support, production-readiness.

1. **Distributed Caching** (2 weeks)
   - Migrate to Redis for artifact cache
   - Add cache metrics and monitoring
   - Implement cache warming strategies
   - **Files:** `cache/artifact_cache.py`, new Redis integration

2. **LLM Provider Improvements** (2 weeks)
   - Implement fallback strategy (primary -> secondary provider)
   - Add rate limiting (token bucket)
   - Cost monitoring per request
   - Provider health checks
   - **Files:** `llm/provider_factory.py`, `llm/provider_client.py`

3. **API Rate Limiting** (1 week)
   - Per-IP rate limiting
   - Per-thread rate limiting
   - Token bucket algorithm
   - **Files:** New `middleware/rate_limiter.py`

4. **Comprehensive Testing** (3 weeks)
   - Integration tests for all agents
   - Contract tests for AG-UI/A2UI protocols
   - Performance benchmarks
   - Chaos engineering tests (failure injection)
   - **Files:** `tests/` expansion

5. **Deployment Hardening** (2 weeks)
   - Health checks (deep health, not just `/health`)
   - Graceful shutdown handlers
   - Kubernetes readiness/liveness probes
   - Circuit breaker metrics
   - **Files:** `main.py`, new `health/` module

**Impact:** Production-ready, scalable, resilient system.

---

## 4. Security Audit

### Threats & Vulnerabilities

#### 🔴 **S1: API Key Exposure**
**Threat:** Secrets leaked via logs, error messages, or environment variables.  
**Vulnerability:** Plain text storage, no redaction in logs.  
**Mitigation:**
- Use `SecretStr` in Pydantic models
- Implement secrets provider (Azure Key Vault)
- Audit all log statements for secret leakage
- Add `.env` to `.gitignore` (verify)

#### 🔴 **S2: Prompt Injection**
**Threat:** User crafts malicious input to manipulate LLM behavior.  
**Vulnerability:** No input sanitization, LLM has direct access to user content.  
**Mitigation:**
- Implement prompt sanitization layer
- Use LLM guardrails (Azure Content Safety, LlamaGuard)
- Validate tool call arguments
- Add input length limits

#### 🟠 **S3: Denial of Service (DoS)**
**Threat:** Attacker sends large payloads or excessive requests.  
**Vulnerability:** No rate limiting, no max message length, unbounded cache.  
**Mitigation:**
- API rate limiting (per-IP, per-thread)
- Max message length validation (100KB)
- Cache size limits with eviction
- Request timeout enforcement

#### 🟠 **S4: Information Leakage**
**Threat:** Sensitive data exposed in error messages or logs.  
**Vulnerability:** Full tracebacks sent to client, PII not redacted.  
**Mitigation:**
- Sanitize error messages
- Redact PII in logs (email, names, etc.)
- Use error codes instead of detailed messages
- Log full details server-side only

#### 🟡 **S5: Insecure Dependencies**
**Threat:** Vulnerable packages in `requirements.txt`.  
**Vulnerability:** No dependency scanning, no lock file.  
**Mitigation:**
- Use `pip-audit` or `safety` for vulnerability scanning
- Pin versions in `requirements.txt`
- Generate `requirements.lock` with hashes
- Regular dependency updates

### PII Redaction Strategy
```python
# observability/redaction.py
import re

PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
}

def redact_pii(text: str) -> str:
    """Redact PII from text"""
    for pii_type, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
    return text

# Usage in logging
logger.info("user_message", content=redact_pii(message_content))
```

---

## 5. Performance Audit

### Bottlenecks Identified

#### **P1: LLM Streaming Latency**
**Issue:** First token latency not measured or optimized.  
**Evidence:** No metrics, no caching of common prompts.  
**Impact:** Poor user experience for first response.

**Optimization:**
- Measure TTFT (Time To First Token)
- Implement prompt caching (if provider supports)
- Use smaller models for simple queries
- Parallel LLM calls for independent tasks

#### **P2: Synchronous Graph Execution**
**Issue:** Nodes execute sequentially even when independent.  
**Evidence:** Canvas graph has sequential prepare -> detect -> agent flow.  
**Impact:** Unnecessary latency for independent operations.

**Optimization:**
```python
# Instead of sequential
graph.add_edge("prepare_state", "detect_intent")
graph.add_edge("detect_intent", "canvas_agent")

# Use parallel execution for independent nodes
from langgraph.graph import parallel

graph.add_node("parallel_tasks", parallel([
    prepare_cache_lookup,
    validate_input,
    load_context
]))
```

#### **P3: N+1 Cache Lookups**
**Issue:** Multiple cache lookups for same artifact in canvas flow.  
**Evidence:**
```python
# prepare_canvas_state - cache lookup 1
artifact = artifact_cache.get(artifact_id)

# canvas_agent.run - cache lookup 2
cached_artifact = artifact_cache.get(artifact_id)
```

**Optimization:**
- Single cache lookup at graph entry
- Pass artifact through state graph
- Add cache warming for hot artifacts

#### **P4: Unbounded Event Queue**
**Issue:** AsyncIO queue can grow without bounds during slow streaming.  
**Evidence:** `event_queue = asyncio.Queue()` with no maxsize.  
**Impact:** Memory growth during backpressure.

**Optimization:**
```python
# api/routes.py
event_queue = asyncio.Queue(maxsize=100)  # Bounded queue

try:
    await asyncio.wait_for(event_queue.put(event), timeout=5.0)
except asyncio.TimeoutError:
    logger.warning("Event queue full, dropping event")
```

### Token Usage Optimization

**Current State:** No token tracking or optimization.

**Recommendations:**
1. Track tokens per request (prompt + completion)
2. Implement sliding window for conversation history
3. Summarize old messages instead of sending full history
4. Use embeddings for context retrieval instead of full text

```python
# llm/token_manager.py
from tiktoken import encoding_for_model

class TokenManager:
    def __init__(self, model: str, max_tokens: int = 4096):
        self.encoding = encoding_for_model(model)
        self.max_tokens = max_tokens
    
    def trim_messages(self, messages: List[Dict]) -> List[Dict]:
        """Keep only recent messages within token limit"""
        total_tokens = 0
        trimmed = []
        
        for msg in reversed(messages):
            msg_tokens = len(self.encoding.encode(msg["content"]))
            if total_tokens + msg_tokens > self.max_tokens:
                break
            trimmed.insert(0, msg)
            total_tokens += msg_tokens
        
        return trimmed
```

---

## 6. Observability Audit

### LangFuse Integration
**Current State:** Mentioned in instructions, but no visible integration.

**Gaps:**
1. No LangFuse trace initialization in graph execution
2. No span annotations for node execution
3. No token usage tracking
4. No cost tracking
5. Environment tagging missing

**Implementation Plan:**
```python
# observability/langfuse.py
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse_client = Langfuse()

@observe(name="agent_execution")
async def execute_agent_with_tracing(agent_id: str, state: dict, config: dict):
    """Wrapper that adds LangFuse tracing to agent execution"""
    trace = langfuse_client.trace(
        name=f"agent_{agent_id}",
        metadata={
            "agent_id": agent_id,
            "model": config.get("model"),
            "provider": config.get("provider"),
            "request_id": request_id_ctx.get(),
            "environment": "production"
        }
    )
    
    with trace.span(name="graph_execution") as span:
        result = await graph.ainvoke(state, config)
        
        # Track tokens and cost
        span.update(
            metadata={
                "tokens_used": result.get("tokens_used", 0),
                "cost_usd": result.get("cost_usd", 0)
            }
        )
    
    return result
```

### Metrics Gaps

| Metric | Status | Priority |
|--------|--------|----------|
| Request latency (p50, p95, p99) | ❌ Missing | HIGH |
| Agent execution time per node | ❌ Missing | HIGH |
| LLM token usage per request | ❌ Missing | HIGH |
| Cache hit rate | ❌ Missing | MEDIUM |
| Error rate by agent/node | ❌ Missing | HIGH |
| Concurrent requests | ❌ Missing | MEDIUM |
| Queue depth | ❌ Missing | MEDIUM |
| Cost per request | ❌ Missing | HIGH |

**Recommendation:** Implement Prometheus metrics exporter.

```python
# observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge

agent_requests_total = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["agent_id", "status"]
)

agent_duration_seconds = Histogram(
    "agent_duration_seconds",
    "Agent execution duration",
    ["agent_id", "node"]
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["agent_id", "model", "type"]  # type: prompt/completion
)

cache_hit_rate = Gauge(
    "cache_hit_rate",
    "Artifact cache hit rate"
)
```

### Logging Gaps

**Current:** Basic Python logging with plain text format.

**Missing:**
- Structured fields (JSON logs)
- Correlation IDs across async execution
- Performance metrics in logs
- Log levels inconsistent (DEBUG vs INFO)
- No log sampling for high-volume events

**Example Structured Log:**
```json
{
  "timestamp": "2026-01-01T12:00:00.000Z",
  "level": "INFO",
  "message": "agent_completed",
  "agent_id": "canvas",
  "model": "qwen:7b",
  "provider": "ollama",
  "thread_id": "thread-123",
  "run_id": "run-456",
  "request_id": "req-789",
  "duration_ms": 1234,
  "tokens_used": 500,
  "cost_usd": 0.001
}
```

---

## 7. Testing Gaps

### Current Coverage
**Test Files:** 20+ test files in `backend/tests/`  
**Patterns:** Pytest with asyncio, some integration tests  
**Gaps:** See below

### Unit Test Gaps

| Component | Coverage | Missing Tests |
|-----------|----------|---------------|
| BaseAgent | ❌ No tests | Abstract method validation, lifecycle |
| AgentRegistry | ✅ Good | Edge cases (duplicate registration) |
| GraphFactory | ✅ Good | Error handling for invalid agent_id |
| LLM Providers | ⚠️ Partial | Retry logic, rate limiting, fallback |
| Artifact Cache | ❌ No tests | TTL, eviction, thread-safety |
| EventEncoder | ✅ Good | Edge cases (malformed events) |
| Config | ❌ No tests | Validation, secrets handling |

### Integration Test Gaps

**Missing:**
1. **End-to-End SSE Streaming:** No test verifying full request -> graph -> agent -> SSE pipeline
2. **Multi-Agent Routing:** No test for insurance supervisor routing logic
3. **A2UI User Action Flow:** Test exists, but limited coverage
4. **Canvas Partial Update:** No test for selectedText-based editing
5. **LLM Provider Fallback:** No test for provider switching on failure

**Needed:**
```python
# tests/integration/test_e2e_streaming.py
@pytest.mark.asyncio
async def test_chat_endpoint_e2e_streaming():
    """Test full chat endpoint with SSE streaming"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/api/chat/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "thread_id": "test-thread",
                "run_id": "test-run"
            }
        ) as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
            
            # Verify event sequence
            assert events[0]["type"] == "run_started"
            assert any(e["type"] == "text_message_start" for e in events)
            assert any(e["type"] == "text_message_content" for e in events)
            assert events[-1]["type"] == "run_finished"
```

### Contract Tests (Missing)

**Need:** Tests verifying AG-UI and A2UI protocol compliance.

```python
# tests/contract/test_agui_protocol.py
def test_run_started_event_schema():
    """Verify RunStartedEvent matches AG-UI spec"""
    event = RunStartedEvent(
        type=EventType.RUN_STARTED,
        thread_id="test",
        run_id="test"
    )
    
    # Validate against official schema
    assert event.model_dump() == {
        "type": "run_started",
        "threadId": "test",
        "runId": "test"
    }
```

### Performance Tests (Missing)

**Need:** Load tests, latency benchmarks, token usage tracking.

```python
# tests/performance/test_load.py
@pytest.mark.benchmark
def test_chat_agent_latency(benchmark):
    """Benchmark chat agent response time"""
    result = benchmark(
        lambda: asyncio.run(execute_chat_request())
    )
    
    assert result.stats.mean < 2.0  # < 2s average latency
    assert result.stats.p95 < 5.0   # < 5s p95 latency
```

### CI/CD Gates (Missing)

**Needed:**
1. Automated test execution on PR
2. Code coverage threshold (target: 80%)
3. Lint/type checking (mypy, ruff)
4. Security scanning (pip-audit, bandit)
5. Performance regression tests

---

## 8. Code Quality Issues

### Anti-Patterns Identified

#### **AP1: God Object - routes.py**
**Issue:** Single file with 720 lines, 5+ endpoints, mixed concerns.  
**Pattern:** Violation of Single Responsibility Principle.

**Refactor:**
```
api/
  routes/
    chat.py         # Chat endpoints
    agents.py       # Agent management
    models.py       # Model listing
    canvas.py       # Canvas endpoints (deprecated)
    user_actions.py # A2UI user actions
```

#### **AP2: Primitive Obsession - State Passing**
**Issue:** State passed as `dict` instead of typed objects.  
**Pattern:** Lack of type safety, prone to KeyErrors.

**Example:**
```python
# Bad
state = {
    "messages": [...],
    "thread_id": "...",
    "run_id": "..."
}

# Good
@dataclass
class GraphExecutionContext:
    messages: List[Message]
    thread_id: str
    run_id: str
    request_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### **AP3: Magic Strings**
**Issue:** Event types, agent IDs, provider names as strings.  
**Pattern:** Typos cause runtime errors, hard to refactor.

**Refactor:**
```python
# constants.py
class AgentType(str, Enum):
    CHAT = "chat"
    CANVAS = "canvas"
    A2UI = "a2ui"
    A2UI_LOOP = "a2ui-loop"

class ProviderType(str, Enum):
    OLLAMA = "ollama"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure-openai"

# Usage
agent = agent_registry.get_agent(AgentType.CHAT)
```

#### **AP4: Copy-Paste Code**
**Issue:** Exception handling duplicated across 3 endpoints.  
**Pattern:** Maintenance burden, inconsistency risk.

**Solution:** Extract to shared function or decorator (see Finding #3).

### Type Hints Coverage
**Current:** Partial - some functions lack return types.  
**Target:** 100% coverage with mypy strict mode.

**Example Missing Types:**
```python
# agents/canvas_agent.py - Line 150
async def process_sync(self, state: CanvasGraphState):  # Missing return type
    """Synchronous version for LangGraph node execution."""
```

**Fixed:**
```python
async def process_sync(self, state: CanvasGraphState) -> CanvasGraphState:
    """Synchronous version for LangGraph node execution."""
```

### Docstring Coverage
**Current:** ~60% - key functions documented, many missing.  
**Target:** 90% with consistent Google-style docstrings.

**Example:**
```python
def create_graph(cls, agent_id: str, model: Optional[str] = None, provider: Optional[str] = None):
    """
    Dynamically create and compile a graph for the given agent_id
    
    Args:
        agent_id: Identifier from agent registry (e.g., "chat", "canvas")
        model: Optional model name (e.g., "qwen:7b", "gemini-pro")
        provider: Optional provider name (e.g., "ollama", "gemini", "azure-openai")
        
    Returns:
        Compiled LangGraph workflow ready for execution (CompiledStateGraph)
        
    Raises:
        ValueError: If agent_id is not registered, unavailable, or no graph creator exists
        
    Example:
        >>> graph = graph_factory.create_graph("chat", model="qwen:7b", provider="ollama")
        >>> config = {"configurable": {"event_callback": callback_fn}}
        >>> result = await graph.ainvoke(state, config)
    """
```

---

## 9. Detailed Code Examples

### Critical Snippets Requiring Immediate Attention

#### **Example 1: Request ID Middleware**
**File:** `middleware/correlation.py` (new)

```python
"""
Correlation ID Middleware

Generates and propagates request IDs across the async execution pipeline.
"""

from contextvars import ContextVar
from typing import Callable
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for thread-safe request ID storage
request_id_ctx: ContextVar[str] = ContextVar('request_id', default=None)

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to inject and propagate correlation IDs"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in context variable (thread-safe)
        request_id_ctx.set(request_id)
        
        # Process request
        response: Response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

# Integration in main.py
from middleware.correlation import CorrelationMiddleware

app = FastAPI(title="AgentKit Backend")
app.add_middleware(CorrelationMiddleware)  # Add before CORS
app.add_middleware(CORSMiddleware, ...)
```

**Usage in routes:**
```python
from middleware.correlation import request_id_ctx

# Add to AG-UI events
yield encoder.encode(
    RunStartedEvent(
        type=EventType.RUN_STARTED,
        thread_id=input_data.thread_id,
        run_id=input_data.run_id,
        metadata={"request_id": request_id_ctx.get()}
    )
)

# Add to logs
logger.info(
    "agent_started",
    agent_id=agent_id,
    request_id=request_id_ctx.get()
)
```

---

#### **Example 2: Enhanced Artifact Cache with TTL**
**File:** `cache/artifact_cache.py`

```python
"""
Artifact Cache with TTL and Eviction

Thread-safe in-memory cache with time-to-live and size limits.
Supports Redis backend for distributed deployments.
"""

import logging
import threading
import time
from typing import Optional, Dict
from cachetools import TTLCache
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class ArtifactCache:
    """
    Thread-safe artifact cache with TTL and LRU eviction.
    
    Features:
    - Time-to-live (TTL) based expiration
    - Size-based LRU eviction
    - Thread-safe operations
    - Metrics tracking (hit rate, size)
    - Optional Redis backend for distributed systems
    
    Usage:
        cache = ArtifactCache(maxsize=1000, ttl=3600)
        cache.set("artifact-123", artifact_data)
        artifact = cache.get("artifact-123")
    """
    
    def __init__(self, maxsize: int = 1000, ttl: int = 3600, use_redis: bool = False):
        """
        Initialize artifact cache
        
        Args:
            maxsize: Maximum number of artifacts to cache
            ttl: Time-to-live in seconds (default: 1 hour)
            use_redis: Use Redis backend instead of in-memory (for distributed systems)
        """
        self._maxsize = maxsize
        self._ttl = ttl
        self._use_redis = use_redis
        
        if use_redis:
            self._init_redis_backend()
        else:
            self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
            self._lock = threading.Lock()
        
        self._metrics = CacheMetrics()
        self._metrics_lock = threading.Lock()
        
        logger.info(f"ArtifactCache initialized: maxsize={maxsize}, ttl={ttl}s, redis={use_redis}")
    
    def _init_redis_backend(self):
        """Initialize Redis backend (for future implementation)"""
        # TODO: Implement Redis backend
        raise NotImplementedError("Redis backend not yet implemented")
    
    def set(self, artifact_id: str, artifact: dict, thread_id: str = None) -> None:
        """
        Store artifact in cache
        
        Args:
            artifact_id: Unique artifact identifier
            artifact: Artifact data dictionary
            thread_id: Optional thread ID for logging
        """
        with self._lock:
            self._cache[artifact_id] = artifact
        
        logger.debug(
            "cache_set",
            artifact_id=artifact_id,
            thread_id=thread_id,
            size=len(self._cache)
        )
    
    def get(self, artifact_id: str) -> Optional[dict]:
        """
        Retrieve artifact from cache
        
        Args:
            artifact_id: Unique artifact identifier
            
        Returns:
            Artifact data or None if not found/expired
        """
        with self._lock:
            artifact = self._cache.get(artifact_id)
        
        # Update metrics
        with self._metrics_lock:
            if artifact:
                self._metrics.hits += 1
                logger.debug("cache_hit", artifact_id=artifact_id)
            else:
                self._metrics.misses += 1
                logger.debug("cache_miss", artifact_id=artifact_id)
        
        return artifact
    
    def delete(self, artifact_id: str) -> bool:
        """
        Delete artifact from cache
        
        Args:
            artifact_id: Unique artifact identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if artifact_id in self._cache:
                del self._cache[artifact_id]
                logger.debug("cache_delete", artifact_id=artifact_id)
                return True
        return False
    
    def clear(self) -> None:
        """Clear all artifacts from cache"""
        with self._lock:
            self._cache.clear()
        logger.info("cache_cleared")
    
    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        with self._metrics_lock:
            self._metrics.size = len(self._cache)
            return CacheMetrics(
                hits=self._metrics.hits,
                misses=self._metrics.misses,
                evictions=self._metrics.evictions,
                size=self._metrics.size
            )


# Global instance
artifact_cache = ArtifactCache()
```

---

#### **Example 3: Centralized Exception Handling**
**File:** `exceptions/handlers.py` (new)

```python
"""
Centralized Exception Handling

Provides consistent error responses and logging across all endpoints.
"""

import logging
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from middleware.correlation import request_id_ctx

logger = logging.getLogger(__name__)


class AgentKitException(Exception):
    """Base exception for all AgentKit errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AgentExecutionError(AgentKitException):
    """Error during agent execution"""
    pass


class RetryableError(AgentKitException):
    """Error that can be retried by client"""
    pass


class ValidationError(AgentKitException):
    """Input validation error"""
    pass


class ProviderError(AgentKitException):
    """LLM provider error"""
    pass


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    retryable: bool = False,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        error_code: Machine-readable error code (e.g., "agent_execution_failed")
        message: Human-readable error message
        status_code: HTTP status code
        retryable: Whether client should retry
        details: Additional error details (sanitized)
    
    Returns:
        JSONResponse with error payload
    """
    request_id = request_id_ctx.get()
    
    error_payload = {
        "error": error_code,
        "message": message,
        "request_id": request_id,
        "retryable": retryable
    }
    
    if details:
        error_payload["details"] = details
    
    # Log server-side with full details
    logger.error(
        "error_response",
        error_code=error_code,
        message=message,
        status_code=status_code,
        request_id=request_id,
        details=details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_payload
    )


# FastAPI exception handlers

async def agentkit_exception_handler(request: Request, exc: AgentKitException):
    """Handle custom AgentKit exceptions"""
    return create_error_response(
        error_code=exc.__class__.__name__,
        message=exc.message,
        status_code=500,
        retryable=isinstance(exc, RetryableError),
        details=exc.details
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return create_error_response(
        error_code="validation_error",
        message="Invalid request parameters",
        status_code=422,
        retryable=False,
        details={"errors": exc.errors()}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    return create_error_response(
        error_code="http_error",
        message=exc.detail,
        status_code=exc.status_code,
        retryable=False
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected exceptions"""
    # Log full traceback server-side
    logger.exception(
        "unexpected_error",
        error_type=type(exc).__name__,
        request_id=request_id_ctx.get()
    )
    
    # Return generic error to client (don't leak internal details)
    return create_error_response(
        error_code="internal_error",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        retryable=True
    )


# Register handlers in main.py
from exceptions.handlers import (
    AgentKitException,
    agentkit_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)

app.add_exception_handler(AgentKitException, agentkit_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
```

---

## 10. Summary & Next Steps

### Executive Summary

**Overall Assessment:** The backend architecture is **functional and well-structured** for early-stage development, but requires **significant hardening for production use**. The codebase demonstrates good understanding of LangGraph patterns and AG-UI protocol, but lacks critical operational concerns (observability, resilience, security).

**Strengths:**
1. ✅ Clean separation between agents, graphs, and API layer
2. ✅ Factory patterns for extensibility (GraphFactory, LLMProviderFactory)
3. ✅ Event-driven architecture with streaming support
4. ✅ Good test coverage for core functionality

**Critical Weaknesses:**
1. ❌ No correlation IDs or distributed tracing
2. ❌ Plain text secrets management
3. ❌ No exception handling standardization
4. ❌ Unbounded in-memory cache
5. ❌ No LLM resilience (retry, rate limit, fallback)

**Risk Assessment:**
- **Security Risk:** HIGH - Secrets exposure, no input validation, info leakage
- **Reliability Risk:** HIGH - No retry logic, no circuit breakers, no health checks
- **Scalability Risk:** MEDIUM - Single-instance cache, no distributed support
- **Maintainability Risk:** MEDIUM - Copy-paste code, weak abstractions

### Recommended Priorities

**Week 1-2 (Critical):**
1. Implement secrets management (SecretStr)
2. Add centralized exception handling
3. Add request correlation IDs
4. Implement input validation

**Week 3-4 (High):**
5. Fix artifact cache (TTL, thread-safety)
6. Add LLM retry logic
7. Implement structured logging
8. Add state validation (Pydantic models)

**Month 2 (Medium):**
9. Node observability instrumentation
10. Redis cache migration
11. API rate limiting
12. Comprehensive testing expansion

**Month 3+ (Strategic):**
13. Provider fallback strategy
14. Performance optimization
15. Production deployment hardening

### Success Metrics

**Phase 1 Targets:**
- 🎯 Zero secrets in plain text (100% SecretStr)
- 🎯 100% of endpoints with standardized error handling
- 🎯 All requests traceable via correlation ID

**Phase 2 Targets:**
- 🎯 Cache hit rate > 70%
- 🎯 LLM request success rate > 99% (with retry)
- 🎯 All logs structured (JSON format)
- 🎯 State validation coverage 100%

**Phase 3 Targets:**
- 🎯 P95 latency < 3 seconds
- 🎯 API rate limiting enforced
- 🎯 Test coverage > 85%
- 🎯 Zero high-severity security vulnerabilities

---

## Appendix: Reference Materials

### Architecture Diagrams
- See Section 1 for ASCII architecture map

### Anti-Pattern Catalog
- **God Object:** routes.py (720 lines, multiple responsibilities)
- **Primitive Obsession:** State as dict instead of typed objects
- **Magic Strings:** Event types, agent IDs as strings
- **Copy-Paste Programming:** Exception handling duplicated

### Glossary
- **AG-UI:** Agent-UI protocol for streaming events (run_started, text_message_content, etc.)
- **A2UI:** Agent-to-UI protocol for interactive components (buttons, forms, etc.)
- **LangGraph:** State machine framework for agent orchestration
- **SSE:** Server-Sent Events (streaming protocol)
- **TTL:** Time-To-Live (cache expiration)
- **LRU:** Least Recently Used (eviction policy)
- **TTFT:** Time To First Token (LLM latency metric)

### Related Documents
- `agents.md` - Multi-agent architecture overview
- `.github/agents/backend.agent.md` - Backend implementation patterns
- `.docs/2-knowledge-base/` - Existing knowledge base
- `TEST_RESULTS.md` - Current test status

---

**End of Review**

*This review was conducted in Backend Reviewer mode. For frontend reviews, see `.github/agents/frontend.agent.md` guidance.*
