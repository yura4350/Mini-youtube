from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .models import Video
from .database import SessionLocal

router = APIRouter(prefix="/videos", tags=["videos"])

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _split_tags(tags: str) -> list[str]:
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def serialize_video(video: Video) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "category": video.category,
        "tags": _split_tags(video.tags),
        "thumbnail_url": video.thumbnail_url,
        "uploader_id": video.uploader_id,
        "original_filename": video.original_filename,
        "saved_filename": video.saved_filename,
        "content_type": video.content_type,
        "size": video.size,
        "path": video.path,
        "views": video.views,
        "likes": video.likes,
        "duration_seconds": video.duration_seconds,
        "playback_url": f"/videos/{video.id}/play",
        "created_at": video.created_at.isoformat() if video.created_at else None,
    }


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
    description: str = Form(""),
    category: str = Form("Education"),
    tags: str = Form(""),
    thumbnail_url: str = Form(""),
    views: int = Form(0),
    likes: int = Form(0),
    duration_seconds: int = Form(0),
    uploader_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a video file and store metadata"""
    allowed_types = {"video/mp4", "video/webm", "video/quicktime"}
    allowed_extensions = {".mp4", ".webm", ".mov"}
    suffix = Path(file.filename).suffix.lower() if file.filename else ""

    is_known_video_mime = file.content_type in allowed_types
    is_octet_stream_with_video_extension = (
        file.content_type == "application/octet-stream" and suffix in allowed_extensions
    )
    if not (is_known_video_mime or is_octet_stream_with_video_extension):
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
        description=description,
        category=category,
        tags=tags,
        thumbnail_url=thumbnail_url,
        uploader_id=uploader_id,
        original_filename=file.filename,
        saved_filename=saved_name,
        content_type=file.content_type,
        size=len(content),
        path=str(saved_path),
        views=max(views, 0),
        likes=max(likes, 0),
        duration_seconds=max(duration_seconds, 0),
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    return serialize_video(video)


@router.get("")
def get_all_videos(db: Session = Depends(get_db)):
    """List all uploaded videos"""
    videos = db.query(Video).all()
    return [serialize_video(video) for video in videos]


@router.get("/{video_id}")
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Retrieve video metadata by ID"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return serialize_video(video)


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