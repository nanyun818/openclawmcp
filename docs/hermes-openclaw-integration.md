# Hermes Agent + OpenClaw Integration

This project can track OpenClaw Gateway and Hermes Agent as external runtimes.

The first integration is intentionally read-only:

- Check whether a runtime is configured.
- Check whether its local URL is reachable.
- Run a safe status command when configured.
- Expose the status through Web/API/MCP tools.

It does not start long-running agents or expose high-risk tools by default.

## Local Hermes Agent

Your local Hermes launcher is:

```powershell
cd C:\Users\Zhangxu669090\Documents\Codex\2026-04-21-hermes-agent
.\run-hermes.ps1
```

Your local Hermes status command is:

```powershell
cd C:\Users\Zhangxu669090\Documents\Codex\2026-04-21-hermes-agent
.\hermes-status.ps1
```

To let OpenCLAW MCP check Hermes status on Windows, set:

```powershell
$env:HERMAS_COMMAND='powershell -ExecutionPolicy Bypass -File C:\Users\Zhangxu669090\Documents\Codex\2026-04-21-hermes-agent\hermes-status.ps1'
python -m openclaw_lab_agent.web_server
```

The environment variable keeps the original `HERMAS_*` spelling for compatibility, but
the UI labels it as Hermes Agent.

## Server Deployment Note

`clawmcp.cloud` runs on Tencent Cloud Linux. It cannot directly execute a Windows local
PowerShell script unless you add a tunnel, VPN, or install Hermes on the server too.

Recommended options:

1. Install Hermes on the server and configure a Linux status command.
2. Keep Hermes local and expose only a narrow health endpoint through Tailscale.
3. Keep Hermes local-only and use OpenCLAW MCP as the public experiment dashboard.

## Environment Variables

OpenClaw Gateway:

```bash
OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789
OPENCLAW_GATEWAY_HEALTH_PATH=/
OPENCLAW_COMMAND='openclaw status'
```

Hermes Agent:

```bash
HERMAS_URL=http://127.0.0.1:9000
HERMAS_HEALTH_PATH=/health
HERMAS_COMMAND='hermes status'
```

`HERMES_COMMAND` is also accepted as an alias.

## API

```text
GET /api/integrations
GET /api/integrations/openclaw
GET /api/integrations/hermas
GET /api/integrations/hermes
```

## MCP Tools

- `list_runtime_integrations`
- `check_runtime_integration`

Example tool argument:

```json
{"name": "hermes"}
```

