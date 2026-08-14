"""Dashboard route for POWER-GUI."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(
    request: Request,
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render main dashboard with vault metrics, active tasks, and system status."""
    templates: Jinja2Templates = request.app.state.templates

    stats = client.get_source_stats()
    tasks = client.list_tasks(limit=10)
    receipts = client.get_receipts(limit=5)
    discovery = client.discover()

    active_tasks = [t for t in tasks if t.state in {"ready", "working", "input-required"}]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "stats": stats,
            "tasks": tasks,
            "active_tasks": active_tasks,
            "receipts": receipts,
            "discovery": discovery.data,
            "settings": settings,
        },
    )
