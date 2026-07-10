"""Общий rate limiter (slowapi). Ключ — IP клиента (за прокси учитывается X-Forwarded-For)."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
