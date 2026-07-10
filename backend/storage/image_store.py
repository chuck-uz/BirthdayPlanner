"""Единое хранилище загружаемых изображений.

Одна реализация вместо продублированных avatar_storage/wishlist_storage:
- проверка сигнатуры (magic bytes) JPEG/PNG;
- защита от path traversal;
- пережатие через Pillow — снимает EXIF/встроенные данные и гасит decompression bomb;
- опциональное уменьшение по длинной стороне.
"""

from __future__ import annotations

import logging
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_ROOT = BACKEND_ROOT / "uploads"

# Защита от decompression bomb: жёсткий предел на число пикселей до декодирования.
Image.MAX_IMAGE_PIXELS = 64_000_000  # ~64 Мп

ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/jpg", "image/png", "image/pjpeg")
_MAGIC: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "jpeg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)
_READ_CHUNK = 64 * 1024


def _detect_kind(header: bytes) -> str | None:
    for magic, kind in _MAGIC:
        if header.startswith(magic):
            return kind
    return None


class ImageStore:
    """Хранилище изображений одного типа (аватары / фото вишлиста)."""

    def __init__(
        self,
        subdir: str,
        *,
        max_upload_bytes: int,
        max_side: int | None = None,
        not_found_detail: str = "file_not_found",
    ) -> None:
        self.subdir = subdir
        self.dir = UPLOADS_ROOT / subdir
        self.max_upload_bytes = max_upload_bytes
        self.max_side = max_side
        self.not_found_detail = not_found_detail

    # --- каталоги и пути -------------------------------------------------
    def ensure_dir(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)

    def _relative(self, filename: str) -> str:
        return f"{self.subdir}/{filename}"

    def filesystem_path(self, stored: str) -> Path:
        """Абсолютный путь к файлу; защита от path traversal."""
        if not stored or ".." in stored or stored.startswith(("/", "\\")):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=self.not_found_detail)
        full = (UPLOADS_ROOT / stored).resolve()
        try:
            full.relative_to(self.dir.resolve())
        except ValueError:
            logger.warning("path traversal blocked stored=%r", stored)
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=self.not_found_detail) from None
        return full

    # --- чтение и валидация ---------------------------------------------
    async def _read_capped(self, file: UploadFile) -> bytes:
        content_type = (file.content_type or "").lower().split(";")[0].strip()
        if (
            content_type
            and content_type != "application/octet-stream"
            and not content_type.startswith(ALLOWED_CONTENT_TYPES)
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_file_type")

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = await file.read(_READ_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > self.max_upload_bytes:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="file_too_large")
            chunks.append(chunk)

        data = b"".join(chunks)
        if not data:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="empty_file")
        if _detect_kind(data[:24]) is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_image_payload")
        return data

    # --- нормализация через Pillow --------------------------------------
    def _resize(self, im: Image.Image) -> Image.Image:
        if self.max_side is None:
            return im
        width, height = im.size
        if max(width, height) <= self.max_side:
            return im
        if width >= height:
            new_w, new_h = self.max_side, max(1, round(height * self.max_side / width))
        else:
            new_h, new_w = self.max_side, max(1, round(width * self.max_side / height))
        return im.resize((new_w, new_h), Image.Resampling.LANCZOS)

    def normalize(self, data: bytes) -> tuple[bytes, str]:
        """Пережимает изображение в JPEG (или PNG при наличии альфы). Возвращает (bytes, ext)."""
        try:
            im = Image.open(BytesIO(data))
            im = ImageOps.exif_transpose(im)
            im.load()
        except Image.DecompressionBombError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="image_too_large") from None
        except Exception:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid_image_payload") from None

        has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        if has_alpha:
            resized = self._resize(im.convert("RGBA"))
            buf = BytesIO()
            resized.save(buf, format="PNG", optimize=True)
            return buf.getvalue(), ".png"

        resized = self._resize(im.convert("RGB"))
        buf = BytesIO()
        resized.save(buf, format="JPEG", quality=88, optimize=True)
        return buf.getvalue(), ".jpg"

    # --- запись и удаление ----------------------------------------------
    def _save_bytes(self, data: bytes, ext: str) -> str:
        self.ensure_dir()
        name = f"{uuid.uuid4().hex}{ext}"
        rel = self._relative(name)
        self.filesystem_path(rel).write_bytes(data)
        return rel

    async def store_upload(self, file: UploadFile) -> str:
        """Полный цикл: читать → валидировать → пережать → сохранить. Возвращает относительный путь."""
        raw = await self._read_capped(file)
        processed, ext = self.normalize(raw)
        return self._save_bytes(processed, ext)

    def delete_if_exists(self, stored: str | None) -> None:
        if not stored:
            return
        try:
            path = self.filesystem_path(stored)
        except HTTPException:
            return
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                logger.warning("failed to unlink %s", path, exc_info=True)

    @staticmethod
    def media_type(stored: str) -> str:
        lower = stored.lower()
        if lower.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        if lower.endswith(".png"):
            return "image/png"
        return "application/octet-stream"


AVATAR_MAX_BYTES = 5 * 1024 * 1024
WISHLIST_MAX_BYTES = 5 * 1024 * 1024

avatar_store = ImageStore(
    "avatars",
    max_upload_bytes=AVATAR_MAX_BYTES,
    max_side=512,
    not_found_detail="avatar_not_found",
)
wishlist_store = ImageStore(
    "wishlist",
    max_upload_bytes=WISHLIST_MAX_BYTES,
    max_side=800,
    not_found_detail="wishlist_photo_not_found",
)
