# Security Policy

OpenCLAW Lab Agent is an experimental research tool. Treat it as a control plane for
training workflows, not as a hardened multi-tenant platform.

## Supported Versions

Only the `main` branch is currently maintained.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if available, or contact the
maintainers privately before publishing details.

## Deployment Guidance

- Always set `OPENCLAW_LAB_TOKEN` for any network-accessible deployment.
- Keep the Python app bound to `127.0.0.1` behind Nginx.
- Use HTTPS for browser access.
- Do not commit `.env`, API tokens, SSH keys, training data, checkpoints, or logs.
- Prefer SSH keys over password login for production servers.
- Review MCP tool exposure carefully before connecting autonomous agents.

## Current Limitations

- The dashboard uses bearer-token authentication only.
- There is no per-user account model.
- The training runner defaults to mock mode.
- The MCP adapter is intended for local/trusted clients unless placed behind
  additional controls.

