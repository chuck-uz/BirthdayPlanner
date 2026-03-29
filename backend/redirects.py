from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})


def safe_browser_redirect(url: str | None) -> str | None:
    """Разрешённые редиректы после Telegram Login (без open redirect)."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return None
        if parsed.hostname not in _ALLOWED_HOSTS:
            return None
        return url
    except Exception:
        return None
