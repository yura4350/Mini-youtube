import os
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
# Import from your package — adjust if you use relative imports inside the package
from src.user_prefs_and_accounts_service.main import User, UserResponse, get_current_active_user, get_db

router = APIRouter(tags=["avatars"])

AVATAR_DIR = Path(__file__).resolve().parent / "avatars" # Dedicated directory for avatars
AVATAR_DIR.mkdir(parents=True, exist_ok=True) # Create the directory if it doesn't exist

PUBLIC_BASE_URL = os.getenv("USER_ACCOUNTS_PUBLIC_BASE_URL", "").strip().rstrip("/")
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # (5MB)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/user/profile/avatar")
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
    
    

    


