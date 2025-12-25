"""
Server-side artifact caching to avoid sending full artifacts from frontend.

This module provides an in-memory cache for artifacts with TTL (time-to-live) support.
Artifacts are stored with unique IDs and can be retrieved/updated by the canvas agent.
"""
import uuid
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from graphs.canvas_graph import Artifact

logger = logging.getLogger(__name__)


@dataclass
class CachedArtifact:
    """Wrapper for cached artifact with metadata"""
    artifact_id: str
    artifact: Artifact
    created_at: datetime
    last_accessed: datetime
    thread_id: str  # Associate with conversation thread


class ArtifactCache:
    """In-memory cache for artifacts with TTL support"""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize artifact cache
        
        Args:
            ttl_hours: Time-to-live in hours for cached artifacts (default: 24)
        """
        self._cache: Dict[str, CachedArtifact] = {}
        self._ttl = timedelta(hours=ttl_hours)
        logger.info(f"ArtifactCache initialized with TTL: {ttl_hours} hours")
    
    def store(self, artifact: Artifact, thread_id: str, artifact_id: Optional[str] = None) -> str:
        """
        Store artifact in cache and return artifact ID
        
        Args:
            artifact: Artifact to cache
            thread_id: Thread ID for association
            artifact_id: Optional existing artifact ID (for updates)
        
        Returns:
            str: Artifact ID
        """
        if artifact_id is None:
            artifact_id = str(uuid.uuid4())
            logger.info(f"Created new artifact_id: {artifact_id} for thread: {thread_id}")
        else:
            logger.info(f"Updating existing artifact_id: {artifact_id} for thread: {thread_id}")
        
        now = datetime.now()
        self._cache[artifact_id] = CachedArtifact(
            artifact_id=artifact_id,
            artifact=artifact,
            created_at=now,
            last_accessed=now,
            thread_id=thread_id
        )
        
        # Clean up expired entries
        self._cleanup()
        
        logger.debug(f"Artifact stored successfully. Cache size: {len(self._cache)}")
        return artifact_id
    
    def get(self, artifact_id: str) -> Optional[Artifact]:
        """
        Retrieve artifact from cache by ID
        
        Args:
            artifact_id: Artifact ID
        
        Returns:
            Artifact or None if not found or expired
        """
        cached = self._cache.get(artifact_id)
        
        if cached is None:
            logger.warning(f"Artifact not found in cache: {artifact_id}")
            return None
        
        # Check if expired
        if datetime.now() - cached.created_at > self._ttl:
            logger.info(f"Artifact expired, removing from cache: {artifact_id}")
            del self._cache[artifact_id]
            return None
        
        # Update last accessed time
        cached.last_accessed = datetime.now()
        logger.debug(f"Artifact retrieved from cache: {artifact_id}")
        return cached.artifact
    
    def update(self, artifact_id: str, artifact: Artifact) -> bool:
        """
        Update existing artifact in cache
        
        Args:
            artifact_id: Artifact ID to update
            artifact: New artifact data
        
        Returns:
            bool: True if updated, False if not found
        """
        cached = self._cache.get(artifact_id)
        
        if cached is None:
            logger.warning(f"Cannot update, artifact not found: {artifact_id}")
            return False
        
        cached.artifact = artifact
        cached.last_accessed = datetime.now()
        logger.info(f"Artifact updated in cache: {artifact_id}")
        return True
    
    def delete(self, artifact_id: str) -> bool:
        """
        Remove artifact from cache
        
        Args:
            artifact_id: Artifact ID to remove
        
        Returns:
            bool: True if deleted, False if not found
        """
        if artifact_id in self._cache:
            del self._cache[artifact_id]
            logger.info(f"Artifact deleted from cache: {artifact_id}")
            return True
        
        logger.warning(f"Cannot delete, artifact not found: {artifact_id}")
        return False
    
    def get_thread_artifacts(self, thread_id: str) -> Dict[str, Artifact]:
        """
        Get all artifacts for a specific thread
        
        Args:
            thread_id: Thread ID
        
        Returns:
            Dict mapping artifact_id to artifact
        """
        artifacts = {
            artifact_id: cached.artifact
            for artifact_id, cached in self._cache.items()
            if cached.thread_id == thread_id and datetime.now() - cached.created_at <= self._ttl
        }
        
        logger.debug(f"Retrieved {len(artifacts)} artifacts for thread: {thread_id}")
        return artifacts
    
    def _cleanup(self):
        """Remove expired artifacts from cache"""
        now = datetime.now()
        expired_ids = [
            artifact_id
            for artifact_id, cached in self._cache.items()
            if now - cached.created_at > self._ttl
        ]
        
        for artifact_id in expired_ids:
            del self._cache[artifact_id]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired artifacts from cache")
    
    def clear(self):
        """Clear all artifacts from cache (mainly for testing)"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared, removed {count} artifacts")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        now = datetime.now()
        stats = {
            "total_artifacts": len(self._cache),
            "threads": len(set(cached.thread_id for cached in self._cache.values())),
            "expired": sum(1 for cached in self._cache.values() if now - cached.created_at > self._ttl)
        }
        return stats


# Global singleton instance
artifact_cache = ArtifactCache(ttl_hours=24)
