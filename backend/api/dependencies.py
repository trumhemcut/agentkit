"""
FastAPI Dependencies

Shared dependencies for API endpoints.
"""
import logging
from database.config import get_db

logger = logging.getLogger(__name__)

# Re-export commonly used dependencies
__all__ = ["get_db", "logger"]
