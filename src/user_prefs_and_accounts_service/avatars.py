import os
import time
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from src.user_prefs_and_accounts_service.main import User, UserResponse, get_current_active_user, get_db

router = APIRouter(tags=["avatars"])

AVATAR_DIR = Path(__file__).resolve().parent / "avatars" # Dedicated directory for avatars
AVATAR_DIR.mkdir(parents=True, exist_ok=True) # Create the directory if it doesn't exist

PUBLIC_BASE_URL = os.getenv("USER_ACCOUNTS_PUBLIC_BASE_URL", "").strip().rstrip("/")
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # (5MB)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/user/profile/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    content = await file.read()

    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar too large",
        )
    
    name = file.filename # maybe add more robust suffix checking here
    suffix = Path(name).suffix.lower() if name else ""
    
    if suffix not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )
    
    saved_name = f"{current_user.id}_{int(time.time())}{suffix}"
    user_dir = AVATAR_DIR / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Delete previous avatar file so old uploads don't accumulate on disk
    if db_user.avatar and str(db_user.avatar).startswith("/user/profile/avatar/file/"):
        old_filename = str(db_user.avatar).split("/user/profile/avatar/file/")[-1]
        old_path = user_dir / old_filename
        old_path.unlink(missing_ok=True)

    saved_path = user_dir / saved_name
    saved_path.write_bytes(content)

    db_user.avatar = f"/user/profile/avatar/file/{saved_name}"
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/user/profile/avatar/file/{user_id}/{filename}")
def get_avatar_file(user_id: int, filename: str):
    safe = Path(filename).name
    path = AVATAR_DIR / str(user_id) / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Avatar not found")
    if path.suffix.lower() in (".jpg", ".jpeg"):
        media = "image/jpeg"
    elif path.suffix.lower() == ".png":
        media = "image/png"
    elif path.suffix.lower() == ".webp":
        media = "image/webp"
    else:
        media = "application/octet-stream"
    return FileResponse(path=str(path), media_type=media, filename=safe)




    


