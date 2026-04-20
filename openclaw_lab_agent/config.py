from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .paths import DEFAULT_CONFIG


Config = dict[str, Any]


def load_config(path: str | Path = DEFAULT_CONFIG) -> Config:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_config(config: Config, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, sort_keys=True)
        handle.write("\n")


def merge_overrides(config: Config, overrides: Config | None) -> Config:
    merged = copy.deepcopy(config)
    if not overrides:
        return merged
    _deep_merge(merged, overrides)
    return merged


def _deep_merge(target: Config, source: Config) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_merge(target[key], value)
        else:
            target[key] = value


def validate_config(config: Config) -> list[str]:
    errors: list[str] = []

    training = config.get("training", {})
    hardware = config.get("hardware", {})
    data = config.get("data", {})

    required_sections = ["model", "data", "training", "hardware", "safety"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")

    learning_rate = training.get("learning_rate")
    if not isinstance(learning_rate, (int, float)) or learning_rate <= 0:
        errors.append("training.learning_rate must be a positive number")
    elif learning_rate > 0.01:
        errors.append("training.learning_rate is unusually high and likely unstable")

    batch_size = training.get("batch_size")
    if not isinstance(batch_size, int) or batch_size <= 0:
        errors.append("training.batch_size must be a positive integer")

    max_steps = training.get("max_steps")
    if not isinstance(max_steps, int) or max_steps <= 0:
        errors.append("training.max_steps must be a positive integer")

    gpus = hardware.get("gpus")
    memory = hardware.get("gpu_memory_gb")
    if not isinstance(gpus, int) or gpus <= 0:
        errors.append("hardware.gpus must be a positive integer")
    if not isinstance(memory, (int, float)) or memory <= 0:
        errors.append("hardware.gpu_memory_gb must be a positive number")

    train_tokens = data.get("train_tokens")
    if not isinstance(train_tokens, int) or train_tokens <= 0:
        errors.append("data.train_tokens must be a positive integer")

    return errors


def estimate_training_hours(config: Config) -> float:
    training = config.get("training", {})
    hardware = config.get("hardware", {})
    data = config.get("data", {})

    max_steps = int(training.get("max_steps", 1))
    batch_size = int(training.get("batch_size", 1))
    grad_accum = int(training.get("gradient_accumulation_steps", 1))
    gpus = max(int(hardware.get("gpus", 1)), 1)
    tokens = int(data.get("train_tokens", 1))

    effective_batch = max(batch_size * grad_accum * gpus, 1)
    token_factor = min(tokens / 25_000_000, 20)
    step_factor = max_steps / 100
    throughput_factor = 1 / min(effective_batch / 32, 4)
    return round(max(0.05, 0.7 * token_factor * step_factor * throughput_factor), 2)

