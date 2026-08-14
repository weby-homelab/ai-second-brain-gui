"""Search route for multi-modal knowledge retrieval."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/search")


@router.get("", response_class=HTMLResponse)
async def search_view(
    request: Request,
    q: str = Query("", description="Search query"),
    mode: str = Query("auto", description="Retrieval mode: auto, fts, semantic, reranked"),
    limit: int = Query(20, ge=1, le=100),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Execute search query and display results with provenance."""
    templates: Jinja2Templates = request.app.state.templates

    results_data: dict[str, object] = {}
    if q.strip():
        try:
            env = client.search(q, mode=mode, max_results=limit)
            results_data = env.data
        except Exception as exc:
            results_data = {"error": str(exc), "items": []}

    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "query": q,
            "mode": mode,
            "results": results_data,
            "settings": settings,
        },
    )
