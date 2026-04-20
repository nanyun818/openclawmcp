# Contributing

Thanks for helping improve OpenCLAW Lab Agent.

## Development Setup

This project currently uses only the Python standard library.

```powershell
python -m openclaw_lab_agent.cli list
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"
python -m pytest
```

## Design Principles

- Keep the agent tool surface small and auditable.
- Do not expose shell execution to public users.
- Keep generated experiment data outside the source tree.
- Prefer explicit JSON files for experiment artifacts.
- Keep deployment secrets in environment variables or private `.env` files.

## Pull Requests

Before opening a pull request:

- Run tests.
- Avoid committing `.env`, tokens, run artifacts, checkpoints, or logs.
- Keep changes focused.
- Update docs when adding commands, API endpoints, or deployment steps.

## Security-Sensitive Changes

Changes that affect authentication, command execution, file access, network access,
or MCP tool exposure should include a short security note in the pull request.

