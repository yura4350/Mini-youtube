from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from models import Video
from database import SessionLocal

router = APIRouter(prefix="/videos", tags=["videos"])

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/ping")
def ping_videos():
    """Health check for videos service"""
    return {"message": "videos route is working"}


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    uploader_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a video file and store metadata"""
    allowed_types = {"video/mp4", "video/webm", "video/quicktime"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported video type")

    video_id = str(uuid4())
    suffix = Path(file.filename).suffix or ".bin"
    saved_name = f"{video_id}{suffix}"
    saved_path = UPLOAD_DIR / saved_name

    content = await file.read()
    saved_path.write_bytes(content)

    # Save to database
    video = Video(
        id=video_id,
        title=title,
        uploader_id=uploader_id,
        original_filename=file.filename,
        saved_filename=saved_name,
        content_type=file.content_type,
        size=len(content),
        path=str(saved_path),
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    return {
        "id": video.id,
        "title": video.title,
        "uploader_id": video.uploader_id,
        "original_filename": video.original_filename,
        "saved_filename": video.saved_filename,
        "content_type": video.content_type,
        "size": video.size,
        "path": video.path,
    }


@router.get("")
def get_all_videos(db: Session = Depends(get_db)):
    """List all uploaded videos"""
    videos = db.query(Video).all()
    return videos


@router.get("/{video_id}")
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Retrieve video metadata by ID"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/play")
def play_video(video_id: str, db: Session = Depends(get_db)):
    """Stream/download video file"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = Path(video.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    return FileResponse(
        path=str(file_path),
        media_type=video.content_type,
        filename=video.original_filename,
    )


@router.delete("/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete video file and metadata"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = Path(video.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    file_path.unlink()
    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully", "id": video_id}