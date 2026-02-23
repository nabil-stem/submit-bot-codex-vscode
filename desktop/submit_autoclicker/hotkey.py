from __future__ import annotations

import logging
import threading
from collections.abc import Callable

try:
    from pynput import keyboard
except ImportError:  # pragma: no cover - environment dependent
    keyboard = None  # type: ignore[assignment]


def to_pynput_hotkey(hotkey: str) -> str:
    mapping = {
        "ctrl": "<ctrl>",
        "control": "<ctrl>",
        "alt": "<alt>",
        "shift": "<shift>",
        "win": "<cmd>",
        "cmd": "<cmd>",
        "super": "<cmd>",
    }
    tokens = [token.strip().lower() for token in hotkey.split("+") if token.strip()]
    converted = [mapping.get(token, token) for token in tokens]
    return "+".join(converted)


class GlobalHotkeyController:
    def __init__(self, hotkey: str, on_toggle: Callable[[], bool], logger: logging.Logger) -> None:
        self._raw_hotkey = hotkey
        self._on_toggle = on_toggle
        self._logger = logger
        self._listener: keyboard.GlobalHotKeys | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def update_hotkey(self, hotkey: str) -> None:
        with self._lock:
            self.stop()
            self._raw_hotkey = hotkey
            self.start()

    def start(self) -> None:
        if keyboard is None:
            self._logger.warning("pynput is not installed. Global hotkey is disabled.")
            return

        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            combo = to_pynput_hotkey(self._raw_hotkey)
            self._listener = keyboard.GlobalHotKeys({combo: self._handle_toggle})
            self._thread = threading.Thread(
                target=self._listener.run,
                name="submit-autoclicker-hotkey",
                daemon=True,
            )
            self._thread.start()
            self._logger.info("Global pause/resume hotkey active: %s", self._raw_hotkey)

    def stop(self) -> None:
        with self._lock:
            listener = self._listener
            thread = self._thread
            self._listener = None
            self._thread = None

        if listener is not None:
            listener.stop()
        if thread and thread.is_alive():
            thread.join(timeout=1.0)

    def _handle_toggle(self) -> None:
        try:
            paused = self._on_toggle()
            state = "paused" if paused else "running"
            self._logger.info("Hotkey toggled engine state to %s.", state)
        except Exception:
            self._logger.exception("Hotkey toggle callback failed.")

