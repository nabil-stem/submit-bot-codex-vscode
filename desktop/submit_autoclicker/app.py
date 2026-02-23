from __future__ import annotations

import os
import subprocess
from pathlib import Path

from submit_autoclicker.adapters.image_adapter import ImageFallbackAdapter
from submit_autoclicker.adapters.uia_adapter import UIAAdapter
from submit_autoclicker.config import AppConfig, default_config_path, load_config
from submit_autoclicker.core.engine import ClickEngine
from submit_autoclicker.hotkey import GlobalHotkeyController
from submit_autoclicker.logging_setup import setup_logging
from submit_autoclicker.tray import TrayController


class DesktopAutoClickerApp:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or default_config_path()
        self._config = load_config(self._config_path)
        self._logger = setup_logging(self._config.log_dir, self._config.log_level)

        self._uia_adapter = UIAAdapter(self._logger)
        self._image_adapter = ImageFallbackAdapter(self._logger)
        self._engine = ClickEngine(
            config=self._config,
            providers=[self._uia_adapter, self._image_adapter],
            logger=self._logger,
        )
        self._hotkey = GlobalHotkeyController(
            hotkey=self._config.hotkey_pause_resume,
            on_toggle=self._engine.toggle_paused,
            logger=self._logger,
        )
        self._tray = TrayController(
            status_provider=self._engine.status,
            toggle_pause=self._engine.toggle_paused,
            toggle_dry_run=self._engine.toggle_dry_run,
            reload_config=self.reload_config,
            open_config=self.open_config,
            open_logs=self.open_logs,
            on_quit=self.stop,
            logger=self._logger,
        )
        self._stopped = False

    def run(self) -> int:
        self._logger.info("Starting Submit Auto-Clicker desktop app.")
        self._engine.start()
        self._hotkey.start()

        try:
            self._tray.run()
        except KeyboardInterrupt:
            self._logger.info("Interrupted by user.")
        except Exception:
            self._logger.exception("Tray runtime failed.")
            self.stop()
            return 1

        self.stop()
        return 0

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._hotkey.stop()
        self._engine.stop()
        self._logger.info("Submit Auto-Clicker shutdown complete.")

    def reload_config(self) -> None:
        previous_hotkey = self._config.hotkey_pause_resume
        self._config = load_config(self._config_path)
        self._engine.update_config(self._config, keep_runtime_toggles=True)
        self._logger.setLevel(self._config.log_level)
        self._logger.info("Config reloaded from %s", self._config_path)
        if self._config.hotkey_pause_resume != previous_hotkey:
            self._hotkey.update_hotkey(self._config.hotkey_pause_resume)

    def open_config(self) -> None:
        self._open_path_in_explorer(self._config.config_path)

    def open_logs(self) -> None:
        self._open_path_in_explorer(self._config.log_dir)

    def _open_path_in_explorer(self, path: Path) -> None:
        try:
            if os.name == "nt":
                subprocess.Popen(["explorer.exe", str(path)], shell=False)  # noqa: S603
            else:
                subprocess.Popen([str(path)], shell=False)  # noqa: S603
        except Exception:
            self._logger.warning("Failed to open path: %s", path, exc_info=True)

