from __future__ import annotations

from openclaw_lab_agent.diagnostics import summarize_failure
from openclaw_lab_agent.experiments import compare_runs, create_experiment, run_training


def test_mock_training_workflow(tmp_path, monkeypatch):
    import openclaw_lab_agent.experiments as experiments
    import openclaw_lab_agent.paths as paths

    monkeypatch.setattr(paths, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(experiments, "RUNS_DIR", tmp_path / "runs", raising=False)

    created = create_experiment("Baseline Test")
    assert created["run_id"] == "baseline-test"

    completed = run_training("baseline-test", max_steps=8)
    assert completed["status"] == "completed"
    assert completed["steps"] == 8

    report = summarize_failure("baseline-test")
    assert report["run_id"] == "baseline-test"
    assert report["findings"]

    comparison = compare_runs(["baseline-test"])
    assert comparison["winner"] == "baseline-test"

