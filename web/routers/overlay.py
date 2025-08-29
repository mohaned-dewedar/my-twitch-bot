"""Overlay routes for HTML template responses."""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional

from web.models.channel import OverlayConfig
from web.services.leaderboard_service import LeaderboardService
from web.dependencies import validate_channel_exists

logger = logging.getLogger(__name__)
router = APIRouter()

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/{channel_name}", response_class=HTMLResponse)
async def overlay_leaderboard(
    request: Request,
    channel_name: str,
    limit: Optional[int] = Query(5, ge=1, le=20, description="Number of entries to show"),
    theme: Optional[str] = Query("default", description="Overlay theme"),
    compact: Optional[bool] = Query(False, description="Use compact mode"),
    refresh: Optional[int] = Query(15, ge=5, le=300, description="Refresh interval in seconds"),
    channel_id: int = Depends(validate_channel_exists)
):
    """
    Render leaderboard overlay HTML for OBS Browser Source.
    
    Args:
        request: FastAPI request object
        channel_name: Channel name to display leaderboard for
        limit: Maximum number of entries to display
        theme: Visual theme for overlay
        compact: Whether to use compact display mode
        refresh: Auto-refresh interval in seconds
        channel_id: Channel ID (injected by dependency)
        
    Returns:
        HTML response optimized for OBS overlay
    """
    try:
        # Create overlay configuration
        config = OverlayConfig(
            theme=theme,
            compact_mode=compact,
            refresh_interval=refresh,
            max_entries=limit
        )
        
        # Get leaderboard data
        leaderboard_data = await LeaderboardService.get_channel_leaderboard(channel_name, limit)
        
        # Choose template based on mode
        template_name = "overlay/compact.html" if compact else "overlay/leaderboard.html"
        
        return templates.TemplateResponse(
            template_name,
            {
                "request": request,
                "channel_name": channel_name,
                "leaderboard": leaderboard_data,
                "config": config,
                "api_url": f"/api/leaderboard/{channel_name}?limit={limit}"
            }
        )
    
    except ValueError as e:
        logger.warning(f"Channel validation failed for {channel_name}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Overlay error for {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to render overlay")


@router.get("/{channel_name}/preview", response_class=HTMLResponse)
async def preview_overlay(
    request: Request,
    channel_name: str,
    limit: Optional[int] = Query(5, ge=1, le=20),
    theme: Optional[str] = Query("default"),
    compact: Optional[bool] = Query(False),
    channel_id: int = Depends(validate_channel_exists)
):
    """
    Preview overlay with browser controls (non-OBS version).
    
    This version includes refresh controls and debugging info,
    useful for testing before setting up in OBS.
    """
    try:
        config = OverlayConfig(
            theme=theme,
            compact_mode=compact,
            refresh_interval=30,  # Longer interval for preview
            max_entries=limit
        )
        
        leaderboard_data = await LeaderboardService.get_channel_leaderboard(channel_name, limit)
        
        return templates.TemplateResponse(
            "overlay/preview.html",
            {
                "request": request,
                "channel_name": channel_name,
                "leaderboard": leaderboard_data,
                "config": config,
                "overlay_url": f"/overlay/{channel_name}",
                "api_url": f"/api/leaderboard/{channel_name}?limit={limit}"
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Preview error for {channel_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to render preview")