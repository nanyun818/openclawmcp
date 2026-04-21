from __future__ import annotations

from typing import Any

from .config import Config, estimate_training_hours, load_config, validate_config as validate_config_core
from .diagnostics import summarize_failure as summarize_failure_core
from .experiments import compare_runs as compare_runs_core
from .experiments import create_experiment, get_status, list_experiments as list_experiments_core
from .experiments import read_metrics as read_metrics_core
from .experiments import run_training as run_training_core
from .integrations import check_integration as check_integration_core
from .integrations import list_integrations as list_integrations_core


def list_experiments() -> list[dict[str, Any]]:
    return list_experiments_core()


def create_experiment_config(
    name: str,
    config_path: str | None = None,
    overrides: Config | None = None,
) -> dict[str, Any]:
    return create_experiment(name=name, config_path=config_path, overrides=overrides)


def validate_config(config: Config | None = None, config_path: str | None = None) -> dict[str, Any]:
    loaded = config or load_config(config_path)  # type: ignore[arg-type]
    errors = validate_config_core(loaded)
    return {"valid": not errors, "errors": errors, "estimated_hours": estimate_training_hours(loaded)}


def run_training(run_id: str, max_steps: int | None = None) -> dict[str, Any]:
    return run_training_core(run_id=run_id, max_steps=max_steps)


def get_training_status(run_id: str) -> dict[str, Any]:
    return get_status(run_id)


def read_metrics(run_id: str) -> dict[str, Any]:
    rows = read_metrics_core(run_id)
    return {"run_id": run_id, "count": len(rows), "metrics": rows}


def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    return compare_runs_core(run_ids)


def summarize_failure(run_id: str) -> dict[str, Any]:
    return summarize_failure_core(run_id)


def list_runtime_integrations() -> dict[str, Any]:
    return list_integrations_core()


def check_runtime_integration(name: str) -> dict[str, Any]:
    return check_integration_core(name)


TOOL_SCHEMAS = [
    {
        "name": "list_experiments",
        "description": "List known OpenCLAW experiment runs and their current status.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "create_experiment_config",
        "description": "Create a validated experiment config snapshot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "config_path": {"type": "string"},
                "overrides": {"type": "object"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "run_training",
        "description": "Run the mock training loop for an experiment.",
        "input_schema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}, "max_steps": {"type": "integer"}},
            "required": ["run_id"],
        },
    },
    {
        "name": "summarize_failure",
        "description": "Generate a training diagnosis report from metrics.",
        "input_schema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}},
            "required": ["run_id"],
        },
    },
    {
        "name": "list_runtime_integrations",
        "description": "List configured OpenClaw/Hermas runtime integrations and reachability.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "check_runtime_integration",
        "description": "Check one runtime integration by name, such as openclaw or hermas.",
        "input_schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
]
