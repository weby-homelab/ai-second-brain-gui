"""Authentication routes for session login and logout."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ..auth.session import SessionManager
from ..config import Settings, get_settings
from ..i18n import get_request_lang, translate

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
) -> Response:
    """Verify password and set signed session cookie."""
    templates: Jinja2Templates = request.app.state.templates
    lang = get_request_lang(request)
    if not settings.auth_enabled:
        return RedirectResponse(url="/dashboard", status_code=303)

    valid_password = settings.admin_password or settings.admin_password_hash or "weby-brain-secure"
    if not secrets.compare_digest(password, valid_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": translate("invalid_password", lang),
                "settings": settings,
            },
            status_code=401,
        )

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


@router.get("/set-lang")
async def set_language(
    lang: str = "en",
    next: str = "/dashboard",
) -> RedirectResponse:
    """Set language preference in cookie and redirect back to previous page."""
    clean_lang = "uk" if lang.lower() in {"uk", "ua", "ukr"} else "en"
    target = next if next.startswith("/") and not next.startswith("//") else "/dashboard"
    response = RedirectResponse(url=target, status_code=303)
    response.set_cookie(
        key="power_gui_lang",
        value=clean_lang,
        max_age=31536000,
        httponly=False,
        samesite="lax",
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

