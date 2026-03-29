from __future__ import annotations

from fastapi import APIRouter, Depends

from deps import get_current_user
from models import User
from schemas.user import UserMeOut, UserProfileUpdate, build_user_me_out

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserMeOut)
async def get_me(user: User = Depends(get_current_user)) -> UserMeOut:
    return build_user_me_out(user)


@router.patch("/me", response_model=UserMeOut)
async def patch_me(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
) -> UserMeOut:
    user.full_name = body.full_name
    user.birth_date = body.birth_date
    return build_user_me_out(user)
