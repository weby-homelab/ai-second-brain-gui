"""CSRF protection tokens and middleware helpers."""

from __future__ import annotations

import hashlib
import hmac
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def generate_csrf_token(secret_key: str, session_id: str) -> str:
    """Generate deterministic HMAC-SHA256 CSRF token for a given session."""
    key = secret_key.encode("utf-8")
    msg = f"csrf:{session_id}".encode()
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_csrf_token(secret_key: str, session_id: str, token: str) -> bool:
    """Constant-time comparison of submitted CSRF token."""
    expected = generate_csrf_token(secret_key, session_id)
    return hmac.compare_digest(expected, token)
