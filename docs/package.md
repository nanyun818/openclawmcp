# Packaging

Use the packaging script to create a deployment zip without copying runtime data,
secrets, caches, or Git metadata.

From the project root on Windows:

```powershell
.\scripts\package.ps1
```

The package is written to:

```text
D:\Codex\openclaw-lab-agent\packages
```

The script also writes a `.sha256` checksum beside the zip.

To include tests in the archive:

```powershell
.\scripts\package.ps1 -IncludeTests
```

To choose a different output directory:

```powershell
.\scripts\package.ps1 -OutputDir "D:\Your\Package\Folder"
```

The archive excludes:

- `.env`
- `.git`
- `.pytest_cache`
- `.venv` and `venv`
- `__pycache__`
- `runs`
- `packages`
- `*.pyc`, `*.pyo`, and `*.log`

## Upload After Packaging

After creating a zip, upload it with:

```powershell
.\scripts\upload.ps1
```

The script uses native `ssh` and `scp`. It does not store your password; the SSH
client will ask for it in the terminal when needed.

It uploads the newest package to:

```text
/data/openclaw-lab-agent/uploads
```

Then it extracts the package under:

```text
/data/openclaw-lab-agent/app
```

Keep the private server environment file at:

```text
/data/openclaw-lab-agent/.env
```

Do not put `.env` into the package.
