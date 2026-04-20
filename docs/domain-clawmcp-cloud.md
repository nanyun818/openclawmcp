# Connect clawmcp.cloud

This keeps OpenCLAW Lab Agent private behind token auth while exposing the dashboard
through Nginx and HTTPS.

## 1. DNS

In your DNS provider, add:

```text
Type: A
Host: @
Value: 124.222.101.170
TTL: 600
```

Optional:

```text
Type: A
Host: www
Value: 124.222.101.170
TTL: 600
```

Wait until this works:

```bash
nslookup clawmcp.cloud
```

## 2. Keep the App Local

The Python app should keep listening on:

```text
127.0.0.1:8765
```

Do not set `OPENCLAW_LAB_HOST=0.0.0.0` for this deployment.

## 3. Install Nginx

On the server:

```bash
sudo apt update
sudo apt install -y nginx
```

## 4. Enable Reverse Proxy

```bash
sudo cp /data/openclaw-lab-agent/app/deploy/nginx/clawmcp.cloud.conf /etc/nginx/sites-available/clawmcp.cloud
sudo ln -sf /etc/nginx/sites-available/clawmcp.cloud /etc/nginx/sites-enabled/clawmcp.cloud
sudo nginx -t
sudo systemctl reload nginx
```

Visit:

```text
http://clawmcp.cloud
```

The page should ask for the same token stored in:

```text
/data/openclaw-lab-agent/.env
```

## 5. Add HTTPS

After DNS points to the server:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d clawmcp.cloud -d www.clawmcp.cloud
```

Then visit:

```text
https://clawmcp.cloud
```

## 6. Firewall

Allow only SSH, HTTP, and HTTPS:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw status
```

Enable UFW only after confirming SSH access is stable:

```bash
sudo ufw enable
```

## Security Notes

- Keep `OPENCLAW_LAB_TOKEN` long and private.
- Do not commit `/data/openclaw-lab-agent/.env`.
- Rotate the server password and move to SSH keys when convenient.
- Keep OpenCLAW Lab Agent bound to `127.0.0.1`; Nginx is the public entrypoint.

