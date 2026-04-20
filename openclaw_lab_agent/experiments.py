from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Config, estimate_training_hours, load_config, merge_overrides, save_config, validate_config
from .paths import DEFAULT_CONFIG, ensure_runs_dir, run_dir
from .runner import run_external_training, runner_mode


@dataclass(frozen=True)
class Experiment:
    run_id: str
    path: Path
    status: str
    steps: int
    best_eval_loss: float | None


def create_experiment(name: str, config_path: str | Path | None = None, overrides: Config | None = None) -> dict[str, Any]:
    safe_name = _safe_run_id(name)
    target = run_dir(safe_name)
    if target.exists():
        raise ValueError(f"Experiment already exists: {safe_name}")

    base = load_config(config_path or DEFAULT_CONFIG)
    config = merge_overrides(base, overrides)
    errors = validate_config(config)
    if errors:
        raise ValueError("; ".join(errors))

    target.mkdir(parents=True)
    save_config(config, target / "config.json")
    _write_json(target / "status.json", {"status": "created", "run_id": safe_name, "created_at": _now()})
    _append_event(target, "created experiment")

    return {
        "run_id": safe_name,
        "status": "created",
        "config_path": str(target / "config.json"),
        "estimated_hours": estimate_training_hours(config),
    }


def list_experiments() -> list[dict[str, Any]]:
    ensure_runs_dir()
    experiments: list[dict[str, Any]] = []
    for path in sorted(ensure_runs_dir().iterdir()):
        if not path.is_dir():
            continue
        status = _read_json(path / "status.json", default={"status": "unknown"})
        metrics = read_metrics(path.name)
        best_eval = min((row["eval_loss"] for row in metrics if "eval_loss" in row), default=None)
        experiments.append(
            {
                "run_id": path.name,
                "status": status.get("status", "unknown"),
                "steps": len(metrics),
                "best_eval_loss": best_eval,
            }
        )
    return experiments


def run_training(run_id: str, max_steps: int | None = None) -> dict[str, Any]:
    target = run_dir(run_id)
    if not target.exists():
        raise ValueError(f"Unknown experiment: {run_id}")

    config = load_config(target / "config.json")
    errors = validate_config(config)
    if errors:
        raise ValueError("; ".join(errors))

    if runner_mode() == "external":
        _write_json(target / "status.json", {"status": "running", "run_id": run_id, "started_at": _now()})
        _append_event(target, "started external training")
        external = run_external_training(run_id, target, config)
        metrics = read_metrics(run_id)
        best_eval = min((row["eval_loss"] for row in metrics if "eval_loss" in row), default=None)
        final_eval = metrics[-1].get("eval_loss") if metrics else None
        status = {
            "status": "completed",
            "run_id": run_id,
            "runner": "external",
            "completed_at": _now(),
            "steps": len(metrics),
            "best_eval_loss": best_eval,
            "final_eval_loss": final_eval,
        }
        _write_json(target / "status.json", status)
        _append_event(target, f"completed external training; best_eval_loss={best_eval}")
        return {**external, "steps": len(metrics), "best_eval_loss": best_eval}

    if runner_mode() != "mock":
        raise ValueError(f"Unknown runner mode: {runner_mode()}")

    configured_steps = int(config["training"]["max_steps"])
    steps = max_steps or configured_steps
    steps = min(steps, configured_steps)

    _write_json(target / "status.json", {"status": "running", "run_id": run_id, "started_at": _now()})
    _append_event(target, f"started mock training for {steps} steps")

    seed = int(config["training"].get("seed", 42))
    lr = float(config["training"]["learning_rate"])
    rng = random.Random(seed)
    metrics_path = target / "metrics.jsonl"

    base_loss = 3.4 + rng.random() * 0.3
    instability = max(0.0, (lr - 0.0008) * 900)

    with metrics_path.open("w", encoding="utf-8") as handle:
        for step in range(1, steps + 1):
            progress = step / steps
            train_loss = base_loss * math.exp(-2.2 * progress) + 0.55
            train_loss += rng.uniform(-0.03, 0.03) + instability * progress

            eval_loss = train_loss + 0.1 + rng.uniform(-0.025, 0.04)
            if step > steps * 0.72 and lr > 0.0006:
                eval_loss += (progress - 0.72) * 0.35

            gpu_utilization = max(25, min(98, 72 + rng.randint(-12, 16)))
            if int(config["training"].get("batch_size", 1)) <= 2:
                gpu_utilization -= 20

            row = {
                "step": step,
                "train_loss": round(train_loss, 4),
                "eval_loss": round(eval_loss, 4),
                "learning_rate": lr,
                "gpu_utilization": gpu_utilization,
                "tokens_seen": step * int(config["training"]["batch_size"]) * 2048,
                "time": _now(),
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            if steps <= 20:
                time.sleep(0.005)

    metrics = read_metrics(run_id)
    final = metrics[-1]
    best_eval = min(row["eval_loss"] for row in metrics)

    _write_json(
        target / "status.json",
        {
            "status": "completed",
            "run_id": run_id,
            "completed_at": _now(),
            "steps": steps,
            "best_eval_loss": best_eval,
            "final_eval_loss": final["eval_loss"],
        },
    )
    _append_event(target, f"completed mock training; best_eval_loss={best_eval}")

    return {"run_id": run_id, "status": "completed", "steps": steps, "best_eval_loss": best_eval}


def get_status(run_id: str) -> dict[str, Any]:
    target = run_dir(run_id)
    if not target.exists():
        raise ValueError(f"Unknown experiment: {run_id}")
    status = _read_json(target / "status.json", default={"status": "unknown", "run_id": run_id})
    status["metrics_count"] = len(read_metrics(run_id))
    return status


def read_metrics(run_id: str) -> list[dict[str, Any]]:
    metrics_path = run_dir(run_id) / "metrics.jsonl"
    if not metrics_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    with metrics_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def compare_runs(run_ids: list[str]) -> dict[str, Any]:
    summaries = []
    for run_id in run_ids:
        metrics = read_metrics(run_id)
        if not metrics:
            summaries.append({"run_id": run_id, "status": "no_metrics"})
            continue
        summaries.append(
            {
                "run_id": run_id,
                "status": get_status(run_id).get("status", "unknown"),
                "steps": len(metrics),
                "best_eval_loss": min(row["eval_loss"] for row in metrics),
                "final_eval_loss": metrics[-1]["eval_loss"],
                "avg_gpu_utilization": round(sum(row["gpu_utilization"] for row in metrics) / len(metrics), 1),
            }
        )

    completed = [row for row in summaries if "best_eval_loss" in row]
    winner = min(completed, key=lambda row: row["best_eval_loss"])["run_id"] if completed else None
    return {"runs": summaries, "winner": winner}


def _safe_run_id(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "-" for char in name.strip().lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        raise ValueError("Experiment name cannot be empty")
    return cleaned[:80]


def _append_event(target: Path, message: str) -> None:
    with (target / "events.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{_now()} {message}\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
