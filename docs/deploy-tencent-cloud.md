# Tencent Cloud Deployment

This guide deploys OpenCLAW Lab Agent on Ubuntu with runtime data in
`/data/openclaw-lab-agent`.

Do not put server passwords, API tokens, or SSH keys in this repository.

## 1. Prepare Server

SSH to the server as `ubuntu`, then run:

```bash
sudo mkdir -p /data/openclaw-lab-agent/app
sudo chown -R ubuntu:ubuntu /data/openclaw-lab-agent
python3 --version
```

Python 3.10+ is preferred.

## 2. Upload Code

For the first private test, copy the project directory to:

```bash
/data/openclaw-lab-agent/app
```

After the repository is published, use Git instead:

```bash
cd /data/openclaw-lab-agent
git clone <your-github-repo-url> app
```

## 3. Configure Token

Create a private environment file:

```bash
cat > /data/openclaw-lab-agent/.env <<'EOF'
OPENCLAW_LAB_HOME=/data/openclaw-lab-agent
OPENCLAW_LAB_TOKEN=replace-with-a-long-random-token
EOF
chmod 600 /data/openclaw-lab-agent/.env
```

Generate a token with:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
```

## 4. Run Manually

```bash
cd /data/openclaw-lab-agent/app
set -a
. /data/openclaw-lab-agent/.env
set +a
python3 -m openclaw_lab_agent.web_server
```

The service listens on `127.0.0.1:8765` by default.

## 5. Access Safely With SSH Tunnel

From your local machine:

```bash
ssh -L 8765:127.0.0.1:8765 ubuntu@124.222.101.170
```

Then open:

```text
http://127.0.0.1:8765
```

This avoids exposing the dashboard directly to the public internet.

## 6. Install systemd Service

```bash
sudo cp /data/openclaw-lab-agent/app/deploy/systemd/openclaw-lab-agent.service /etc/systemd/system/openclaw-lab-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now openclaw-lab-agent
sudo systemctl status openclaw-lab-agent
```

Useful commands:

```bash
sudo journalctl -u openclaw-lab-agent -f
sudo systemctl restart openclaw-lab-agent
```

## Security Notes

- Keep the dashboard bound to `127.0.0.1` during the first phase.
- Use an SSH tunnel instead of opening port `8765` publicly.
- Keep `/data/openclaw-lab-agent/.env` out of Git.
- Rotate the server password if it was ever shared in chat or screenshots.
- Prefer SSH keys and disable password login after the first deployment works.

