from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class IntegrationConfig:
    name: str
    label: str
    url_env: str
    default_url: str | None
    health_path_env: str
    default_health_path: str
    command_env: str


INTEGRATIONS = [
    IntegrationConfig(
        name="openclaw",
        label="OpenClaw Gateway",
        url_env="OPENCLAW_GATEWAY_URL",
        default_url="http://127.0.0.1:18789",
        health_path_env="OPENCLAW_GATEWAY_HEALTH_PATH",
        default_health_path="/",
        command_env="OPENCLAW_COMMAND",
    ),
    IntegrationConfig(
        name="hermas",
        label="Hermes Agent",
        url_env="HERMAS_URL",
        default_url=None,
        health_path_env="HERMAS_HEALTH_PATH",
        default_health_path="/health",
        command_env="HERMAS_COMMAND",
    ),
]


def list_integrations() -> dict[str, Any]:
    return {"integrations": [check_integration(config.name) for config in INTEGRATIONS]}


def check_integration(name: str) -> dict[str, Any]:
    config = _get_config(name)
    url = os.environ.get(config.url_env, config.default_url or "").strip()
    command = os.environ.get(config.command_env, "").strip()
    if config.name == "hermas" and not command:
        command = os.environ.get("HERMES_COMMAND", "").strip()
    health_path = os.environ.get(config.health_path_env, config.default_health_path).strip() or "/"

    result: dict[str, Any] = {
        "name": config.name,
        "label": config.label,
        "configured": bool(url or command),
        "url": url or None,
        "command": command or None,
        "status": "not_configured",
        "checks": [],
    }

    if url:
        result["checks"].append(check_http(url, health_path))
    if command:
        result["checks"].append(check_command(command))

    checks = result["checks"]
    if checks and any(check["ok"] for check in checks):
        result["status"] = "reachable"
    elif checks:
        result["status"] = "unreachable"

    return result


def check_http(base_url: str, health_path: str) -> dict[str, Any]:
    target = base_url.rstrip("/") + "/" + health_path.lstrip("/")
    started = time.time()
    try:
        request = Request(target, headers={"User-Agent": "openclaw-lab-agent/0.1"})
        with urlopen(request, timeout=2) as response:
            body = response.read(256).decode("utf-8", errors="replace")
            return {
                "type": "http",
                "ok": 200 <= response.status < 500,
                "target": target,
                "status_code": response.status,
                "latency_ms": round((time.time() - started) * 1000),
                "preview": body,
            }
    except URLError as exc:
        return {
            "type": "http",
            "ok": False,
            "target": target,
            "error": str(exc.reason),
            "latency_ms": round((time.time() - started) * 1000),
        }
    except Exception as exc:  # noqa: BLE001 - status endpoint should report failures as data.
        return {
            "type": "http",
            "ok": False,
            "target": target,
            "error": str(exc),
            "latency_ms": round((time.time() - started) * 1000),
        }


def check_command(command: str) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=5,
            check=False,
        )
        return {
            "type": "command",
            "ok": completed.returncode == 0,
            "command": command,
            "exit_code": completed.returncode,
            "latency_ms": round((time.time() - started) * 1000),
            "preview": completed.stdout[:500],
        }
    except Exception as exc:  # noqa: BLE001 - status endpoint should report failures as data.
        return {
            "type": "command",
            "ok": False,
            "command": command,
            "error": str(exc),
            "latency_ms": round((time.time() - started) * 1000),
        }


def _get_config(name: str) -> IntegrationConfig:
    if name == "hermes":
        name = "hermas"
    for config in INTEGRATIONS:
        if config.name == name:
            return config
    raise ValueError(f"Unknown integration: {name}")
