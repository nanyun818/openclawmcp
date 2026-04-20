# MCP Integration

OpenCLAW Lab Agent exposes a stable Python tool layer in:

```text
openclaw_lab_agent/mcp_tools.py
```

The dependency-free stdio adapter is:

```bash
python -m openclaw_lab_agent.mcp_stdio_server
```

It accepts newline-delimited JSON-RPC messages and supports:

- `initialize`
- `tools/list`
- `tools/call`

## Example

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' \
  | python -m openclaw_lab_agent.mcp_stdio_server
```

Tool call example:

```bash
printf '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_experiments","arguments":{}}}\n' \
  | python -m openclaw_lab_agent.mcp_stdio_server
```

## Tool Surface

- `list_experiments`
- `create_experiment_config`
- `validate_config`
- `run_training`
- `get_training_status`
- `read_metrics`
- `compare_runs`
- `summarize_failure`

## Security

Use this adapter for local or trusted agent clients first. Before exposing it to a
remote agent runtime, add transport-level authentication, tool-call auditing, and
approval gates for any tool that can trigger expensive work.

## Next Step

When third-party dependencies are acceptable, wrap `mcp_tools.py` with the official MCP
SDK transport while keeping the tool function names and schemas stable.

