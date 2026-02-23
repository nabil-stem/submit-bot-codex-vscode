from __future__ import annotations

from pathlib import Path

from submit_autoclicker.config import load_config


def test_load_config_creates_default_when_missing(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    assert not config_path.exists()

    config = load_config(config_path)

    assert config_path.exists()
    assert config.allowed_processes == ["Code.exe"]
    assert config.dry_run is True
    assert config.allow_focus is False
    assert config.preserve_focus is True


def test_load_config_parses_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "allowed_processes = ['Code.exe', 'CustomApp.exe']",
                "allowed_window_title_contains = ['Visual Studio Code']",
                "button_texts = ['Submit']",
                "poll_interval_ms = 200",
                "click_cooldown_ms = 3000",
                "require_button_enabled = true",
                "require_near_text_contains = ['Do you want to make these changes?']",
                "allow_focus = false",
                "preserve_focus = true",
                "focus_restore_delay_ms = 120",
                "dry_run = false",
                "enable_image_fallback = true",
                "image_fallback_confidence = 0.95",
                "image_button_templates = ['templates/submit.png']",
                "hotkey_pause_resume = 'ctrl+shift+p'",
                "log_level = 'DEBUG'",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.allowed_processes == ["Code.exe", "CustomApp.exe"]
    assert config.button_texts == ["Submit"]
    assert config.poll_interval_ms == 200
    assert config.click_cooldown_ms == 3000
    assert config.require_near_text_contains == ["Do you want to make these changes?"]
    assert config.preserve_focus is True
    assert config.focus_restore_delay_ms == 120
    assert config.enable_image_fallback is True
    assert config.image_fallback_confidence == 0.95
    assert config.hotkey_pause_resume == "ctrl+shift+p"
    assert config.log_level == "DEBUG"


def test_load_config_clamps_and_fallbacks_invalid_values(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "poll_interval_ms = -1",
                "click_cooldown_ms = 'bad'",
                "focus_restore_delay_ms = -100",
                "image_fallback_confidence = 10",
                "allowed_processes = []",
                "button_texts = []",
            ]
        ),
        encoding="utf-8",
    )
    config = load_config(config_path)

    assert config.poll_interval_ms == 50
    assert config.click_cooldown_ms == 5000
    assert config.focus_restore_delay_ms == 0
    assert config.image_fallback_confidence == 1.0
    assert config.allowed_processes == ["Code.exe"]
    assert config.button_texts == ["Submit", "Continue", "Apply", "Yes"]
