"""Bounded liveness/readiness identity contract."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from power_gui.app import create_app
from power_gui.config import Settings


def test_healthz_is_cheap_liveness_only(tmp_path: Path) -> None:
    app = create_app(Settings(vault_path=tmp_path, auth_enabled=False, cookie_secure=False))

    response = TestClient(app).get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": response.json()["version"]}


def test_readiness_returns_identity_and_custom_vault(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            vault_path=tmp_path,
            auth_enabled=True,
            admin_password="test-only-password",
            cookie_secure=False,
        )
    )

    response = TestClient(app).get("/readiness")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ready"
    assert payload["application_schema"] == "power.application.v2"
    assert payload["vault"]["configured"] is True
    assert payload["vault"]["exists"] is True
    assert str(tmp_path) not in response.text
    assert payload["auth_configured"] is True


def test_readiness_fails_closed_for_missing_auth_configuration(tmp_path: Path) -> None:
    app = create_app(Settings(vault_path=tmp_path, auth_enabled=True, cookie_secure=False))

    response = TestClient(app).get("/readiness")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "credentials" in response.json()["issues"][-1]


def test_readiness_fails_closed_for_missing_vault(tmp_path: Path) -> None:
    missing = tmp_path / "missing-vault"
    app = create_app(
        Settings(
            vault_path=missing,
            auth_enabled=False,
            cookie_secure=False,
        )
    )

    response = TestClient(app).get("/readiness")

    assert response.status_code == 503
    assert "vault" in response.json()["issues"][0]
