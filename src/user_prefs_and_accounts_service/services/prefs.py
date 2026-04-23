from sqlalchemy.orm import Session
from ..models import UserPreferences
def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    user_prefs = (
        db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    )
    if not user_prefs:
        user_prefs = UserPreferences(user_id=user_id)
        db.add(user_prefs)
        db.commit()
        db.refresh(user_prefs)
    return user_prefs