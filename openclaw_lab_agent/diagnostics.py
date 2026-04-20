from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import load_config
from .experiments import read_metrics
from .paths import run_dir


def summarize_failure(run_id: str) -> dict[str, Any]:
    target = run_dir(run_id)
    if not target.exists():
        raise ValueError(f"Unknown experiment: {run_id}")

    config = load_config(target / "config.json")
    metrics = read_metrics(run_id)
    if not metrics:
        report = {
            "run_id": run_id,
            "status": "no_metrics",
            "findings": ["No metrics were found. Run training before diagnosis."],
            "recommendations": ["Start a training run or check whether the metrics path is configured correctly."],
        }
        _write_report(target / "diagnosis.md", report)
        return report

    findings: list[str] = []
    recommendations: list[str] = []

    first = metrics[0]
    final = metrics[-1]
    best_eval = min(row["eval_loss"] for row in metrics)
    best_step = min(metrics, key=lambda row: row["eval_loss"])["step"]
    avg_gpu = sum(row["gpu_utilization"] for row in metrics) / len(metrics)

    if final["train_loss"] > first["train_loss"] * 0.95:
        findings.append("Training loss barely improved from the first step.")
        recommendations.append("Lower the learning rate, inspect data formatting, or verify labels/objectives.")

    if final["eval_loss"] > best_eval * 1.05 and best_step < final["step"]:
        findings.append("Eval loss regressed after the best checkpoint, suggesting overfitting or instability.")
        recommendations.append("Keep the best checkpoint, add early stopping, or reduce the learning rate.")

    if avg_gpu < 55:
        findings.append("Average GPU utilization is low.")
        recommendations.append("Increase batch size, tune dataloader workers, or inspect CPU/input pipeline bottlenecks.")

    lr = float(config["training"]["learning_rate"])
    if lr > 0.0008:
        findings.append("Learning rate is high for a small-model fine-tuning run.")
        recommendations.append("Try 1e-4 to 3e-4 as a safer sweep range.")

    if not findings:
        findings.append("No obvious failure pattern was detected in the mock metrics.")
        recommendations.append("Compare against another run or inspect sample-level evaluation errors next.")

    report = {
        "run_id": run_id,
        "status": "diagnosed",
        "summary": {
            "steps": len(metrics),
            "first_train_loss": first["train_loss"],
            "final_train_loss": final["train_loss"],
            "best_eval_loss": best_eval,
            "best_step": best_step,
            "avg_gpu_utilization": round(avg_gpu, 1),
        },
        "findings": findings,
        "recommendations": recommendations,
    }
    _write_report(target / "diagnosis.md", report)
    return report


def _write_report(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# Diagnosis: {report['run_id']}",
        "",
        f"Status: {report['status']}",
        "",
    ]
    summary = report.get("summary")
    if summary:
        lines.extend(["## Summary", ""])
        for key, value in summary.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

    lines.extend(["## Findings", ""])
    for item in report["findings"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Recommendations", ""])
    for item in report["recommendations"]:
        lines.append(f"- {item}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

