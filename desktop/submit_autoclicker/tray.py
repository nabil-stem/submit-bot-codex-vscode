from __future__ import annotations

import logging
import threading
from collections.abc import Callable

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover - environment dependent
    pystray = None  # type: ignore[assignment]
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]


StatusProvider = Callable[[], dict[str, str | bool | float | None]]
SimpleAction = Callable[[], None]
ToggleAction = Callable[[], bool]


class TrayController:
    def __init__(
        self,
        *,
        status_provider: StatusProvider,
        toggle_pause: ToggleAction,
        toggle_dry_run: ToggleAction,
        reload_config: SimpleAction,
        open_config: SimpleAction,
        open_logs: SimpleAction,
        on_quit: SimpleAction,
        logger: logging.Logger,
    ) -> None:
        self._status_provider = status_provider
        self._toggle_pause = toggle_pause
        self._toggle_dry_run = toggle_dry_run
        self._reload_config = reload_config
        self._open_config = open_config
        self._open_logs = open_logs
        self._on_quit = on_quit
        self._logger = logger

        self._icon: pystray.Icon | None = None
        self._stop_event = threading.Event()
        self._refresh_thread: threading.Thread | None = None

    def run(self) -> None:
        if pystray is None or Image is None or ImageDraw is None:
            raise RuntimeError("pystray and pillow are required for tray mode.")

        initial = self._status_provider()
        self._icon = pystray.Icon(
            "submit-autoclicker",
            icon=self._build_icon(initial),
            title=self._build_title(initial),
            menu=self._build_menu(),
        )

        self._start_refresh_loop()
        self._icon.run()
        self._stop_event.set()

    def _start_refresh_loop(self) -> None:
        def _loop() -> None:
            while not self._stop_event.wait(2.0):
                self._refresh_icon()

        self._refresh_thread = threading.Thread(
            target=_loop,
            name="submit-autoclicker-tray-refresh",
            daemon=True,
        )
        self._refresh_thread.start()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("Pause / Resume", self._on_toggle_pause),
            pystray.MenuItem("Dry-Run Mode", self._on_toggle_dry_run, checked=self._is_dry_run_checked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Reload Config", self._on_reload_config),
            pystray.MenuItem("Open Config", self._on_open_config),
            pystray.MenuItem("Open Logs", self._on_open_logs),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_clicked),
        )

    def _on_toggle_pause(self, icon: object, item: object) -> None:
        self._toggle_pause()
        self._refresh_icon()

    def _on_toggle_dry_run(self, icon: object, item: object) -> None:
        self._toggle_dry_run()
        self._refresh_icon()

    def _on_reload_config(self, icon: object, item: object) -> None:
        self._reload_config()
        self._refresh_icon()

    def _on_open_config(self, icon: object, item: object) -> None:
        self._open_config()

    def _on_open_logs(self, icon: object, item: object) -> None:
        self._open_logs()

    def _on_quit_clicked(self, icon: object, item: object) -> None:
        self._stop_event.set()
        self._on_quit()
        if self._icon:
            self._icon.stop()

    def _is_dry_run_checked(self, item: object) -> bool:
        status = self._status_provider()
        return bool(status.get("dry_run"))

    def _refresh_icon(self) -> None:
        if not self._icon:
            return
        status = self._status_provider()
        self._icon.icon = self._build_icon(status)
        self._icon.title = self._build_title(status)
        self._icon.update_menu()

    def _build_icon(self, status: dict[str, str | bool | float | None]):
        paused = bool(status.get("paused", False))
        dry_run = bool(status.get("dry_run", True))

        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        if paused:
            base_color = (196, 0, 0, 255)
        else:
            base_color = (0, 143, 57, 255)

        draw.ellipse((6, 6, 58, 58), fill=base_color)
        draw.text((23, 20), "S", fill=(255, 255, 255, 255))

        if dry_run:
            draw.ellipse((44, 44, 62, 62), fill=(230, 180, 0, 255))
        return image

    def _build_title(self, status: dict[str, str | bool | float | None]) -> str:
        paused = bool(status.get("paused", False))
        dry_run = bool(status.get("dry_run", True))
        runtime = "PAUSED" if paused else "ACTIVE"
        mode = "DRY-RUN" if dry_run else "LIVE"
        return f"Submit Auto-Clicker [{runtime} | {mode}]"

