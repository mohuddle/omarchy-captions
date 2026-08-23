from __future__ import annotations

import json
import sys

from . import client
from .models import download_default, model_ready
from .paths import default_save_path
from .tui import run_tui


def _print_status(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "tui"
    rest = args[1:]

    if cmd in ("-h", "--help", "help"):
        print(
            "captions — live captions of speaker audio (PipeWire + sherpa-onnx)\n\n"
            "  captions            open the TUI\n"
            "  captions tui\n"
            "  captions start      listen to the default speakers\n"
            "  captions stop\n"
            "  captions status\n"
            "  captions follow     JSON events on stdout\n"
            "  captions clear\n"
            "  captions save [path]\n"
            "  captions setup      download the default English model\n"
            "  captions daemon     run the background service in the foreground\n"
        )
        return 0

    if cmd == "setup":
        download_default()
        print("then: captions tui   (space to listen)")
        return 0

    if cmd == "daemon":
        from .daemon import run_daemon

        run_daemon()
        return 0

    if cmd == "tui":
        if not model_ready():
            print("model missing — run: captions setup", file=sys.stderr)
            return 1
        run_tui()
        return 0

    if cmd == "follow":
        for event in client.follow():
            print(json.dumps(event, ensure_ascii=False), flush=True)
        return 0

    if cmd == "start":
        _print_status(client.request("start"))
        return 0
    if cmd == "stop":
        _print_status(client.request("stop"))
        return 0
    if cmd == "status":
        _print_status(client.request("status"))
        return 0
    if cmd == "clear":
        _print_status(client.request("clear"))
        return 0
    if cmd == "save":
        path = rest[0] if rest else str(default_save_path())
        _print_status(client.request("save", path=path))
        return 0

    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
