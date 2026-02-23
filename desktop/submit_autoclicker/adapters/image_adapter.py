from __future__ import annotations

import logging
from pathlib import Path

import psutil

from submit_autoclicker.config import AppConfig
from submit_autoclicker.core.policy import AllowlistPolicy
from submit_autoclicker.models import ButtonCandidate, WindowIdentity

try:
    import pyautogui
except ImportError:  # pragma: no cover - environment dependent
    pyautogui = None  # type: ignore[assignment]

try:
    from pywinauto import Desktop
except ImportError:  # pragma: no cover - environment dependent
    Desktop = None  # type: ignore[assignment]


class ImageFallbackAdapter:
    """
    Optional image-based fallback.
    Safety model:
    - Disabled by default.
    - Only scans active foreground window.
    - Active window must still pass process/title allowlist.
    - Click requires allow_focus=True.
    """

    name = "image_fallback"

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._warned_missing_dep = False

    def scan(self, config: AppConfig) -> list[ButtonCandidate]:
        if not config.enable_image_fallback:
            return []

        if pyautogui is None or Desktop is None:
            if not self._warned_missing_dep:
                self._logger.warning(
                    "Image fallback requested but pyautogui/pywinauto is missing. Skipping fallback."
                )
                self._warned_missing_dep = True
            return []

        if not config.image_button_templates:
            return []

        active_window = self._active_window()
        if active_window is None:
            return []

        policy = AllowlistPolicy(config.allowed_processes, config.allowed_window_title_contains)
        if not policy.is_allowed(active_window):
            return []

        region = self._active_window_region()
        if region is None:
            return []

        for template in config.image_button_templates:
            path = Path(template)
            if not path.exists():
                self._logger.debug("Template does not exist: %s", path)
                continue

            try:
                hit = pyautogui.locateOnScreen(
                    str(path),
                    confidence=config.image_fallback_confidence,
                    region=region,
                )
            except Exception:
                self._logger.warning("Image lookup failed for template %s.", path, exc_info=True)
                continue

            if not hit:
                continue

            center_x = hit.left + hit.width // 2
            center_y = hit.top + hit.height // 2
            button_text = path.stem
            click_action = self._build_click_action(center_x, center_y)
            return [
                ButtonCandidate(
                    window=active_window,
                    button_text=button_text,
                    enabled=True,
                    near_text="",
                    source=self.name,
                    click_action=click_action,
                )
            ]

        return []

    def _active_window(self) -> WindowIdentity | None:
        try:
            active = Desktop(backend="uia").get_active()
            title = str(getattr(active, "window_text")() or "<untitled>").strip()
            process_id = int(getattr(active, "process_id")())
            process_name = psutil.Process(process_id).name()
            handle = int(getattr(active, "handle", 0))
            return WindowIdentity(title=title, process_name=process_name, handle=handle)
        except Exception:
            self._logger.debug("Unable to resolve active window for image fallback.", exc_info=True)
            return None

    def _active_window_region(self) -> tuple[int, int, int, int] | None:
        try:
            active = Desktop(backend="uia").get_active()
            rect = active.rectangle()
            width = max(1, int(rect.width()))
            height = max(1, int(rect.height()))
            return (int(rect.left), int(rect.top), width, height)
        except Exception:
            self._logger.debug("Unable to resolve active window region.", exc_info=True)
            return None

    def _build_click_action(self, x: int, y: int):
        def _click(allow_focus: bool) -> bool:
            if not allow_focus:
                self._logger.warning(
                    "Image fallback matched but allow_focus=false. Not clicking at (%s, %s).",
                    x,
                    y,
                )
                return False
            try:
                pyautogui.click(x=x, y=y)
                return True
            except Exception:
                self._logger.warning("Image fallback click failed at (%s, %s).", x, y, exc_info=True)
                return False

        return _click

