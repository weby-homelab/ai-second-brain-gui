"""FastAPI application factory and server entry point for POWER-GUI."""

from __future__ import annotations

import argparse
from pathlib import Path

import power_framework
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from .auth.csrf import get_csrf_token
from .auth.session import SessionManager
from .config import Settings, get_global_settings
from .i18n import get_request_lang, get_request_theme, jinja_translate
from .routes import (
    auth_router,
    dashboard_router,
    decisions_router,
    federation_router,
    graph_router,
    notes_router,
    receipts_router,
    search_router,
    tasks_router,
)

POWER_VERSION = getattr(power_framework, "__version__", "3.6.0")


def jinja_csrf_token(context: dict) -> str:
    """Jinja helper to obtain request-bound CSRF token."""
    request: Request | None = context.get("request")
    if not request:
        return ""
    settings: Settings = getattr(request.app.state, "settings", None) or get_global_settings()
    return get_csrf_token(request, settings)


def jinja_is_authenticated(context: dict) -> bool:
    """Jinja helper to check if current request has authenticated session."""
    request: Request | None = context.get("request")
    if not request:
        return False
    return bool(getattr(request.state, "is_authenticated", False))


def _maybe_set_csrf_cookie(request: Request, response: Response, settings: Settings) -> None:
    """Set ephemeral CSRF cookie if generated during request lifecycle."""
    new_csrf = getattr(request.state, "csrf_cookie_val", None)
    if new_csrf and not request.cookies.get(settings.csrf_cookie_name):
        response.set_cookie(
            key=settings.csrf_cookie_name,
            value=new_csrf,
            httponly=True,
            samesite=settings.cookie_samesite,  # type: ignore[arg-type]
            secure=settings.cookie_secure,
            max_age=86400,
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the POWER-GUI FastAPI application."""
    app_settings = settings or get_global_settings()

    app = FastAPI(
        title="POWER-GUI",
        description=f"Secure, accessible local-first web cockpit for P.O.W.E.R {POWER_VERSION}",
        version="0.6.1",
        docs_url=None,
        redoc_url=None,
    )

    base_dir = Path(__file__).parent
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"

    templates = Jinja2Templates(directory=str(templates_dir))
    templates.env.globals["t"] = pass_context(jinja_translate)
    templates.env.globals["csrf_token"] = pass_context(jinja_csrf_token)
    templates.env.globals["get_lang"] = get_request_lang
    templates.env.globals["get_theme"] = get_request_theme
    templates.env.globals["power_version"] = POWER_VERSION
    templates.env.globals["is_authenticated"] = pass_context(jinja_is_authenticated)

    app.state.templates = templates
    app.state.settings = app_settings

    # Mount static assets
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Authentication, Language & Theme guard middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next) -> Response:
        lang = get_request_lang(request)
        theme = get_request_theme(request)
        request.state.lang = lang
        request.state.theme = theme

        is_auth = False
        if not app_settings.auth_enabled:
            is_auth = True
        else:
            cookie = request.cookies.get(app_settings.session_cookie_name)
            if cookie:
                session_mgr = SessionManager(app_settings.secret_key)
                user_id = session_mgr.verify_session(cookie)
                if user_id:
                    is_auth = True

        request.state.is_authenticated = is_auth

        if app_settings.auth_enabled:
            path = request.url.path
            # Allow public assets, login, language switch, theme switch, and healthcheck
            if path in {"/login", "/healthz", "/set-lang", "/set-theme"} or path.startswith("/static/"):
                response = await call_next(request)
                _maybe_set_csrf_cookie(request, response, app_settings)
                return response

            if not is_auth:
                return RedirectResponse(url="/login", status_code=303)

        response = await call_next(request)
        _maybe_set_csrf_cookie(request, response, app_settings)
        return response

    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response


    # Register Routers
    app.include_router(dashboard_router)
    app.include_router(notes_router)
    app.include_router(search_router)
    app.include_router(graph_router)
    app.include_router(tasks_router)
    app.include_router(decisions_router)
    app.include_router(receipts_router)
    app.include_router(federation_router)
    app.include_router(auth_router)

    @app.get("/healthz")
    async def health_check() -> dict[str, str]:
        """Unauthenticated healthcheck endpoint for load balancers and container probes."""
        return {"status": "ok", "version": POWER_VERSION}

    return app



def main() -> None:
    """CLI entry point for running power-gui."""
    parser = argparse.ArgumentParser(description="P.O.W.E.R. GUI Web Cockpit")
    parser.add_argument("--host", default=None, help="Host interface to bind")
    parser.add_argument("--port", type=int, default=None, help="Port to bind")
    parser.add_argument("--vault", default=None, help="Path to Markdown knowledge vault")
    args = parser.parse_args()

    import uvicorn

    settings_kwargs = {}
    if args.host is not None:
        settings_kwargs["host"] = args.host
    if args.port is not None:
        settings_kwargs["port"] = args.port
    if args.vault is not None:
        settings_kwargs["vault_path"] = Path(args.vault)

    settings = Settings(**settings_kwargs)
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
