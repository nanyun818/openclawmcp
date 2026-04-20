from __future__ import annotations

from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = Path("D:/Codex/openclaw-lab-agent") if Path("D:/").exists() else PROJECT_ROOT
DATA_ROOT = Path(os.environ.get("OPENCLAW_LAB_HOME", DEFAULT_DATA_ROOT)).expanduser()
RUNS_DIR = DATA_ROOT / "runs"
EXAMPLES_DIR = PROJECT_ROOT / "examples"
DEFAULT_CONFIG = EXAMPLES_DIR / "base_config.json"


def ensure_runs_dir() -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return RUNS_DIR


def run_dir(run_id: str) -> Path:
    return ensure_runs_dir() / run_id
