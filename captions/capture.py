from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Iterator


SAMPLE_RATE = 16000


def default_monitor_target() -> str | None:
    pactl = shutil.which("pactl")
    if not pactl:
        return None
    try:
        sink = subprocess.check_output([pactl, "get-default-sink"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    if not sink:
        return None
    return f"{sink}.monitor"


def pw_record_cmd(target: str | None = None) -> list[str]:
    binary = shutil.which("pw-record")
    if not binary:
        raise RuntimeError("pw-record not found; install pipewire-audio")
    cmd = [
        binary,
        "--media-type",
        "Audio",
        "--media-category",
        "Capture",
        "--media-role",
        "Accessibility",
        "--rate",
        str(SAMPLE_RATE),
        "--channels",
        "1",
        "--format",
        "s16",
        "--raw",
        "--latency",
        "100ms",
        "-P",
        "stream.capture.sink=true",
        "-P",
        "node.name=omarchy-captions",
    ]
    if target:
        cmd.extend(["--target", target])
    cmd.append("-")
    return cmd


def iter_pcm16(proc: subprocess.Popen[bytes], frame_bytes: int = 3200) -> Iterator[bytes]:
    """Yield ~100ms of s16le mono at 16 kHz (3200 bytes)."""
    while True:
        chunk = proc.stdout.read(frame_bytes) if proc.stdout else b""
        if not chunk:
            break
        yield chunk


def start_capture(target: str | None = None) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    cmd = pw_record_cmd(target)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
