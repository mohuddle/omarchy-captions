from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .paths import socket_path
from .protocol import encode


def _connect() -> socket.socket:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(8)
    sock.connect(str(socket_path()))
    return sock


def daemon_alive() -> bool:
    path = socket_path()
    if not path.exists():
        return False
    try:
        sock = _connect()
        sock.sendall(encode({"op": "ping"}))
        sock.recv(256)
        sock.close()
        return True
    except OSError:
        return False


def start_daemon() -> None:
    if daemon_alive():
        return
    if socket_path().exists():
        try:
            socket_path().unlink()
        except OSError:
            pass
    root = str(Path(__file__).resolve().parents[1])
    env = os.environ.copy()
    env["PYTHONPATH"] = root + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [sys.executable, "-m", "captions", "daemon"]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd=root,
        env=env,
    )
    for _ in range(40):
        time.sleep(0.1)
        if daemon_alive():
            return
    raise RuntimeError("captions daemon failed to start")


def request(op: str, **fields: Any) -> dict[str, Any]:
    start_daemon()
    sock = _connect()
    try:
        payload = {"op": op, **fields}
        sock.sendall(encode(payload))
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(8192)
            if not chunk:
                break
            buf += chunk
        if not buf:
            raise RuntimeError("no reply from captions daemon")
        return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
    finally:
        sock.close()


def follow() -> Iterator[dict[str, Any]]:
    start_daemon()
    sock = _connect()
    sock.settimeout(None)
    sock.sendall(encode({"op": "subscribe"}))
    buf = b""
    try:
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                if raw.strip():
                    yield json.loads(raw.decode("utf-8"))
    finally:
        sock.close()
