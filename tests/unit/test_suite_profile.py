"""Static suite-profile guardrails for the native and container GUI surfaces."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
POWER_SHA = "a70ecbba880a3e9d13e7cdac3b729987169a8d13"


def test_native_service_is_user_scoped_loopback_and_opt_in() -> None:
    service = (ROOT / "power-gui.service").read_text(encoding="utf-8")
    assert "User=" not in service
    assert "Group=" not in service
    assert "WantedBy=default.target" in service
    assert "ExecStart=%h/.local/bin/power-gui" in service
    assert "--vault" not in service
    assert "EnvironmentFile=-%h/.config/power-gui.env" in service
    assert "Restart=on-failure" in service
    assert "Restart=always" not in service


def test_container_profile_is_pinned_non_root_and_health_checked() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert f"ARG POWER_FRAMEWORK_COMMIT={POWER_SHA}" in dockerfile
    assert "COPY release/power-suite.constraints.txt /app/power-suite.constraints.txt" in dockerfile
    assert "--constraint /app/power-suite.constraints.txt" in dockerfile
    constraints = (ROOT / "release" / "power-suite.constraints.txt").read_bytes()
    assert hashlib.sha256(constraints).hexdigest() == "7f44b449a46b784083ded0b7b94c99c6a26f090759a6ae5a12674146982a7eca"
    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "POWER_GUI_HOST=0.0.0.0" in dockerfile
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert 'user: "10001:10001"' in compose
    assert "no-new-privileges:true" in compose
    assert "- ALL" in compose


def test_compatibility_manifest_does_not_claim_unpublished_digest() -> None:
    manifest = json.loads((ROOT / "compatibility.json").read_text(encoding="utf-8"))
    assert manifest["power_core"]["candidate_version"] == "3.7.2"
    assert manifest["power_core"]["dependency"]["revision"] == POWER_SHA
    assert manifest["power_core"]["dependency"]["tag"] == "v3.7.2"
    assert manifest["power_core"]["candidate_publication_required"] is True
    assert manifest["power_gui"]["version"] == "0.7.8"
    assert manifest["power_gui"]["release_tag"] is None
    assert manifest["container"]["digest"] is None
    assert manifest["container"]["digest_status"] == "not_published"


def test_accessibility_profile_has_focus_motion_and_form_guardrails() -> None:
    css = (ROOT / "src/power_gui/static/css/style.css").read_text(encoding="utf-8")
    base = (ROOT / "src/power_gui/templates/base.html").read_text(encoding="utf-8")
    graph = (ROOT / "src/power_gui/templates/graph.html").read_text(encoding="utf-8")
    search = (ROOT / "src/power_gui/templates/search.html").read_text(encoding="utf-8")
    decisions = (ROOT / "src/power_gui/templates/decisions.html").read_text(encoding="utf-8")

    assert "transition: all" not in css
    assert "prefers-reduced-motion: reduce" in css
    assert ".skip-link" in base and 'id="main-content" tabindex="-1"' in base
    assert "outline: none" not in base
    for control_id in ("graphSearchInput", "graphCategorySelect", "graphDegreeSelect"):
        assert f'for="{control_id}"' in graph
    assert 'for="searchQuery"' in search and 'id="searchQuery"' in search
    assert 'for="decisionInputValue"' in decisions and 'id="decisionInputValue"' in decisions
