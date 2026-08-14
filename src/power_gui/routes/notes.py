"""Notes routes: listing, secure reading, transactional editor, and proposal workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings
from ..view_models.markdown_render import render_markdown

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/notes")


@router.get("", response_class=HTMLResponse)
async def list_notes_view(
    request: Request,
    category: str | None = Query(None),
    tag: str | None = Query(None),
    prefix: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = Query(None),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render notes list with category filtering, search chips, and pagination."""
    templates: Jinja2Templates = request.app.state.templates

    source_list = client.list_sources(
        prefix=prefix,
        category=category,
        tag=tag,
        limit=limit,
        cursor=cursor,
    )
    stats = client.get_source_stats()

    return templates.TemplateResponse(
        request=request,
        name="notes.html",
        context={
            "sources": source_list,
            "category": category,
            "tag": tag,
            "prefix": prefix,
            "stats": stats,
            "settings": settings,
        },
    )


@router.get("/read", response_class=HTMLResponse)
async def read_note_view(
    request: Request,
    path: str = Query("", description="Relative path to note"),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> Response:
    """View note content with sanitized HTML rendering, metadata chips, and ETag."""
    templates: Jinja2Templates = request.app.state.templates

    clean_path = path.strip()
    if not clean_path:
        return RedirectResponse(url="/notes", status_code=303)

    try:
        source_data = client.read_source(clean_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Note '{clean_path}' not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Path traversal forbidden") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    rendered_html = render_markdown(source_data.content)

    return templates.TemplateResponse(
        request=request,
        name="note_view.html",
        context={
            "note": source_data,
            "rendered_html": rendered_html,
            "settings": settings,
        },
    )


@router.get("/edit", response_class=HTMLResponse)
async def edit_note_view(
    request: Request,
    path: str = Query("", description="Relative path to note"),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> Response:
    """Transactional note editor interface with diff preview and preimage ETag."""
    templates: Jinja2Templates = request.app.state.templates

    clean_path = path.strip()
    if not clean_path:
        return RedirectResponse(url="/notes", status_code=303)

    try:
        source_data = client.read_source(clean_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Note '{clean_path}' not found") from exc

    return templates.TemplateResponse(
        request=request,
        name="note_edit.html",
        context={
            "note": source_data,
            "settings": settings,
        },
    )


@router.post("/propose", response_class=HTMLResponse)
async def propose_note_view(
    request: Request,
    path: str = Form(...),
    content: str = Form(...),
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Create a structured, reviewable proposal without directly mutating source."""
    templates: Jinja2Templates = request.app.state.templates

    try:
        proposal_env = client.propose(path, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return templates.TemplateResponse(
        request=request,
        name="proposal_review.html",
        context={
            "proposal": proposal_env.data,
            "receipt": proposal_env.receipt.as_dict(),
            "rel_path": path,
            "settings": settings,
        },
    )


@router.post("/apply")
async def apply_note_view(
    request: Request,
    proposal_id: str = Form(...),
    rel_path: str = Form(...),
    approved: bool = Form(True),
    client: PowerClient = Depends(get_client),
) -> RedirectResponse:
    """Apply an approved proposal with explicit authority and postcondition check."""
    try:
        client.apply({"proposal_id": proposal_id, "path": rel_path}, approved=approved)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RedirectResponse(url=f"/notes/read?path={rel_path}", status_code=303)
