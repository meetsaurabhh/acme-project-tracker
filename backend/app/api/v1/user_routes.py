"""HTTP routes for account administration. Admin only for anything that writes."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.dto.user_dto import UserCreateRequest, UserResponse, UserUpdateRequest
from app.models import User
from app.services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    search: str | None = Query(default=None, description="Matches name or email"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Any signed-in user can see the list, for example to pick a project manager."""
    return UserService(db).list_users(search)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).create_user(payload)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return UserService(db).update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    UserService(db).delete_user(user_id, current_user)
