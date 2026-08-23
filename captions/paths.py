from __future__ import annotations

import os
from pathlib import Path


APP_ID = "omarchy-captions"


def home() -> Path:
    return Path(os.environ.get("HOME") or Path.home())


def runtime_dir() -> Path:
    raw = os.environ.get("XDG_RUNTIME_DIR")
    path = Path(raw) if raw else Path("/tmp") / f"runtime-{os.getuid()}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_dir() -> Path:
    raw = os.environ.get("XDG_STATE_HOME")
    path = Path(raw) if raw else home() / ".local" / "state"
    dest = path / "omarchy" / "captions"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def data_dir() -> Path:
    raw = os.environ.get("XDG_DATA_HOME")
    path = Path(raw) if raw else home() / ".local" / "share"
    dest = path / "omarchy" / "captions"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def socket_path() -> Path:
    return runtime_dir() / f"{APP_ID}.sock"


def pid_path() -> Path:
    return runtime_dir() / f"{APP_ID}.pid"


def status_path() -> Path:
    return state_dir() / "status.json"


def default_save_path() -> Path:
    return state_dir() / "transcript.txt"


def models_dir() -> Path:
    dest = data_dir() / "models"
    dest.mkdir(parents=True, exist_ok=True)
    return dest
