import os
from ..database import SessionLocal
from ..models import User
from ..security import get_pwd_hash
def seed_admin_user() -> None:
    email = (os.getenv("SEED_ADMIN_EMAIL") or "").strip()
    password = (os.getenv("SEED_ADMIN_PASSWORD") or "").strip()
    if not email or not password:
        return
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return
        db.add(
            User(
                name=(os.getenv("SEED_ADMIN_NAME") or "Admin").strip() or "Admin",
                email=email,
                role="admin",
                hashed_pwd=get_pwd_hash(password),
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()