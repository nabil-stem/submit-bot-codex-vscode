from __future__ import annotations

import os
import re
import shutil
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py310 fallback
    tomllib = None  # type: ignore[assignment]


APP_DIR_NAME = "SubmitAutoClicker"


@dataclass(slots=True)
class AppConfig:
    allowed_processes: list[str] = field(default_factory=lambda: ["Code.exe"])
    allowed_window_title_contains: list[str] = field(
        default_factory=lambda: ["Visual Studio Code", "CODEx", "Copilot"]
    )
    button_texts: list[str] = field(default_factory=lambda: ["Submit", "Continue", "Apply", "Yes"])
    poll_interval_ms: int = 350
    click_cooldown_ms: int = 5000
    require_button_enabled: bool = True
    require_near_text_contains: list[str] = field(default_factory=list)
    allow_focus: bool = False
    preserve_focus: bool = True
    focus_restore_delay_ms: int = 40
    dry_run: bool = True
    enable_image_fallback: bool = False
    image_fallback_confidence: float = 0.92
    image_button_templates: list[str] = field(default_factory=list)
    hotkey_pause_resume: str = "ctrl+alt+p"
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: default_log_dir())
    config_path: Path = field(default_factory=lambda: default_config_path())


def app_data_dir() -> Path:
    root = Path(os.getenv("APPDATA", str(Path.home())))
    path = root / APP_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_config_path() -> Path:
    return app_data_dir() / "config.toml"


def default_log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _coerce_list_of_strings(value: Any, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned or fallback


def _coerce_optional_list_of_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, parsed))


def _coerce_float(value: Any, fallback: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, parsed))


def _coerce_bool(value: Any, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return fallback


def render_default_config() -> str:
    default = AppConfig()
    return (
        "# Submit Auto-Clicker Desktop config\n\n"
        f"allowed_processes = {default.allowed_processes!r}\n"
        f"allowed_window_title_contains = {default.allowed_window_title_contains!r}\n"
        f"button_texts = {default.button_texts!r}\n\n"
        f"poll_interval_ms = {default.poll_interval_ms}\n"
        f"click_cooldown_ms = {default.click_cooldown_ms}\n"
        f"require_button_enabled = {str(default.require_button_enabled).lower()}\n"
        "require_near_text_contains = []\n\n"
        f"allow_focus = {str(default.allow_focus).lower()}\n"
        f"preserve_focus = {str(default.preserve_focus).lower()}\n"
        f"focus_restore_delay_ms = {default.focus_restore_delay_ms}\n"
        f"dry_run = {str(default.dry_run).lower()}\n\n"
        f"enable_image_fallback = {str(default.enable_image_fallback).lower()}\n"
        f"image_fallback_confidence = {default.image_fallback_confidence}\n"
        "image_button_templates = []\n\n"
        f"hotkey_pause_resume = {default.hotkey_pause_resume!r}\n"
        f"log_level = {default.log_level!r}\n"
    )


def ensure_config_exists(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    path.write_text(render_default_config(), encoding="utf-8")

    local_example = Path.cwd() / "config.example.toml"
    if local_example.exists():
        backup = path.parent / "config.example.toml"
        if not backup.exists():
            shutil.copyfile(local_example, backup)


def _parse_toml_fallback(text: str) -> dict[str, Any]:
    """
    Minimal parser for flat key/value config files.
    Supports the value shapes used by this project (strings, lists, bools, ints, floats).
    """
    parsed: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        value = re.sub(r"\btrue\b", "True", value, flags=re.IGNORECASE)
        value = re.sub(r"\bfalse\b", "False", value, flags=re.IGNORECASE)
        try:
            parsed[key] = ast.literal_eval(value)
        except Exception:
            parsed[key] = value.strip("'\"")
    return parsed


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    ensure_config_exists(config_path)

    raw: dict[str, Any] = {}
    try:
        text = config_path.read_text(encoding="utf-8")
        if tomllib is not None:
            raw = tomllib.loads(text)
        else:
            raw = _parse_toml_fallback(text)
    except OSError:
        raw = {}
    except Exception:
        raw = {}

    cfg = AppConfig(
        allowed_processes=_coerce_list_of_strings(raw.get("allowed_processes"), ["Code.exe"]),
        allowed_window_title_contains=_coerce_list_of_strings(
            raw.get("allowed_window_title_contains"), ["Visual Studio Code", "CODEx", "Copilot"]
        ),
        button_texts=_coerce_list_of_strings(
            raw.get("button_texts"), ["Submit", "Continue", "Apply", "Yes"]
        ),
        poll_interval_ms=_coerce_int(raw.get("poll_interval_ms"), 350, 50, 10_000),
        click_cooldown_ms=_coerce_int(raw.get("click_cooldown_ms"), 5000, 0, 300_000),
        require_button_enabled=_coerce_bool(raw.get("require_button_enabled"), True),
        require_near_text_contains=_coerce_optional_list_of_strings(raw.get("require_near_text_contains")),
        allow_focus=_coerce_bool(raw.get("allow_focus"), False),
        preserve_focus=_coerce_bool(raw.get("preserve_focus"), True),
        focus_restore_delay_ms=_coerce_int(raw.get("focus_restore_delay_ms"), 40, 0, 2000),
        dry_run=_coerce_bool(raw.get("dry_run"), True),
        enable_image_fallback=_coerce_bool(raw.get("enable_image_fallback"), False),
        image_fallback_confidence=_coerce_float(raw.get("image_fallback_confidence"), 0.92, 0.5, 1.0),
        image_button_templates=_coerce_optional_list_of_strings(raw.get("image_button_templates")),
        hotkey_pause_resume=str(raw.get("hotkey_pause_resume", "ctrl+alt+p")).strip() or "ctrl+alt+p",
        log_level=str(raw.get("log_level", "INFO")).upper(),
        log_dir=default_log_dir(),
        config_path=config_path,
    )
    return cfg
