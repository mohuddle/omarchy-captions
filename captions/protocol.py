from __future__ import annotations

import json
from typing import Any

MAX_LINES = 200


def encode(message: dict[str, Any]) -> bytes:
    return (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")


def decode_line(line: str) -> dict[str, Any]:
    return json.loads(line)


def empty_status() -> dict[str, Any]:
    return {
        "ready": False,
        "listening": False,
        "model": "",
        "source": "speakers",
        "partial": "",
        "lines": [],
        "error": "",
        "saved": "",
    }
