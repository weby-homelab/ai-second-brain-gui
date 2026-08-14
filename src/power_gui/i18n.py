"""Internationalization (i18n) support for POWER-GUI with English default and Ukrainian."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

DEFAULT_LANG = "en"
SUPPORTED_LANGS = {"en", "uk"}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "html_lang": "en",
        "app_name": "Weby Second Brain",
        "skip_to_content": "Skip to content",
        "dashboard": "Dashboard",
        "notes": "Notes",
        "search": "Search",
        "graph": "Graph",
        "tasks": "Tasks",
        "decisions": "Decisions",
        "receipts": "Receipts",
        "federation": "Federation",
        "login": "Login",
        "logout": "Logout",
        "authorization": "Authorization",
        "login_subtitle": "Enter administrator password to access cockpit",
        "admin_password": "Administrator Password:",
        "sign_in": "Sign In →",
        "invalid_password": "Invalid access password",
        "lang_switch_label": "Language",
        # Dashboard
        "system_status": "System Status",
        "system_healthy": "System Healthy",
        "vault_metrics": "Vault Metrics",
        "total_notes": "Total Notes",
        "active_projects": "Active Projects",
        "recent_updates": "Recent Knowledge Updates",
        "categories": "Categories",
        "quick_search": "Quick Search...",
        "view_all": "View All →",
        # Tasks
        "task_manager": "Task Manager v2",
        "new_task": "+ New Task",
        "backlog": "Backlog",
        "ready": "Ready",
        "in_progress": "In Progress",
        "completed": "Completed",
        "failed": "Failed",
        "revision": "Revision",
        "event_journal": "Event Journal",
        "task_title": "Task Title",
        "create_task": "Create Task",
        # Notes
        "note_browser": "Notes Browser",
        "edit_note": "Edit Note",
        "propose_change": "Propose Change",
        "read_mode": "Read Mode",
        "save": "Save",
        "cancel": "Cancel",
        "status": "Status",
        "created": "Created",
        "modified": "Modified",
        "tags": "Tags",
        "path": "Path",
        "category": "Category",
        "filter": "Filter",
        "all": "All",
        # Search
        "search_vault": "Search Knowledge Vault",
        "search_placeholder": "Search notes by title, tag, or fulltext...",
        "search_btn": "Search",
        "results": "Results",
        # Graph
        "knowledge_graph": "Knowledge Graph",
        "graph_subtitle": "Interactive 2D visualization of Obsidian note relationships",
        "reset_view": "Reset View",
        # Decisions & Receipts
        "decision_queue": "Operator Decision Queue",
        "receipts_ledger": "Receipts & Audit Ledger",
        "fleet_registry": "Fleet Registry",
    },
    "uk": {
        "html_lang": "uk",
        "app_name": "Weby Second Brain",
        "skip_to_content": "Перейти до вмісту",
        "dashboard": "Дашборд",
        "notes": "Нотатки",
        "search": "Пошук",
        "graph": "Граф",
        "tasks": "Завдання",
        "decisions": "Рішення",
        "receipts": "Чеки",
        "federation": "Федерація",
        "login": "Вхід",
        "logout": "Вийти",
        "authorization": "Авторизація",
        "login_subtitle": "Введіть пароль для доступу до панелі",
        "admin_password": "Пароль адміністратора:",
        "sign_in": "Увійти →",
        "invalid_password": "Невірний пароль доступу",
        "lang_switch_label": "Мова",
        # Dashboard
        "system_status": "Стан системи",
        "system_healthy": "Система в нормі",
        "vault_metrics": "Метрики бази знань",
        "total_notes": "Всього нотаток",
        "active_projects": "Активних проєктів",
        "recent_updates": "Останні оновлення знань",
        "categories": "Категорії",
        "quick_search": "Швидкий пошук...",
        "view_all": "Переглянути всі →",
        # Tasks
        "task_manager": "Task Manager v2",
        "new_task": "+ Нове завдання",
        "backlog": "Беклог",
        "ready": "Готово",
        "in_progress": "В роботі",
        "completed": "Виконано",
        "failed": "Помилка",
        "revision": "Ревізія",
        "event_journal": "Журнал подій",
        "task_title": "Назва завдання",
        "create_task": "Створити завдання",
        # Notes
        "note_browser": "Перегляд нотаток",
        "edit_note": "Редагувати нотатку",
        "propose_change": "Запропонувати зміну",
        "read_mode": "Режим читання",
        "save": "Зберегти",
        "cancel": "Скасувати",
        "status": "Статус",
        "created": "Створено",
        "modified": "Змінено",
        "tags": "Теги",
        "path": "Шлях",
        "category": "Категорія",
        "filter": "Фільтр",
        "all": "Всі",
        # Search
        "search_vault": "Пошук по базі знань",
        "search_placeholder": "Пошук нотаток за назвою, тегом чи текстом...",
        "search_btn": "Шукати",
        "results": "Результати",
        # Graph
        "knowledge_graph": "Граф знань",
        "graph_subtitle": "Інтерактивна 2D візуалізація зв'язків між нотатками Obsidian",
        "reset_view": "Скинути вигляд",
        # Decisions & Receipts
        "decision_queue": "Черга рішень оператора",
        "receipts_ledger": "Журнал аудиторських чеків",
        "fleet_registry": "Реєстр вузлів флоту",
    },
}


def normalize_lang(code: str | None) -> str:
    """Normalize language code to supported set, defaulting to 'en'."""
    if not code:
        return DEFAULT_LANG
    cleaned = code.strip().lower()
    if cleaned in {"uk", "ua", "ukr", "ukrainian"}:
        return "uk"
    return DEFAULT_LANG


def get_request_lang(request: Request) -> str:
    """Extract language from request query param or cookie, defaulting to 'en'."""
    query_lang = request.query_params.get("lang")
    if query_lang:
        return normalize_lang(query_lang)
    cookie_lang = request.cookies.get("power_gui_lang")
    if cookie_lang:
        return normalize_lang(cookie_lang)
    return DEFAULT_LANG


def translate(key: str, lang: str = DEFAULT_LANG) -> str:
    """Lookup translation key with fallback to English then raw key."""
    norm_lang = normalize_lang(lang)
    lang_dict = TRANSLATIONS.get(norm_lang, TRANSLATIONS[DEFAULT_LANG])
    if key in lang_dict:
        return lang_dict[key]
    return TRANSLATIONS[DEFAULT_LANG].get(key, key)


__all__ = [
    "DEFAULT_LANG",
    "SUPPORTED_LANGS",
    "TRANSLATIONS",
    "get_request_lang",
    "normalize_lang",
    "translate",
]
