"""Authentication routes for session login and logout."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ..auth.session import SessionManager
from ..config import Settings, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_view(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render login form."""
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "settings": settings,
        },
    )


@router.post("/login")
async def login_action(
    request: Request,
    password: str = Form(...),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Verify password and set signed session cookie."""
    if not settings.auth_enabled:
        return RedirectResponse(url="/dashboard", status_code=303)

    if not settings.admin_password_hash or password != settings.admin_password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_mgr = SessionManager(settings.secret_key)
    auth_session = session_mgr.create_session("admin")

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=auth_session,
        httponly=True,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        secure=settings.cookie_secure,
        max_age=86400,
    )
    return response


@router.post("/logout")
async def logout_action(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=settings.session_cookie_name)
    return response
