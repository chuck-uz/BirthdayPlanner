from __future__ import annotations

from urllib.parse import urlparse

_DEV_HOSTS = frozenset({"127.0.0.1", "localhost"})


def hosts_from_urls(*urls: str | None) -> frozenset[str]:
    """Извлечь hostname из абсолютных URL (FRONTEND_DEFAULT_URL, CORS origins)."""
    hosts: set[str] = set()
    for raw in urls:
        if not raw or not str(raw).strip():
            continue
        try:
            parsed = urlparse(str(raw).strip())
            host = (parsed.hostname or "").lower()
            if host:
                hosts.add(host)
        except Exception:
            continue
    return frozenset(hosts)


def safe_browser_redirect(
    url: str | None,
    *,
    allowed_hosts: frozenset[str] | None = None,
) -> str | None:
    """Разрешённые редиректы после Telegram Login (без open redirect)."""
    url_clean = str(url).strip() if url else ""
    if not url_clean:
        return None
    allow = _DEV_HOSTS if allowed_hosts is None else (_DEV_HOSTS | allowed_hosts)
    try:
        parsed = urlparse(url_clean)
        if parsed.scheme not in ("http", "https"):
            return None
        host = (parsed.hostname or "").lower()
        if host not in allow:
            return None
        return parsed.geturl() or None
    except Exception:
        return None


def resolve_post_login_redirect(
    requested_next: str | None,
    fallback: str,
    *,
    allowed_hosts: frozenset[str] | None = None,
) -> str:
    """Сначала next из запроса, иначе fallback из настроек, иначе жёсткий dev-URL."""
    u = safe_browser_redirect(requested_next, allowed_hosts=allowed_hosts)
    if u:
        return u
    u = safe_browser_redirect(fallback, allowed_hosts=allowed_hosts)
    if u:
        return u
    return "http://127.0.0.1/"
