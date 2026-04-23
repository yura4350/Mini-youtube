from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_active_user
from ..models import User
from ..schemas import UserPreferencesResponse, UserPreferencesUpdate
from ..services.prefs import get_or_create_user_preferences

router = APIRouter(tags=["preferences"])


@router.get("/user/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    return get_or_create_user_preferences(db, current_user.id)


@router.patch("/user/preferences/update", response_model=UserPreferencesResponse)
def update_user_preferences(
    update_prefs: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    user_prefs = get_or_create_user_preferences(db, current_user.id)
    if update_prefs.privacy is not None:
        user_prefs.privacy = update_prefs.privacy
    if update_prefs.notifications is not None:
        user_prefs.notifications = update_prefs.notifications
    if update_prefs.ui_theme is not None:
        user_prefs.ui_theme = update_prefs.ui_theme
    db.commit()
    db.refresh(user_prefs)
    return user_prefs