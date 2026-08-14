"""FastAPI application factory and server entry point for POWER-GUI."""

from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Settings, get_global_settings
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


def create_app(settings: Settings | None = None) -> FastAPI:
    """Instantiate and configure the POWER-GUI FastAPI application."""
    app_settings = settings or get_global_settings()

    app = FastAPI(
        title="POWER-GUI",
        description="Secure, accessible local-first web cockpit for P.O.W.E.R 3.7",
        version="0.5.0",
        docs_url=None,
        redoc_url=None,
    )

    base_dir = Path(__file__).parent
    templates_dir = base_dir / "templates"
    static_dir = base_dir / "static"

    templates = Jinja2Templates(directory=str(templates_dir))
    app.state.templates = templates
    app.state.settings = app_settings

    # Mount static assets
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
