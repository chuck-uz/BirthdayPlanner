"""Сохранение аватаров только через API: без StaticFiles, пути нормализуются под uploads/avatars."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent
UPLOADS_ROOT = BACKEND_ROOT / "uploads"
AVATARS_DIR = UPLOADS_ROOT / "avatars"

AVATAR_MAX_BYTES = 5 * 1024 * 1024
ALLOWED_CT_PREFIXES = ("image/jpeg", "image/jpg", "image/png", "image/pjpeg")

_JPEG_MAGIC = (b"\xff\xd8\xff",)
_PNG_MAGIC = (b"\x89PNG\r\n\x1a\n",)


def ensure_avatars_dir() -> None:
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)


def relative_avatar_path(filename: str) -> str:
    """Путь относительно UPLOADS_ROOT, для поля User.avatar_path."""
    return f"avatars/{filename}"


def filesystem_path_for_stored(stored: str) -> Path:
    """Абсолютный путь к файлу; защита от path traversal."""
    if not stored or ".." in stored or stored.startswith(("/", "\\")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found")
    full = (UPLOADS_ROOT / stored).resolve()
    avatars_resolved = AVATARS_DIR.resolve()
    try:
        full.relative_to(avatars_resolved)
    except ValueError:
        logger.warning("avatar path traversal blocked stored=%r", stored)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="avatar_not_found") from None
    return full


def _detect_image_kind(header: bytes) -> str | None:
    if len(header) < 12:
        return None
    for sig in _JPEG_MAGIC:
        if header.startswith(sig):
            return "jpeg"
    for sig in _PNG_MAGIC:
        if header.startswith(sig):
            return "png"
    return None


async def read_and_validate_avatar(file: UploadFile) -> tuple[bytes, str]:
    """
    Читает тело до AVATAR_MAX_BYTES, проверяет JPEG/PNG по сигнатуре.
    Возвращает (bytes, расширение '.jpg' или '.png').
    """
    ct = (file.content_type or "").lower().split(";")[0].strip()
    if ct and ct != "application/octet-stream" and not ct.startswith(ALLOWED_CT_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_file_type",
        )

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(1024 * 64)
        if not chunk:
            break
        total += len(chunk)
        if total > AVATAR_MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="file_too_large",
            )
        chunks.append(chunk)

    data = b"".join(chunks)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_file")

    kind = _detect_image_kind(data[:24])
    if kind is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_image_payload",
        )
    if ct and ct != "application/octet-stream":
        if kind == "jpeg" and not ct.startswith(("image/jpeg", "image/jpg", "image/pjpeg")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_type_mismatch",
            )
        if kind == "png" and not ct.startswith("image/png"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="content_type_mismatch",
            )

    ext = ".jpg" if kind == "jpeg" else ".png"
    return data, ext


def save_avatar_bytes(data: bytes, ext: str) -> str:
    """Пишет файл, возвращает относительный путь для БД (avatars/<uuid>.ext)."""
    ensure_avatars_dir()
    name = f"{uuid.uuid4().hex}{ext}"
    rel = relative_avatar_path(name)
    path = filesystem_path_for_stored(rel)
    path.write_bytes(data)
    return rel


def delete_stored_file_if_exists(stored: str | None) -> None:
    if not stored:
        return
    try:
        path = filesystem_path_for_stored(stored)
    except HTTPException:
        return
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            logger.warning("failed to unlink avatar %s", path, exc_info=True)


def media_type_for_stored(stored: str) -> str:
    lower = stored.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    return "application/octet-stream"
