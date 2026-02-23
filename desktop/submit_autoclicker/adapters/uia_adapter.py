from __future__ import annotations

import ctypes
import logging
import time
from collections.abc import Iterable

import psutil

from submit_autoclicker.config import AppConfig
from submit_autoclicker.core.policy import AllowlistPolicy, button_text_matches
from submit_autoclicker.models import ButtonCandidate, WindowIdentity

try:
    from pywinauto import Desktop
except ImportError:  # pragma: no cover - environment dependent
    Desktop = None  # type: ignore[assignment]


class UIAAdapter:
    name = "uia"

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._warned_missing_dep = False

    def scan(self, config: AppConfig) -> list[ButtonCandidate]:
        if Desktop is None:
            if not self._warned_missing_dep:
                self._logger.warning("pywinauto is not installed. UIA adapter disabled.")
                self._warned_missing_dep = True
            return []

        policy = AllowlistPolicy(config.allowed_processes, config.allowed_window_title_contains)
        candidates: list[ButtonCandidate] = []

        desktop = Desktop(backend="uia")
        windows = self._safe_windows(desktop.windows())

        for window in windows:
            identity = self._window_identity(window)
            if not identity:
                continue
            if not policy.is_allowed(identity):
                continue

            for button in self._safe_descendants(window, control_type="Button"):
                button_text = self._safe_text(button)
                if not button_text:
                    continue
                if not button_text_matches(button_text, config.button_texts):
                    continue

                enabled = self._safe_is_enabled(button)
                near_text = self._collect_near_text(button)
                click_action = self._build_click_action(
                    button,
                    identity,
                    button_text,
                    preserve_focus=config.preserve_focus,
                    focus_restore_delay_ms=config.focus_restore_delay_ms,
                )
                candidates.append(
                    ButtonCandidate(
                        window=identity,
                        button_text=button_text,
                        enabled=enabled,
                        near_text=near_text,
                        source=self.name,
                        click_action=click_action,
                    )
                )

        return candidates

    def _safe_windows(self, windows: Iterable[object]) -> list[object]:
        try:
            return list(windows)
        except Exception:
            self._logger.exception("Failed to enumerate top-level windows.")
            return []

    def _safe_descendants(self, window: object, **kwargs: object) -> list[object]:
        try:
            descendants = getattr(window, "descendants")(**kwargs)
            return list(descendants)
        except Exception:
            self._logger.debug("Failed to enumerate descendants for one window.", exc_info=True)
            return []

    def _safe_text(self, control: object) -> str:
        for attr in ("window_text",):
            try:
                value = getattr(control, attr)()
                if isinstance(value, str) and value.strip():
                    return value.strip()
            except Exception:
                continue

        try:
            element_info = getattr(control, "element_info")
            name = getattr(element_info, "name", "")
            if isinstance(name, str):
                return name.strip()
        except Exception:
            return ""
        return ""

    def _safe_is_enabled(self, control: object) -> bool:
        try:
            return bool(getattr(control, "is_enabled")())
        except Exception:
            return False

    def _window_identity(self, window: object) -> WindowIdentity | None:
        try:
            title = self._safe_text(window) or "<untitled>"
            process_id = int(getattr(window, "process_id")())
            handle = int(getattr(window, "handle", 0))
            process_name = psutil.Process(process_id).name()
            return WindowIdentity(title=title, process_name=process_name, handle=handle)
        except Exception:
            self._logger.debug("Failed to extract window identity.", exc_info=True)
            return None

    def _collect_near_text(self, button: object) -> str:
        snippets: list[str] = []
        try:
            parent = getattr(button, "parent")()
        except Exception:
            parent = None

        if parent is not None:
            siblings = self._safe_descendants(parent)
            for sibling in siblings[:30]:
                if sibling is button:
                    continue
                text = self._safe_text(sibling)
                if text:
                    snippets.append(text)
                if len(" ".join(snippets)) > 600:
                    break

        return " | ".join(snippets)

    def _foreground_handle(self) -> int | None:
        try:
            handle = int(ctypes.windll.user32.GetForegroundWindow())
            return handle if handle else None
        except Exception:
            return None

    def _restore_foreground(self, handle: int | None, delay_ms: int) -> None:
        if not handle:
            return
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        try:
            if ctypes.windll.user32.IsWindow(handle):
                ctypes.windll.user32.SetForegroundWindow(handle)
        except Exception:
            self._logger.debug("Failed to restore previous foreground window.", exc_info=True)

    def _build_click_action(
        self,
        button: object,
        window: WindowIdentity,
        button_text: str,
        *,
        preserve_focus: bool,
        focus_restore_delay_ms: int,
    ):
        def _click(allow_focus: bool) -> bool:
            previous_foreground = None
            if not allow_focus and preserve_focus:
                previous_foreground = self._foreground_handle()

            try:
                invoke = getattr(button, "invoke", None)
                if callable(invoke):
                    invoke()
                    if previous_foreground is not None:
                        current_foreground = self._foreground_handle()
                        if current_foreground != previous_foreground:
                            self._restore_foreground(previous_foreground, focus_restore_delay_ms)
                    return True
            except Exception:
                self._logger.debug(
                    "UIA invoke failed for %s (%s).",
                    button_text,
                    window.title,
                    exc_info=True,
                )

            if not allow_focus:
                return False

            try:
                getattr(button, "click_input")()
                return True
            except Exception:
                self._logger.warning(
                    "click_input failed for '%s' in '%s'.",
                    button_text,
                    window.title,
                    exc_info=True,
                )
                return False

        return _click
