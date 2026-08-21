"""Static suite-profile guardrails for the native and container GUI surfaces."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
POWER_SHA = "527cc8a77187e9fa6d724b604d1a6634545da575"
POWER_TAG_COMMIT = "6c6b6ae52f4b29382f0d2ec82fbb4e75ba1f471a"
GUI_TAG_COMMIT = "f1c918c7a8c6de011ff0553f08d00675ad296f59"


def test_native_service_is_user_scoped_loopback_and_opt_in() -> None:
    service = (ROOT / "power-gui.service").read_text(encoding="utf-8")
    assert "User=" not in service
    assert "Group=" not in service
    assert "WantedBy=default.target" in service
    assert "ExecStart=%h/.local/bin/power-gui" in service
    assert "--host 127.0.0.1" in service
    assert "Restart=on-failure" in service
    assert "Restart=always" not in service


def test_container_profile_is_pinned_non_root_and_health_checked() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert f"ARG POWER_FRAMEWORK_COMMIT={POWER_SHA}" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "POWER_GUI_HOST=0.0.0.0" in dockerfile
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert 'user: "10001:10001"' in compose
    assert "no-new-privileges:true" in compose
    assert "- ALL" in compose


def test_compatibility_manifest_does_not_claim_unpublished_digest() -> None:
    manifest = json.loads((ROOT / "compatibility.json").read_text(encoding="utf-8"))
    assert manifest["power_core"]["candidate_version"] == "3.6.6"
    assert manifest["power_core"]["dependency"]["revision"] == POWER_SHA
    assert manifest["power_core"]["dependency"]["tag_commit"] == POWER_TAG_COMMIT
    assert manifest["power_gui"]["release_tag_commit"] == GUI_TAG_COMMIT
    assert manifest["container"]["digest"] is None
    assert manifest["container"]["digest_status"] == "not_published_candidate"
