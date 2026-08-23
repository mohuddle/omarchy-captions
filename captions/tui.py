from __future__ import annotations

import curses
import threading
from typing import Any

from . import client
from .paths import default_save_path


class TuiState:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.status: dict[str, Any] = {}
        self.message = ""
        self.running = True

    def update(self, payload: dict[str, Any]) -> None:
        with self.lock:
            if payload.get("event") == "status" or "listening" in payload:
                self.status.update({k: v for k, v in payload.items() if k != "event"})
            elif payload.get("event") == "partial":
                self.status["partial"] = payload.get("text") or ""
            elif payload.get("event") == "final":
                lines = list(self.status.get("lines") or [])
                lines.append(str(payload.get("text") or ""))
                self.status["lines"] = lines[-200:]
                self.status["partial"] = ""


def _follow(state: TuiState) -> None:
    try:
        for event in client.follow():
            if not state.running:
                break
            state.update(event)
    except Exception as exc:
        with state.lock:
            state.message = str(exc)


def run_tui() -> None:
    client.start_daemon()
    state = TuiState()
    state.update(client.request("status"))
    thread = threading.Thread(target=_follow, args=(state,), daemon=True)
    thread.start()
    curses.wrapper(lambda stdscr: _loop(stdscr, state))
    state.running = False


def _loop(stdscr: curses.window, state: TuiState) -> None:
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.nodelay(True)
    stdscr.timeout(120)
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_YELLOW, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_CYAN, -1)

    while state.running:
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            break
        if key in (ord("q"), 27):
            break
        if key in (ord(" "), ord("l")):
            with state.lock:
                listening = bool(state.status.get("listening"))
            client.request("stop" if listening else "start")
        elif key in (ord("c"),):
            client.request("clear")
        elif key in (ord("s"),):
            reply = client.request("save")
            with state.lock:
                state.message = f"saved {reply.get('saved') or default_save_path()}"
        elif key in (ord("r"),):
            client.request("status")

        with state.lock:
            status = dict(state.status)
            note = state.message
        _draw(stdscr, status, note)


def _draw(stdscr: curses.window, status: dict[str, Any], note: str) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    listening = bool(status.get("listening"))
    ready = bool(status.get("ready"))
    error = str(status.get("error") or "")
    mark = "on " if listening else "off"
    title = f" captions  [{mark}]  {status.get('source') or 'speakers'}  {status.get('model') or ''}"
    stdscr.addnstr(0, 0, title[: width - 1], width - 1, curses.color_pair(2 if listening else 0) | curses.A_BOLD)
    hint = "space listen   s save   c clear   q quit"
    stdscr.addnstr(1, 0, hint[: width - 1], width - 1, curses.color_pair(3))
    if error:
        stdscr.addnstr(2, 0, error[: width - 1], width - 1, curses.color_pair(1))
    elif note:
        stdscr.addnstr(2, 0, note[: width - 1], width - 1)
    elif not ready:
        stdscr.addnstr(2, 0, "run captions setup to download the model", width - 1, curses.color_pair(1))

    lines = [str(x) for x in (status.get("lines") or [])]
    partial = str(status.get("partial") or "")
    body_top = 4
    body_height = max(1, height - body_top - 1)
    visible = lines[-body_height:]
    if partial and len(visible) >= body_height:
        visible = visible[-(body_height - 1) :]
    row = body_top
    for line in visible:
        if row >= height - 1:
            break
        stdscr.addnstr(row, 0, line[: width - 1], width - 1)
        row += 1
    if partial and row < height:
        stdscr.addnstr(row, 0, partial[: width - 1], width - 1, curses.A_DIM)
    stdscr.refresh()
