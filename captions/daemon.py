from __future__ import annotations

import json
import os
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .asr import StreamingAsr
from .capture import default_monitor_target, iter_pcm16, start_capture
from .models import DEFAULT_MODEL, model_ready
from .paths import default_save_path, pid_path, socket_path, status_path
from .protocol import MAX_LINES, empty_status, encode


class CaptionsDaemon:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.status: dict[str, Any] = empty_status()
        self.status["model"] = DEFAULT_MODEL["id"]
        self.status["ready"] = model_ready()
        if not self.status["ready"]:
            self.status["error"] = "model missing; run: captions setup"
        self.subscribers: list[socket.socket] = []
        self.capture_thread: threading.Thread | None = None
        self.capture_proc = None
        self.stop_capture = threading.Event()
        self.asr: StreamingAsr | None = None
        self.sock: socket.socket | None = None

    def write_status(self) -> None:
        path = status_path()
        tmp = path.with_suffix(".json.tmp")
        with self.lock:
            payload = json.dumps(self.status, ensure_ascii=False, indent=2)
        tmp.write_text(payload + "\n", encoding="utf-8")
        tmp.replace(path)

    def broadcast(self, message: dict[str, Any]) -> None:
        data = encode(message)
        dead: list[socket.socket] = []
        with self.lock:
            subs = list(self.subscribers)
        for sub in subs:
            try:
                sub.sendall(data)
            except OSError:
                dead.append(sub)
        if dead:
            with self.lock:
                self.subscribers = [s for s in self.subscribers if s not in dead]
            for sub in dead:
                try:
                    sub.close()
                except OSError:
                    pass

    def set_status(self, **fields: Any) -> None:
        with self.lock:
            self.status.update(fields)
            snapshot = dict(self.status)
        self.write_status()
        self.broadcast({"event": "status", **snapshot})

    def append_final(self, text: str) -> None:
        with self.lock:
            lines = list(self.status.get("lines") or [])
            lines.append(text)
            self.status["lines"] = lines[-MAX_LINES:]
            self.status["partial"] = ""
            snapshot = dict(self.status)
        self.write_status()
        self.broadcast({"event": "final", "text": text})
        self.broadcast({"event": "status", **snapshot})

    def set_partial(self, text: str) -> None:
        with self.lock:
            self.status["partial"] = text
            snapshot = dict(self.status)
        self.write_status()
        self.broadcast({"event": "partial", "text": text})
        self.broadcast({"event": "status", **snapshot})

    def load_asr(self) -> StreamingAsr:
        if self.asr is None:
            self.set_status(error="loading model…")
            self.asr = StreamingAsr()
            self.set_status(ready=True, error="")
        return self.asr

    def capture_loop(self) -> None:
        target = default_monitor_target()
        try:
            asr = self.load_asr()
            proc = start_capture(target)
        except Exception as exc:
            self.set_status(listening=False, error=str(exc))
            return
        self.capture_proc = proc
        self.set_status(listening=True, error="", source="speakers")
        try:
            assert proc.stdout is not None
            for chunk in iter_pcm16(proc):
                if self.stop_capture.is_set():
                    break
                event = asr.accept(chunk)
                if not event:
                    continue
                if event["event"] == "final":
                    self.append_final(event["text"])
                elif event["event"] == "partial":
                    self.set_partial(event["text"])
        except Exception as exc:
            self.set_status(error=str(exc), listening=False)
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self.capture_proc = None
            if not self.stop_capture.is_set() and self.status.get("listening"):
                err = ""
                if proc.stderr:
                    err = proc.stderr.read().decode("utf-8", "replace").strip()
                self.set_status(listening=False, error=err or "capture ended")
            else:
                self.set_status(listening=False)

    def start_listening(self) -> dict[str, Any]:
        if not model_ready():
            self.set_status(error="model missing; run: captions setup", ready=False)
            return self.snapshot()
        with self.lock:
            already = bool(self.status.get("listening"))
        if already:
            return self.snapshot()
        self.stop_capture.clear()
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
        for _ in range(80):
            time.sleep(0.1)
            with self.lock:
                listening = bool(self.status.get("listening"))
                err = str(self.status.get("error") or "")
            if listening or (err and err != "loading model…"):
                break
        return self.snapshot()

    def stop_listening(self) -> dict[str, Any]:
        self.stop_capture.set()
        proc = self.capture_proc
        if proc and proc.poll() is None:
            proc.terminate()
        thread = self.capture_thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        self.set_status(listening=False)
        return self.snapshot()

    def clear(self) -> dict[str, Any]:
        self.set_status(partial="", lines=[])
        return self.snapshot()

    def save(self, path: str | None = None) -> dict[str, Any]:
        dest = Path(path).expanduser() if path else default_save_path()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self.lock:
            lines = list(self.status.get("lines") or [])
            partial = str(self.status.get("partial") or "")
        body = "\n".join(lines)
        if partial:
            body = f"{body}\n{partial}" if body else partial
        dest.write_text(body.rstrip() + "\n", encoding="utf-8")
        self.set_status(saved=str(dest))
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return dict(self.status)

    def handle(self, message: dict[str, Any], conn: socket.socket) -> None:
        op = str(message.get("op") or "")
        if op == "subscribe":
            with self.lock:
                self.subscribers.append(conn)
            conn.sendall(encode({"event": "status", **self.snapshot()}))
            return
        if op == "status":
            conn.sendall(encode({"ok": True, **self.snapshot()}))
            return
        if op == "start":
            conn.sendall(encode({"ok": True, **self.start_listening()}))
            return
        if op == "stop":
            conn.sendall(encode({"ok": True, **self.stop_listening()}))
            return
        if op == "clear":
            conn.sendall(encode({"ok": True, **self.clear()}))
            return
        if op == "save":
            conn.sendall(encode({"ok": True, **self.save(message.get("path"))}))
            return
        if op == "ping":
            conn.sendall(encode({"ok": True}))
            return
        conn.sendall(encode({"ok": False, "error": f"unknown op {op}"}))

    def serve_client(self, conn: socket.socket) -> None:
        subscribed = False
        buf = b""
        try:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    raw, buf = buf.split(b"\n", 1)
                    if not raw.strip():
                        continue
                    message = json.loads(raw.decode("utf-8"))
                    if str(message.get("op") or "") == "subscribe":
                        subscribed = True
                    self.handle(message, conn)
                    if not subscribed:
                        return
        except (OSError, json.JSONDecodeError):
            pass
        finally:
            with self.lock:
                self.subscribers = [s for s in self.subscribers if s is not conn]
            try:
                conn.close()
            except OSError:
                pass

    def serve(self) -> None:
        sock_file = socket_path()
        if sock_file.exists():
            sock_file.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(sock_file))
        server.listen(16)
        server.setblocking(False)
        self.sock = server
        pid_path().write_text(str(os.getpid()), encoding="utf-8")
        self.write_status()

        def shutdown(*_args: object) -> None:
            self.stop_listening()
            server.close()
            if sock_file.exists():
                sock_file.unlink()
            sys.exit(0)

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        while True:
            readable, _, _ = select.select([server], [], [], 1.0)
            if not readable:
                continue
            try:
                conn, _ = server.accept()
            except OSError:
                continue
            threading.Thread(target=self.serve_client, args=(conn,), daemon=True).start()


def run_daemon() -> None:
    CaptionsDaemon().serve()
