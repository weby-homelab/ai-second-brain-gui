"""Unit tests for i18n translations and language resolution."""

from __future__ import annotations

from unittest.mock import MagicMock

from power_gui.i18n import (
    DEFAULT_LANG,
    get_request_lang,
    normalize_lang,
    translate,
)


def test_normalize_lang() -> None:
    """Test language normalization with English fallback."""
    assert normalize_lang("en") == "en"
    assert normalize_lang("EN") == "en"
    assert normalize_lang("uk") == "uk"
    assert normalize_lang("UK") == "uk"
    assert normalize_lang("ukr") == "uk"
    assert normalize_lang("unknown") == DEFAULT_LANG
    assert normalize_lang(None) == DEFAULT_LANG


def test_translate_lookup() -> None:
    """Test key translation in English and Ukrainian."""
    # English default
    assert translate("dashboard", "en") == "Dashboard"
    assert translate("notes", "en") == "Notes"
    assert translate("tasks", "en") == "Tasks"

    # Ukrainian
    assert translate("dashboard", "uk") == "Дашборд"
    assert translate("notes", "uk") == "Нотатки"
    assert translate("tasks", "uk") == "Завдання"

    # Fallback to key if unknown in both
    assert translate("nonexistent_key_123", "en") == "nonexistent_key_123"
    assert translate("nonexistent_key_123", "uk") == "nonexistent_key_123"


def test_get_request_lang() -> None:
    """Test extracting language from request query or cookie."""
    # Query param priority
    req1 = MagicMock()
    req1.query_params = {"lang": "uk"}
    req1.cookies = {"power_gui_lang": "en"}
    assert get_request_lang(req1) == "uk"

    # Cookie fallback
    req2 = MagicMock()
    req2.query_params = {}
    req2.cookies = {"power_gui_lang": "uk"}
    assert get_request_lang(req2) == "uk"

    # Default fallback
    req3 = MagicMock()
    req3.query_params = {}
    req3.cookies = {}
    assert get_request_lang(req3) == "en"
