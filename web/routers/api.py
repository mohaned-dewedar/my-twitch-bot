"""API routes for JSON responses."""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from web.models.leaderboard import LeaderboardResponse, ChannelSummary, ErrorResponse
from web.models.channel import ChannelParams
from web.services.leaderboard_service import LeaderboardService
from web.dependencies import validate_channel_exists

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/leaderboard/{channel_name}", response_model=LeaderboardResponse)
async def get_leaderboard(
    channel_name: str,
    limit: Optional[int] = Query(5, ge=1, le=50, description="Number of entries to return"),
    channel_id: int = Depends(validate_channel_exists)
) -> LeaderboardResponse:
    """
    Get leaderboard data for a channel in JSON format.
    
    Args:
        channel_name: Channel name to get leaderboard for
        limit: Maximum number of entries to return
        channel_id: Channel ID (injected by dependency)
        
    Returns:
        LeaderboardResponse with formatted leaderboard data
    """
    try:
        return await LeaderboardService.get_channel_leaderboard(channel_name, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API error getting leaderboard for {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary/{channel_name}", response_model=ChannelSummary)
async def get_channel_summary(
    channel_name: str,
    channel_id: int = Depends(validate_channel_exists)
) -> ChannelSummary:
    """
    Get channel statistics summary.
    
    Args:
        channel_name: Channel name to get summary for
        channel_id: Channel ID (injected by dependency)
        
    Returns:
        ChannelSummary with aggregated statistics
    """
    try:
        return await LeaderboardService.get_channel_summary(channel_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"API error getting summary for {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health")
async def api_health():
    """API health check endpoint."""
    return {
        "status": "healthy",
        "service": "CherryBott API",
        "endpoints": {
            "leaderboard": "/api/leaderboard/{channel_name}",
            "summary": "/api/summary/{channel_name}"
        }
    }