# Clean OpenClaw Runtime

Use this when a local Windows OpenClaw state is hard to repair or when you want a clean
server-side runtime for integration testing.

This flow does not delete existing OpenClaw data. It creates a separate runtime under:

```text
/data/openclaw-runtime
```

## Install on Tencent Cloud Ubuntu

SSH to the server:

```bash
ssh ubuntu@124.222.101.170
```

Run from the deployed app directory:

```bash
cd /data/openclaw-lab-agent/app
bash scripts/server-install-openclaw.sh
```

The script creates:

```text
/data/openclaw-runtime
/data/openclaw-runtime/home
```

and installs the OpenClaw CLI under:

```text
/data/openclaw-runtime/bin
```

## Onboard

After installation:

```bash
export PATH="/data/openclaw-runtime/bin:$PATH"
export OPENCLAW_HOME="/data/openclaw-runtime/home"
openclaw onboard --install-daemon
```

If the installed command is `openclaw-cn`, use:

```bash
openclaw-cn onboard --install-daemon
```

## Security Audit

```bash
openclaw security audit --fix
openclaw security audit
```

or:

```bash
openclaw-cn security audit --fix
openclaw-cn security audit
```

Do not expose the gateway publicly until critical findings are gone.

## Connect to OpenCLAW MCP Later

Once the clean OpenClaw gateway is reachable locally on the server, OpenCLAW MCP can add
tools such as:

- `openclaw_runtime_status`
- `openclaw_gateway_health`
- `openclaw_run_task`

Keep the gateway bound to loopback and let OpenCLAW MCP be the audited control plane.

## Windows State

The old Windows state at:

```text
C:\Users\Zhangxu669090\.openclaw
```

is not touched by this server install.

