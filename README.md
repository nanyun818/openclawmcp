# OpenCLAW Lab Agent

OpenCLAW Lab Agent is an experimental control plane for AI-assisted training workflows.
It gives a human or agent a small, auditable tool surface for creating experiment
configs, running training jobs, reading metrics, comparing runs, and generating
diagnostics.

The first version is dependency-free and uses Python's standard library only. The
`openclaw_lab_agent.mcp_tools` module is intentionally shaped like an MCP tool layer so
it can be wrapped by the official MCP SDK later.

## What It Does

- Creates versioned experiment folders.
- Stores config snapshots, status files, metrics, event logs, and diagnosis reports.
- Runs a safe mock training loop by default.
- Provides a token-protected Web/API dashboard.
- Provides MCP-style local tool adapters for agent integration.
- Deploys cleanly behind Nginx and HTTPS.

## Live Deployment Shape

Recommended production shape:

```text
Browser / Agent
  -> HTTPS / Nginx
  -> 127.0.0.1:8765 OpenCLAW Lab Agent
  -> /data/openclaw-lab-agent/runs
```

Keep the Python service bound to `127.0.0.1`; expose only Nginx publicly.

## Quick Start

```powershell
python -m openclaw_lab_agent.cli init-config
python -m openclaw_lab_agent.cli create --name baseline --config examples/base_config.json
python -m openclaw_lab_agent.cli run --run-id baseline
python -m openclaw_lab_agent.cli diagnose --run-id baseline
python -m openclaw_lab_agent.cli list
```

Experiment artifacts are written under `runs/`:

By default, generated artifacts are stored outside the source tree at
`D:\Codex\openclaw-lab-agent\runs` when the D drive exists. Override this with:

```powershell
$env:OPENCLAW_LAB_HOME="D:\Your\Preferred\Folder"
```

- `config.json`: the training configuration snapshot.
- `metrics.jsonl`: simulated step-by-step metrics.
- `events.log`: human-readable run events.
- `diagnosis.md`: generated diagnosis report.

## Current Tools

The tool layer exposes these functions:

- `list_experiments()`
- `create_experiment_config(name, config_path=None, overrides=None)`
- `validate_config(config)`
- `run_training(run_id, max_steps=None)`
- `get_training_status(run_id)`
- `read_metrics(run_id)`
- `compare_runs(run_ids)`
- `summarize_failure(run_id)`

## MCP-Style JSON-RPC Server

Run the JSON-RPC stdio adapter:

```powershell
python -m openclaw_lab_agent.mcp_stdio_server
```

Supported methods:

- `initialize`
- `tools/list`
- `tools/call`

See `docs/mcp-integration.md` for examples.

## Local Tool Server

For quick agent-style integration testing, the MVP includes a newline-delimited JSON
stdio tool server:

```powershell
'{"tool":"get_training_status","arguments":{"run_id":"baseline"}}' | python -m openclaw_lab_agent.tool_server
```

This is not a full MCP transport yet; it is the stable tool surface that the real MCP
adapter should wrap.

## Local Web/API Server

Run the minimal dashboard and API:

```powershell
python -m openclaw_lab_agent.web_server
```

Open `http://127.0.0.1:8765`.

To require an API token:

```powershell
$env:OPENCLAW_LAB_TOKEN="your-long-random-token"
python -m openclaw_lab_agent.web_server
```

API endpoints:

- `GET /health`
- `GET /api/experiments`
- `POST /api/experiments`
- `POST /api/compare`
- `POST /api/experiments/{run_id}/run`
- `POST /api/experiments/{run_id}/diagnose`
- `GET /api/experiments/{run_id}/metrics?tail=20`

## Deployment

See `docs/deploy-tencent-cloud.md` for the Ubuntu/Tencent Cloud deployment flow.
For the first phase, keep the service bound to `127.0.0.1` and access it through an
SSH tunnel instead of opening it directly to the public internet.

For `clawmcp.cloud`, see `docs/domain-clawmcp-cloud.md`.

## Real OpenCLAW Runner

Mock training is the default. To connect a real OpenCLAW command, see
`docs/openclaw-runner.md`.

## Packaging

Create a deployment zip on D drive:

```powershell
.\scripts\package.ps1
```

Upload the newest package to the Tencent Cloud server:

```powershell
.\scripts\upload.ps1
```

See `docs/package.md` for packaging options and exclusions.

## Project Direction

This MVP is the base for a larger OpenCLAW + MCP research assistant:

1. Replace mock training with a real OpenCLAW command runner.
2. Add an MCP server adapter around `mcp_tools`.
3. Add TensorBoard/W&B/JSONL metric ingestion.
4. Add a dashboard for experiment history and tool-call traces.
5. Generate tool-use fine-tuning data from successful workflows.
