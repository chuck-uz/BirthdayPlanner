from redirects import hosts_from_urls, resolve_post_login_redirect, safe_browser_redirect


def test_allows_localhost_http():
    assert safe_browser_redirect("http://127.0.0.1/profile") == "http://127.0.0.1/profile"
    assert safe_browser_redirect("http://localhost:5173/") == "http://localhost:5173/"


def test_blocks_external_host_open_redirect():
    assert safe_browser_redirect("http://evil.example.com/") is None
    assert safe_browser_redirect("https://attacker.test/phish") is None


def test_allows_configured_production_host():
    allow = frozenset({"example.org"})
    assert (
        safe_browser_redirect("https://example.org/", allowed_hosts=allow)
        == "https://example.org/"
    )
    assert (
        safe_browser_redirect("https://example.org/profile", allowed_hosts=allow)
        == "https://example.org/profile"
    )


def test_blocks_non_http_schemes():
    assert safe_browser_redirect("javascript:alert(1)") is None
    assert safe_browser_redirect("file:///etc/passwd") is None


def test_blocks_empty_and_none():
    assert safe_browser_redirect(None) is None
    assert safe_browser_redirect("   ") is None


def test_hosts_from_urls():
    assert hosts_from_urls("https://example.org/", "https://example.org") == frozenset(
        {"example.org"}
    )


def test_resolve_falls_back_to_default_then_hard_default():
    assert resolve_post_login_redirect("http://evil.test/", "http://127.0.0.1/") == "http://127.0.0.1/"
    assert resolve_post_login_redirect(None, "http://evil.test/") == "http://127.0.0.1/"


def test_resolve_uses_production_fallback_when_allowed():
    allow = frozenset({"example.org"})
    assert (
        resolve_post_login_redirect(
            None,
            "https://example.org/",
            allowed_hosts=allow,
        )
        == "https://example.org/"
    )
    assert (
        resolve_post_login_redirect(
            "https://example.org/setup-profile",
            "https://example.org/",
            allowed_hosts=allow,
        )
        == "https://example.org/setup-profile"
    )
