"""FastAPI dependency injection setup."""

from typing import AsyncGenerator
from fastapi import HTTPException
from db.database import Database
from db.channels import get_channel_id
import logging

logger = logging.getLogger(__name__)


async def get_database_pool():
    """Get database connection pool."""
    try:
        pool = await Database.get_pool()
        return pool
    except Exception as e:
        logger.error(f"Failed to get database pool: {e}")
        raise HTTPException(
            status_code=500,
            detail="Database connection failed"
        )


async def validate_channel_exists(channel_name: str) -> int:
    """
    Validate that a channel exists and return its ID.
    
    Args:
        channel_name: The channel name to validate
        
    Returns:
        Channel ID from database
        
    Raises:
        HTTPException: If channel not found
    """
    try:
        channel_id = await get_channel_id(channel_name)
        if channel_id is None:
            raise HTTPException(
                status_code=404,
                detail=f"Channel '{channel_name}' not found"
            )
        return channel_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating channel {channel_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to validate channel"
        )