"""Configuration settings for POWER-GUI."""

from __future__ import annotations

import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Request
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from .clients.power import PowerClient


def _default_vault_path() -> Path:
    """Resolve default vault path across local dev, Docker, and environment variables."""
    for env_var in ("POWER_GUI_VAULT_PATH", "POWER_VAULT_DIR", "POWER_VAULT_PATH"):
        val = os.environ.get(env_var)
        if val:
            return Path(val).expanduser().resolve()
    if Path("/brain").exists():
        return Path("/brain")
    cwd_brain = Path.cwd() / "brain"
    if cwd_brain.exists():
        return cwd_brain
    return Path.cwd()


def _default_admin_password() -> str:

    """Resolve admin password supporting both standard and legacy environment variables."""
    return os.environ.get("POWER_GUI_ADMIN_PASSWORD") or os.environ.get("BRAIN_PORTAL_PASSWORD") or ""


class Settings(BaseSettings):
    """Fail-closed configuration settings for POWER-GUI application."""

    vault_path: Path = Field(
        default_factory=_default_vault_path,
        description="Path to the authoritative Markdown knowledge vault",
    )
    host: str = Field(default="127.0.0.1", description="Bind interface")
    port: int = Field(default=8080, ge=1, le=65535, description="Bind port")
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32),
        description="Secret key for signing sessions and CSRF tokens",
    )
    auth_enabled: bool = Field(
        default=True,
        description="Enable authentication requirements (redirects to /login)",
    )
    admin_password: str = Field(
        default_factory=_default_admin_password,
        description="Password for web access",
    )
    admin_password_hash: str | None = Field(
        default=None,
        description="Optional password hash for local web access",
    )

    session_cookie_name: str = "power_gui_session"
    csrf_cookie_name: str = "power_gui_csrf"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    max_upload_bytes: int = 5_000_000
    read_only_mode: bool = False
    federation_nodes: str = Field(
        default="",
        description="Optional JSON string of custom federated nodes to probe",
    )

    model_config = SettingsConfigDict(
        env_prefix="POWER_GUI_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_global_settings() -> Settings:
    """Return cached fallback global settings instance."""
    return Settings()


def get_settings(request: Request) -> Settings:
    """Get active Settings from current request app state."""
    return getattr(request.app.state, "settings", None) or get_global_settings()


def get_client(request: Request) -> PowerClient:
    """Get PowerClient instance using active application settings."""
    from .clients.power import PowerClient

    settings: Settings = get_settings(request)
    return PowerClient(settings.vault_path)


