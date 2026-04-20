# Real OpenCLAW Runner

The default runner is safe mock mode:

```bash
OPENCLAW_LAB_RUNNER=mock
```

To connect a real training command, set:

```bash
OPENCLAW_LAB_RUNNER=external
OPENCLAW_TRAIN_COMMAND='python3 /path/to/train.py --config {config} --output {run_dir}'
```

Available placeholders:

- `{run_id}`
- `{run_dir}`
- `{config}`
- `{metrics}`

The command should write metrics to:

```text
{metrics}
```

as JSONL rows with fields like:

```json
{"step": 1, "train_loss": 2.3, "eval_loss": 2.5, "gpu_utilization": 80, "tokens_seen": 4096}
```

If the command succeeds but does not write metrics, the runner writes a minimal placeholder
metric so the dashboard can still show the run as completed.

## Safety

External runner mode executes a shell command. Only enable it on a trusted server with a
private token and controlled command template. Do not expose arbitrary command editing in
the browser.

