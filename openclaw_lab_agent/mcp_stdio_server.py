from __future__ import annotations

import json
import sys
from typing import Any, Callable

from . import __version__, mcp_tools


TOOLS: dict[str, Callable[..., Any]] = {
    "list_experiments": mcp_tools.list_experiments,
    "create_experiment_config": mcp_tools.create_experiment_config,
    "validate_config": mcp_tools.validate_config,
    "run_training": mcp_tools.run_training,
    "get_training_status": mcp_tools.get_training_status,
    "read_metrics": mcp_tools.read_metrics,
    "compare_runs": mcp_tools.compare_runs,
    "summarize_failure": mcp_tools.summarize_failure,
}


def main() -> None:
    for raw in sys.stdin:
        if not raw.strip():
            continue
        response = handle_jsonrpc(raw)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")
            sys.stdout.flush()


def handle_jsonrpc(raw: str) -> dict[str, Any] | None:
    try:
        request = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError as exc:
        return _error(None, -32700, f"Parse error: {exc}")

    if isinstance(request, list):
        return _error(None, -32600, "Batch requests are not supported")

    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    try:
        if method == "notifications/initialized":
            return None
        if method == "initialize":
            return _result(request_id, initialize_result())
        if method == "tools/list":
            return _result(request_id, {"tools": to_mcp_tools()})
        if method == "tools/call":
            return _result(request_id, call_tool(params))
        return _error(request_id, -32601, f"Method not found: {method}")
    except Exception as exc:  # noqa: BLE001 - transport reports tool failures as JSON-RPC errors.
        return _error(request_id, -32000, str(exc))


def initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": "openclaw-lab-agent",
            "version": __version__,
        },
    }


def to_mcp_tools() -> list[dict[str, Any]]:
    tools = []
    for schema in mcp_tools.TOOL_SCHEMAS:
        tools.append(
            {
                "name": schema["name"],
                "description": schema["description"],
                "inputSchema": schema["input_schema"],
            }
        )
    return tools


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    if not isinstance(arguments, dict):
        raise ValueError("arguments must be an object")

    result = TOOLS[name](**arguments)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
            }
        ],
        "isError": False,
    }


def _result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    main()

