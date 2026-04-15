import logging
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.dashboard_service.models import Subscription
from .models import Video, VideoTranscript
from .database import SessionLocal

router = APIRouter(prefix="/videos", tags=["videos"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
COMMUNICATION_API_BASE_URL = os.getenv("COMMUNICATION_API_BASE_URL", "").strip().rstrip("/")
MAX_NOTIFICATION_MESSAGE_LENGTH = 180
ASR_ENABLED = os.getenv("ASR_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
ASR_MODEL_SIZE = os.getenv("ASR_MODEL_SIZE", "tiny").strip() or "tiny"
ASR_COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "int8").strip() or "int8"
MAX_TRANSCRIPT_CHARS = 20000


def _split_tags(tags: str) -> list[str]:
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def _thumbnail_path(video_id: str) -> Path:
    return THUMBNAIL_DIR / f"{video_id}.jpg"


def _truncate_text(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[:max_length - 3].rstrip()}..."


def _generate_first_frame_thumbnail(video_path: Path, thumbnail_path: Path) -> bool:
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                "select=eq(n\\,0)",
                "-vframes",
                "1",
                str(thumbnail_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _transcribe_video_audio_to_text(video_path: Path) -> tuple[str, str | None] | None:
    if not ASR_ENABLED:
        return None

    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:
        logger.warning("Automatic ASR skipped: faster_whisper import failed: %s", exc)
        return None

    try:
        model = WhisperModel(ASR_MODEL_SIZE, compute_type=ASR_COMPUTE_TYPE)
        segments, info = model.transcribe(str(video_path), vad_filter=True)
        text_parts = [segment.text.strip() for segment in segments if segment.text and segment.text.strip()]
        transcript_text = " ".join(text_parts).strip()
        if not transcript_text:
            return None
        if len(transcript_text) > MAX_TRANSCRIPT_CHARS:
            transcript_text = transcript_text[:MAX_TRANSCRIPT_CHARS]
        language = getattr(info, "language", None)
        return transcript_text, language
    except Exception:
        logger.exception("Automatic ASR failed for file=%s", video_path)
        return None


def _upsert_video_transcript(
    db: Session,
    *,
    video_id: str,
    transcript_text: str = "",
    source: str = "asr",
    status: str = "queued",
    error_message: str | None = None,
    language: str | None = None,
) -> None:
    row = db.query(VideoTranscript).filter(VideoTranscript.video_id == video_id).first()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if row:
        row.transcript_text = transcript_text
        row.source = source
        row.status = status
        row.error_message = error_message
        row.language = language
        row.updated_at = now
    else:
        db.add(
            VideoTranscript(
                video_id=video_id,
                transcript_text=transcript_text,
                source=source,
                status=status,
                error_message=error_message,
                language=language,
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()


def _best_effort_update_transcript(
    *,
    video_id: str,
    transcript_text: str = "",
    source: str = "faster_whisper",
    status: str,
    error_message: str | None = None,
    language: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        _upsert_video_transcript(
            db,
            video_id=video_id,
            transcript_text=transcript_text,
            source=source,
            status=status,
            error_message=error_message,
            language=language,
        )
    except Exception:
        logger.exception(
            "Failed to update transcript state=%s for video_id=%s",
            status,
            video_id,
        )
    finally:
        db.close()


def _generate_and_store_transcript_for_video(video_id: str, video_path: str) -> None:
    _best_effort_update_transcript(
        video_id=video_id,
        transcript_text="",
        source="faster_whisper",
        status="processing",
        error_message=None,
        language=None,
    )

    if not ASR_ENABLED:
        _best_effort_update_transcript(
            video_id=video_id,
            transcript_text="",
            source="faster_whisper",
            status="failed",
            error_message="ASR is disabled by configuration.",
            language=None,
        )
        return

    result = _transcribe_video_audio_to_text(Path(video_path))
    if not result:
        _best_effort_update_transcript(
            video_id=video_id,
            transcript_text="",
            source="faster_whisper",
            status="failed",
            error_message="ASR produced no transcript or failed. Check video service logs.",
            language=None,
        )
        return

    transcript_text, language = result
    _best_effort_update_transcript(
        video_id=video_id,
        transcript_text=transcript_text,
        source="faster_whisper",
        status="ready",
        error_message=None,
        language=language,
    )


def serialize_video(video: Video) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "category": video.category,
        "tags": _split_tags(video.tags),
        "thumbnail_url": f"/videos/{video.id}/thumbnail",
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


def _subscriber_user_ids_for_channel(db: Session, channel_user_id: int) -> list[str]:
    rows = (
        db.query(Subscription.subscriber_user_id)
        .filter(Subscription.channel_user_id == str(channel_user_id))
        .all()
    )
    # rows are SQLAlchemy row tuples in this query shape
    return [row[0] for row in rows if row and row[0]]


async def _notify_subscribers_new_video(db: Session, video: Video) -> None:
    if not COMMUNICATION_API_BASE_URL:
        return

    recipient_user_ids = _subscriber_user_ids_for_channel(db, video.uploader_id)
    if not recipient_user_ids:
        return

    payload = {
        "type": "new_video",
        "recipient_user_ids": recipient_user_ids,
        "title": "New video uploaded",
        "message": _truncate_text(
            f"Uploader {video.uploader_id} posted: {video.title}",
            MAX_NOTIFICATION_MESSAGE_LENGTH,
        ),
        "actor_user_id": str(video.uploader_id),
        "channel_id": str(video.uploader_id),
        "video_id": video.id,
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{COMMUNICATION_API_BASE_URL}/comm/notifications",
                json=payload,
            )
            response.raise_for_status()
    except Exception:
        # Notification is best-effort; upload should still succeed.
        logger.exception("Failed to send new-video notifications for video_id=%s", video.id)


@router.get("/ping")
def ping_videos():
    """Health check for videos service"""
    return {"message": "videos route is working"}


@router.post("/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
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

    generated = _generate_first_frame_thumbnail(saved_path, _thumbnail_path(video_id))
    resolved_thumbnail_url = f"/videos/{video_id}/thumbnail" if generated else thumbnail_url

    # Save to database
    video = Video(
        id=video_id,
        title=title,
        description=description,
        category=category,
        tags=tags,
        thumbnail_url=resolved_thumbnail_url,
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
    if ASR_ENABLED:
        _upsert_video_transcript(
            db,
            video_id=video.id,
            transcript_text="",
            source="faster_whisper",
            status="queued",
            error_message=None,
            language=None,
        )
        background_tasks.add_task(_generate_and_store_transcript_for_video, video.id, str(saved_path))
    else:
        _upsert_video_transcript(
            db,
            video_id=video.id,
            transcript_text="",
            source="faster_whisper",
            status="failed",
            error_message="ASR is disabled by configuration.",
            language=None,
        )
    try:
        await _notify_subscribers_new_video(db, video)
    except Exception:
        logger.exception("Unexpected notification error for video_id=%s", video.id)

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


@router.get("/{video_id}/transcript")
def get_video_transcript(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    row = db.query(VideoTranscript).filter(VideoTranscript.video_id == video_id).first()
    if not row:
        return {
            "video_id": video_id,
            "status": "pending",
            "transcript_text": "",
            "source": None,
            "error_message": None,
            "language": None,
            "updated_at": None,
        }

    return {
        "video_id": video_id,
        "status": row.status or "ready",
        "transcript_text": row.transcript_text,
        "source": row.source,
        "error_message": row.error_message,
        "language": row.language,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/{video_id}/play")
def play_video(video_id: str, db: Session = Depends(get_db)):
    """Stream/download video file"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = Path(video.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    # Atomic increment avoids lost updates under concurrent requests.
    db.query(Video).filter(Video.id == video_id).update(
        {Video.views: Video.views + 1},
        synchronize_session=False,
    )
    db.commit()

    return FileResponse(
        path=str(file_path),
        media_type=video.content_type,
        filename=video.original_filename,
    )


@router.get("/{video_id}/thumbnail")
def get_video_thumbnail(video_id: str, db: Session = Depends(get_db)):
    """Serve thumbnail generated from frame 1 of the video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(video.path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    thumbnail_path = _thumbnail_path(video_id)
    if not thumbnail_path.exists():
        generated = _generate_first_frame_thumbnail(video_path, thumbnail_path)
        if not generated:
            raise HTTPException(status_code=404, detail="Thumbnail not available")

    return FileResponse(path=str(thumbnail_path), media_type="image/jpeg", filename=thumbnail_path.name)


@router.patch("/{video_id}")
def update_video(
    video_id: str,
    title: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    tags: str = Form(None),
    requester_uploader_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Update video metadata (title, description, category, tags)"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if requester_uploader_id != video.uploader_id:
        raise HTTPException(status_code=403, detail="You do not own this video")
    
    # Update only provided fields
    if title is not None:
        video.title = title
    if description is not None:
        video.description = description
    if category is not None:
        video.category = category
    if tags is not None:
        video.tags = tags
    
    db.commit()
    db.refresh(video)
    
    return serialize_video(video)



@router.delete("/{video_id}")
def delete_video(
    video_id: str,
    requester_uploader_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Delete video file and metadata"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    if requester_uploader_id != video.uploader_id:
        raise HTTPException(status_code=403, detail="You do not own this video")

    file_path = Path(video.path)
    
    # Try to delete the video file, but don't fail if it's already gone
    if file_path.exists():
        file_path.unlink()
    
    # Clean up thumbnail
    thumbnail_path = _thumbnail_path(video_id)
    if thumbnail_path.exists():
        thumbnail_path.unlink()
    
    # Remove from database
    db.delete(video)
    db.commit()

    return {"message": "Video deleted successfully", "id": video_id}
