import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

# Import all routers
from api.routers import agents, llm_models, chat, a2ui, threads, messages

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Reduce verbosity of third-party libraries
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="AgentKit Backend")
logger.info("AgentKit Backend starting up...")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers with /api prefix
app.include_router(agents.router, prefix="/api", tags=["agents"])
app.include_router(llm_models.router, prefix="/api", tags=["models"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(a2ui.router, prefix="/api", tags=["a2ui"])
app.include_router(threads.router, prefix="/api", tags=["threads"])
app.include_router(messages.router, prefix="/api", tags=["messages"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
