"""Decisions and human approval queue route."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/decisions")


@router.get("", response_class=HTMLResponse)
async def decisions_view(
    request: Request,
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render approval and decision queue."""
    templates: Jinja2Templates = request.app.state.templates

    # Get active tasks requiring human input/approval
    tasks = client.list_tasks(limit=100)
    pending = [t for t in tasks if t.state in {"input-required", "auth-required"}]

    return templates.TemplateResponse(
        request=request,
        name="decisions.html",
        context={
            "pending_decisions": pending,
            "settings": settings,
        },
    )


@router.post("/{task_id}/resolve")
async def resolve_decision_action(
    request: Request,
    task_id: str,
    action: str = Form(...),  # approve / reject / provide_input
    expected_revision: int = Form(...),
    input_value: str | None = Form(None),
    client: PowerClient = Depends(get_client),
) -> RedirectResponse:
    """Approve, reject, or provide input for a pending decision gate."""
    new_state = "working" if action == "approve" else "failed"
    try:
        client.transition_task(
            task_id,
            new_state=new_state,
            expected_revision=expected_revision,
            next_action=f"decision_{action}: {input_value}" if input_value else f"decision_{action}",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return RedirectResponse(url="/decisions", status_code=303)
