"""Read-only Federation status and multi-vault discovery route."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/federation")


@router.get("", response_class=HTMLResponse)
async def federation_view(
    request: Request,
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render federated nodes status and multi-vault search cockpit."""
    templates: Jinja2Templates = request.app.state.templates

    discovery = client.discover()
    stats = client.get_source_stats()

    # Local node representation and mock federated allowlisted nodes
    nodes = [
        {
            "node_id": "local-core",
            "vault_id": stats.vault_id,
            "role": "Home Core (PRXMX-01)",
            "endpoint": "local",
            "status": "online",
            "notes_count": stats.total_notes,
            "trust_level": "authoritative",
        },
        {
            "node_id": "remote-ws",
            "vault_id": "ws-secondary",
            "role": "AI Workstation (WS)",
            "endpoint": "http://100.68.179.109:8080",
            "status": "standby",
            "notes_count": 0,
            "trust_level": "read-only-federated",
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="federation.html",
        context={
            "nodes": nodes,
            "discovery": discovery.data,
            "settings": settings,
        },
    )
