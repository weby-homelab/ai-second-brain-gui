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


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the POWER-GUI FastAPI application."""
    app_settings = settings or get_global_settings()

    app = FastAPI(
        title="POWER-GUI",
        description=f"Secure, accessible local-first web cockpit for P.O.W.E.R {POWER_VERSION}",
        version="0.5.4",
        docs_url=None,
        redoc_url=None,
    )

    base_dir = Path(__file__).parent
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"

    templates = Jinja2Templates(directory=str(templates_dir))
    templates.env.globals["t"] = pass_context(jinja_translate)
    templates.env.globals["get_lang"] = get_request_lang
    templates.env.globals["get_theme"] = get_request_theme
    templates.env.globals["power_version"] = POWER_VERSION

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

        if app_settings.auth_enabled:
            path = request.url.path
            # Allow public assets, login, language switch, theme switch, and healthcheck
            if path in {"/login", "/healthz", "/set-lang", "/set-theme"} or path.startswith("/static/"):
                return await call_next(request)

            cookie = request.cookies.get(app_settings.session_cookie_name)
            if not cookie:
                return RedirectResponse(url="/login", status_code=303)

            session_mgr = SessionManager(app_settings.secret_key)
            user_id = session_mgr.verify_session(cookie)
            if not user_id:
                return RedirectResponse(url="/login", status_code=303)

        return await call_next(request)

    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
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

    return app


def main() -> None:
    """CLI entry point for running power-gui."""
    parser = argparse.ArgumentParser(description="POWER-GUI Web Cockpit")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument("--vault", default="/root/geminicli/brain", help="Path to Markdown vault")
    args = parser.parse_args()

    import uvicorn

    settings = Settings(host=args.host, port=args.port, vault_path=Path(args.vault))
    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
