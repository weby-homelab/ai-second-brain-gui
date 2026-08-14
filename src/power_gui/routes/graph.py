"""Graph visualization and API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/graph", response_class=HTMLResponse)
async def graph_view(
    request: Request,
    max_nodes: int = Query(300, ge=10, le=1000),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render interactive knowledge graph page with accessibility table fallback."""
    templates: Jinja2Templates = request.app.state.templates

    projection = client.get_graph_projection(max_nodes=max_nodes)

    return templates.TemplateResponse(
        request=request,
        name="graph.html",
        context={
            "projection": projection,
            "max_nodes": max_nodes,
            "settings": settings,
        },
    )


@router.get("/api/graph/data", response_class=JSONResponse)
async def graph_data_api(
    max_nodes: int = Query(500, ge=10, le=1000),
    client: PowerClient = Depends(get_client),
) -> JSONResponse:
    """Return JSON formatted nodes and links for force-graph library."""
    projection = client.get_graph_projection(max_nodes=max_nodes)
    return JSONResponse(
        content={
            "nodes": [n.model_dump() for n in projection.nodes],
            "links": [e.model_dump() for e in projection.edges],
            "total_nodes": projection.total_nodes,
            "total_edges": projection.total_edges,
            "is_truncated": projection.is_truncated,
        }
    )
