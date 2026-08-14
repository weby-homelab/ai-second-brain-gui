"""Read-only Federation status, fleet live health probe, and A2A discovery route."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import power_framework
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from ..clients.power import PowerClient
from ..config import Settings, get_client, get_settings

if TYPE_CHECKING:
    from fastapi.templating import Jinja2Templates

router = APIRouter()

FLEET_TOPOLOGY: list[dict[str, Any]] = [
    {
        "node_id": "local-core",
        "role": "Home Core (PRXMX-01)",
        "host": "100.86.120.114",
        "port": 22,
        "endpoint": "100.86.120.114:22",
        "authority": "authoritative",
        "vault_id_type": "primary",
    },
    {
        "node_id": "docker-plane",
        "role": "Application Plane (LXC 200)",
        "host": "100.124.218.39",
        "port": 8008,
        "endpoint": "100.124.218.39:8008",
        "authority": "operator-cockpit",
        "vault_id_type": "mounted",
    },
    {
        "node_id": "remote-ws",
        "role": "AI Workstation (WS)",
        "host": "100.68.179.109",
        "port": 22,
        "endpoint": "100.68.179.109:22",
        "authority": "agent-executor",
        "vault_id_type": "compute-node",
    },
    {
        "node_id": "edge-htznr",
        "role": "Remote Edge & VPN (HTZNR)",
        "host": "46.224.186.236",
        "port": 443,
        "endpoint": "46.224.186.236:443",
        "authority": "egress-mirror",
        "vault_id_type": "edge-proxy",
    },
    {
        "node_id": "backup-pve02",
        "role": "Backup & Replica (PRXMX-02)",
        "host": "100.122.16.1",
        "port": 8006,
        "endpoint": "100.122.16.1:8006",
        "authority": "cold-storage",
        "vault_id_type": "replica-vault",
    },
]


async def _probe_node(node: dict[str, Any], vault_id: str, total_notes: int) -> dict[str, Any]:
    """Asynchronously probe TCP port with low timeout and measure latency."""
    host = str(node["host"])
    port = int(node["port"])
    t0 = time.perf_counter()
    status = "unreachable"
    latency_ms: float | None = None

    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=0.8)
        writer.close()
        await writer.wait_closed()
        status = "online"
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    except Exception:
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    node_vault_id = vault_id if node["vault_id_type"] in {"primary", "mounted"} else str(node["vault_id_type"])
    notes_count = total_notes if node["vault_id_type"] in {"primary", "mounted"} else "-"

    return {
        "node_id": node["node_id"],
        "role": node["role"],
        "endpoint": node["endpoint"],
        "status": status,
        "latency_ms": latency_ms,
        "vault_id": node_vault_id,
        "notes_count": notes_count,
        "trust_level": node["authority"],
    }


@router.get("/federation", response_class=HTMLResponse)
async def federation_view(
    request: Request,
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    """Render federated nodes status and multi-vault search cockpit with live probe."""
    templates: Jinja2Templates = request.app.state.templates

    discovery = client.discover()
    stats = client.get_source_stats()

    # Parallel asynchronous health probing across the entire Weby Homelab fleet
    nodes = await asyncio.gather(
        *(_probe_node(n, vault_id=stats.vault_id, total_notes=stats.total_notes) for n in FLEET_TOPOLOGY)
    )

    return templates.TemplateResponse(
        request=request,
        name="federation.html",
        context={
            "nodes": nodes,
            "discovery": discovery.data,
            "stats": stats,
            "settings": settings,
        },
    )


@router.get("/federation/agent.json", response_class=JSONResponse)
@router.get("/.well-known/agent.json", response_class=JSONResponse)
async def a2a_agent_card(
    client: PowerClient = Depends(get_client),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """A2A 1.0.1 standardized Agent Card for autonomous agent discovery."""
    stats = client.get_source_stats()
    discovery = client.discover()
    power_version = getattr(power_framework, "__version__", "3.6.0")

    card = {
        "schema_version": "1.0.1",
        "protocol": "A2A",
        "name": "Weby Homelab Second Brain Cockpit",
        "node_id": "local-core",
        "vault_id": stats.vault_id,
        "authority": "authoritative",
        "framework": {
            "name": "P.O.W.E.R",
            "version": power_version,
        },
        "capabilities": [
            "power.search",
            "power.source.read",
            "power.source.list",
            "power.source.stats",
            "power.task.status",
            "power.graph",
        ],
        "discovery": discovery.data,
        "security": {
            "auth_required": settings.auth_enabled,
            "encryption": "Tailscale WireGuard / TLS",
            "fail_closed": True,
            "read_only": True,
        },
    }
    return JSONResponse(content=card)
