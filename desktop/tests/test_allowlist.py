from __future__ import annotations

from submit_autoclicker.core.policy import AllowlistPolicy, button_text_matches, near_text_matches
from submit_autoclicker.models import WindowIdentity


def test_allowlist_requires_process_and_title_match() -> None:
    policy = AllowlistPolicy(
        allowed_processes=["Code.exe"],
        allowed_title_contains=["Visual Studio Code", "Copilot"],
    )

    allowed_window = WindowIdentity(title="Visual Studio Code - workspace", process_name="Code.exe")
    denied_by_process = WindowIdentity(title="Visual Studio Code", process_name="notepad.exe")
    denied_by_title = WindowIdentity(title="Calculator", process_name="Code.exe")

    assert policy.is_allowed(allowed_window) is True
    assert policy.is_allowed(denied_by_process) is False
    assert policy.is_allowed(denied_by_title) is False


def test_button_text_matching_is_case_and_whitespace_tolerant() -> None:
    assert button_text_matches("  Submit  ", ["submit"]) is True
    assert button_text_matches("Submit Changes", ["submit"]) is True
    assert button_text_matches("Yes, and don't ask again", ["Yes"]) is True
    assert button_text_matches("Create submit auto-clicker", ["submit"]) is False
    assert button_text_matches("Continue", ["Submit", "Apply"]) is False


def test_near_text_matching_respects_optional_requirement() -> None:
    assert near_text_matches("anything", []) is True
    assert (
        near_text_matches(
            near_text="Dialog: Do you want to make these changes?",
            required_near_patterns=["make these changes"],
        )
        is True
    )
    assert near_text_matches("Dialog without marker", ["make these changes"]) is False
