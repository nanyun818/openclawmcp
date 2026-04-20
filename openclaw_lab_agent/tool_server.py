from __future__ import annotations

import json
import sys
from typing import Any, Callable

from . import mcp_tools


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
        response = handle_request(raw)
        sys.stdout.write(json.dumps(response, ensure_ascii=False, sort_keys=True) + "\n")
        sys.stdout.flush()


def handle_request(raw: str) -> dict[str, Any]:
    try:
        request = json.loads(raw.lstrip("\ufeff"))
        tool_name = request.get("tool")
        arguments = request.get("arguments", {})
        if tool_name == "tools/list":
            return {"ok": True, "result": mcp_tools.TOOL_SCHEMAS}
        if tool_name not in TOOLS:
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}
        if not isinstance(arguments, dict):
            return {"ok": False, "error": "arguments must be an object"}
        return {"ok": True, "result": TOOLS[tool_name](**arguments)}
    except Exception as exc:  # noqa: BLE001 - tool server must report failures as data.
        return {"ok": False, "error": str(exc)}


if __name__ == "__main__":
    main()
