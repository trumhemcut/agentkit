"""
Model Router

Handles model-related endpoints:
- List all available models from all providers
- List models from specific provider
"""
import logging
from fastapi import APIRouter, HTTPException
from llm.provider_client import provider_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/models")
async def list_models():
    """List available models from all providers"""
    try:
        models_data = await provider_client.list_all_models()
        return models_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")


@router.get("/models/{provider}")
async def list_provider_models(provider: str):
    """List models from a specific provider"""
    try:
        models = await provider_client.get_models_by_provider(provider)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching models: {str(e)}")
