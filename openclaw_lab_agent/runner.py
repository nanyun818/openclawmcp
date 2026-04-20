from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from .config import Config


RUNNER_MODE_ENV = "OPENCLAW_LAB_RUNNER"
COMMAND_TEMPLATE_ENV = "OPENCLAW_TRAIN_COMMAND"


def runner_mode() -> str:
    return os.environ.get(RUNNER_MODE_ENV, "mock").strip().lower() or "mock"


def run_external_training(run_id: str, run_path: Path, config: Config) -> dict[str, Any]:
    template = os.environ.get(COMMAND_TEMPLATE_ENV)
    if not template:
        raise ValueError(f"{COMMAND_TEMPLATE_ENV} is required when {RUNNER_MODE_ENV}=external")

    config_path = run_path / "config.json"
    metrics_path = run_path / "metrics.jsonl"
    command = template.format(
        run_id=run_id,
        run_dir=str(run_path),
        config=str(config_path),
        metrics=str(metrics_path),
    )

    started_at = _now()
    with (run_path / "external.stdout.log").open("w", encoding="utf-8") as stdout:
        process = subprocess.run(
            command,
            cwd=str(run_path),
            shell=True,
            text=True,
            stdout=stdout,
            stderr=subprocess.STDOUT,
            timeout=int(config.get("safety", {}).get("max_seconds", 7200)),
            check=False,
        )

    if process.returncode != 0:
        raise RuntimeError(f"External training failed with exit code {process.returncode}")

    if not metrics_path.exists():
        _write_minimal_metrics(metrics_path)

    return {
        "run_id": run_id,
        "status": "completed",
        "runner": "external",
        "started_at": started_at,
        "completed_at": _now(),
    }


def _write_minimal_metrics(path: Path) -> None:
    row = {
        "step": 1,
        "train_loss": 0.0,
        "eval_loss": 0.0,
        "learning_rate": 0.0,
        "gpu_utilization": 0,
        "tokens_seen": 0,
        "time": _now(),
    }
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")

