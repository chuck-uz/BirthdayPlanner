from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, HttpUrl, TypeAdapter


class WishlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    link_url: str | None = None
    has_photo: bool = False
    created_at: dt.datetime


def build_wishlist_item_out(w: object) -> WishlistItemOut:
    ph = getattr(w, "photo_path", None)
    return WishlistItemOut(
        id=w.id,
        title=w.title,
        description=getattr(w, "description", None),
        link_url=getattr(w, "link_url", None),
        has_photo=bool(ph and str(ph).strip()),
        created_at=w.created_at,
    )


def parse_optional_link_url(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if not s:
        return None
    u = TypeAdapter(HttpUrl).validate_python(s)
    return str(u)
