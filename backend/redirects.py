from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_HOSTS = frozenset({"127.0.0.1", "localhost"})


def safe_browser_redirect(url: str | None) -> str | None:
    """Разрешённые редиректы после Telegram Login (без open redirect)."""
    url_clean = str(url).strip() if url else ""
    if not url_clean:
        return None
    try:
        parsed = urlparse(url_clean)
        if parsed.scheme not in ("http", "https"):
            return None
        host = (parsed.hostname or "").lower()
        if host not in {h.lower() for h in _ALLOWED_HOSTS}:
            return None
        # Вернуть нормализованный абсолютный URL (без лишних пробелов)
        return parsed.geturl() or None
    except Exception:
        return None


def resolve_post_login_redirect(requested_next: str | None, fallback: str) -> str:
    """Сначала next из запроса, иначе fallback из настроек, иначе жёсткий dev-URL."""
    u = safe_browser_redirect(requested_next)
    if u:
        return u
    u = safe_browser_redirect(fallback)
    if u:
        return u
    return "http://127.0.0.1/"
