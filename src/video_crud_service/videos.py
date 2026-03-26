from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/videos", tags=["videos"])

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# TODO: Replace in-memory store with proper database for persistence
videos_db = {}


@router.get("/ping")
def ping_videos():
    """Health check for videos service"""
    return {"message": "videos route is working"}


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    uploader_id: int = Form(...)
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

    metadata = {
        "id": video_id,
        "title": title,
        "uploader_id": uploader_id,
        "original_filename": file.filename,
        "saved_filename": saved_name,
        "content_type": file.content_type,
        "size": len(content),
        "path": str(saved_path),
    }
    videos_db[video_id] = metadata
    return metadata


@router.get("")
def get_all_videos():
    """List all uploaded videos"""
    return list(videos_db.values())


@router.get("/{video_id}")
def get_video(video_id: str):
    """Retrieve video metadata by ID"""
    video = videos_db.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/play")
def play_video(video_id: str):
    """Stream/download video file"""
    video = videos_db.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = Path(video["path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    return FileResponse(
        path=str(file_path),
        media_type=video.get("content_type", "application/octet-stream"),
        filename=video.get("original_filename", file_path.name),
    )


@router.delete("/{video_id}")
def delete_video(video_id: str):
    """Delete video file and metadata"""
    video = videos_db.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    file_path = Path(video["path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")

    file_path.unlink()
    del videos_db[video_id]

    return {"message": "Video deleted successfully", "id": video_id}