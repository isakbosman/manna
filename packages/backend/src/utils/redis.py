"""
Redis connection and utility functions.
"""

import redis.asyncio as redis
from typing import Optional
import logging
import json

from ..config import settings

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client instance.
    
    Returns:
        Redis client instance or None if connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            _redis_client = None
    
    return _redis_client


async def check_redis_connection() -> bool:
    """
    Check if Redis connection is working.
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            await client.ping()
            return True
        return False
    except Exception as e:
        logger.error(f"Redis connection check failed: {e}")
        return False


async def cache_get(key: str) -> Optional[str]:
    """
    Get value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value or None if not found
    """
    try:
        client = await get_redis_client()
        if client:
            return await client.get(key)
        return None
    except Exception as e:
        logger.error(f"Cache get failed for key {key}: {e}")
        return None


async def cache_set(
    key: str,
    value: str,
    expire: Optional[int] = None
) -> bool:
    """
    Set value in Redis cache.
    
    Args:
        key: Cache key
        value: Value to cache
        expire: Expiration time in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            if expire:
                await client.setex(key, expire, value)
            else:
                await client.set(key, value)
            return True
        return False
    except Exception as e:
        logger.error(f"Cache set failed for key {key}: {e}")
        return False


async def cache_delete(key: str) -> bool:
    """
    Delete value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis_client()
        if client:
            await client.delete(key)
            return True
        return False
    except Exception as e:
        logger.error(f"Cache delete failed for key {key}: {e}")
        return False


async def cache_json_get(key: str) -> Optional[dict]:
    """
    Get JSON value from Redis cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached JSON object or None if not found
    """
    try:
        value = await cache_get(key)
        if value:
            return json.loads(value)
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON for key {key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Cache JSON get failed for key {key}: {e}")
        return None


async def cache_json_set(
    key: str,
    value: dict,
    expire: Optional[int] = None
) -> bool:
    """
    Set JSON value in Redis cache.
    
    Args:
        key: Cache key
        value: JSON object to cache
        expire: Expiration time in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        json_str = json.dumps(value)
        return await cache_set(key, json_str, expire)
    except json.JSONEncodeError as e:
        logger.error(f"Failed to encode JSON for key {key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Cache JSON set failed for key {key}: {e}")
        return False