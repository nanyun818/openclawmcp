from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_config, save_config
from .diagnostics import summarize_failure
from .experiments import compare_runs, create_experiment, get_status, list_experiments, read_metrics, run_training
from .mcp_tools import TOOL_SCHEMAS
from .paths import DEFAULT_CONFIG


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenCLAW Lab Agent MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-config", help="Create the example base config if needed")

    create = subparsers.add_parser("create", help="Create an experiment")
    create.add_argument("--name", required=True)
    create.add_argument("--config", default=str(DEFAULT_CONFIG))
    create.add_argument("--override", action="append", default=[], help="JSON object merged into config")

    run = subparsers.add_parser("run", help="Run mock training")
    run.add_argument("--run-id", required=True)
    run.add_argument("--max-steps", type=int)

    status = subparsers.add_parser("status", help="Show run status")
    status.add_argument("--run-id", required=True)

    metrics = subparsers.add_parser("metrics", help="Print run metrics")
    metrics.add_argument("--run-id", required=True)
    metrics.add_argument("--tail", type=int, default=5)

    diagnose = subparsers.add_parser("diagnose", help="Generate a diagnosis report")
    diagnose.add_argument("--run-id", required=True)

    compare = subparsers.add_parser("compare", help="Compare runs")
    compare.add_argument("run_ids", nargs="+")

    subparsers.add_parser("list", help="List experiments")
    subparsers.add_parser("tools", help="Print MCP-style tool schemas")

    args = parser.parse_args()
    result = dispatch(args)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))


def dispatch(args: argparse.Namespace) -> Any:
    if args.command == "init-config":
        config = load_config(DEFAULT_CONFIG)
        save_config(config, DEFAULT_CONFIG)
        return {"status": "ok", "config_path": str(DEFAULT_CONFIG)}

    if args.command == "create":
        overrides: dict[str, Any] = {}
        for raw in args.override:
            _deep_merge(overrides, json.loads(raw))
        return create_experiment(args.name, Path(args.config), overrides)

    if args.command == "run":
        return run_training(args.run_id, args.max_steps)

    if args.command == "status":
        return get_status(args.run_id)

    if args.command == "metrics":
        rows = read_metrics(args.run_id)
        return {"run_id": args.run_id, "count": len(rows), "metrics": rows[-args.tail :]}

    if args.command == "diagnose":
        return summarize_failure(args.run_id)

    if args.command == "compare":
        return compare_runs(args.run_ids)

    if args.command == "list":
        return list_experiments()

    if args.command == "tools":
        return TOOL_SCHEMAS

    raise ValueError(f"Unknown command: {args.command}")


def _deep_merge(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


if __name__ == "__main__":
    main()

