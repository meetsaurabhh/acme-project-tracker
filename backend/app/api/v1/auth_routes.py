"""HTTP routes for signing in."""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.dto.auth_dto import TokenResponse
from app.dto.user_dto import UserResponse
from app.models import User
from app.services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Exchange an email and password for an access token.

    The OAuth2 form calls the field 'username'; this application puts the
    email address in it.
    """
    return AuthService(db).authenticate(form_data.username, form_data.password)


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Who am I? Used by the frontend to restore a session on page load."""
    return current_user
