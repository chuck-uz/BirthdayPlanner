"""Фото референсов вишлиста: только через API, без StaticFiles; сжатие до 800px по длинной стороне."""

from __future__ import annotations

import logging
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent
UPLOADS_ROOT = BACKEND_ROOT / "uploads"
WISHLIST_DIR = UPLOADS_ROOT / "wishlist"

WISHLIST_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
WISHLIST_MAX_SIDE = 800
ALLOWED_CT_PREFIXES = ("image/jpeg", "image/jpg", "image/png", "image/pjpeg")

_JPEG_MAGIC = (b"\xff\xd8\xff",)
_PNG_MAGIC = (b"\x89PNG\r\n\x1a\n",)


def ensure_wishlist_dir() -> None:
    WISHLIST_DIR.mkdir(parents=True, exist_ok=True)


def relative_wishlist_path(filename: str) -> str:
    return f"wishlist/{filename}"


def filesystem_path_for_stored(stored: str) -> Path:
    if not stored or ".." in stored or stored.startswith(("/", "\\")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wishlist_photo_not_found")
    full = (UPLOADS_ROOT / stored).resolve()
    wishlist_resolved = WISHLIST_DIR.resolve()
    try:
        full.relative_to(wishlist_resolved)
    except ValueError:
        logger.warning("wishlist path traversal blocked stored=%r", stored)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="wishlist_photo_not_found",
        ) from None
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


async def read_raw_upload(file: UploadFile) -> tuple[bytes, str]:
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
        if total > WISHLIST_MAX_UPLOAD_BYTES:
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
    ext = ".jpg" if kind == "jpeg" else ".png"
    return data, ext


def _resize_if_needed(im: Image.Image, max_side: int) -> Image.Image:
    w, h = im.size
    if max(w, h) <= max_side:
        return im
    if w >= h:
        nw, nh = max_side, max(1, round(h * max_side / w))
    else:
        nh, nw = max_side, max(1, round(w * max_side / h))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def process_and_resize_wishlist_image(data: bytes) -> tuple[bytes, str]:
    """
    Сжимает изображение до WISHLIST_MAX_SIDE по длинной стороне.
    RGB → JPEG; с альфой → PNG.
    """
    im = Image.open(BytesIO(data))
    im = ImageOps.exif_transpose(im)
    im.load()

    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if has_alpha:
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        resized = _resize_if_needed(im, WISHLIST_MAX_SIDE)
        buf = BytesIO()
        resized.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), ".png"

    rgb = im.convert("RGB")
    resized = _resize_if_needed(rgb, WISHLIST_MAX_SIDE)
    buf = BytesIO()
    resized.save(buf, format="JPEG", quality=88, optimize=True)
    return buf.getvalue(), ".jpg"


def save_wishlist_photo_bytes(data: bytes, ext: str) -> str:
    ensure_wishlist_dir()
    ext = ext.lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    if ext == ".jpeg":
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    rel = relative_wishlist_path(name)
    path = filesystem_path_for_stored(rel)
    path.write_bytes(data)
    return rel


def delete_wishlist_file_if_exists(stored: str | None) -> None:
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
            logger.warning("failed to unlink wishlist photo %s", path, exc_info=True)


def media_type_for_stored(stored: str) -> str:
    lower = stored.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    return "application/octet-stream"
