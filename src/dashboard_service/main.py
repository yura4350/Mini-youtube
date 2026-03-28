import logging

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal
from src.video_crud_service.models import Video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dashboard Service")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _video_summary(v: Video) -> dict:
    return {
        "id": v.id,
        "title": v.title,
        "uploader_id": v.uploader_id,
        "content_type": v.content_type,
        "size": v.size,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard"}


@app.get("/dashboard/recommend")
def recommend(db: Session = Depends(get_db)):
    """Return videos ordered by newest first.
    TODO: personalize recommendations based on user preferences and watch history in the future.
    """
    logger.info("Recommend requested")
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return {"videos": [_video_summary(v) for v in videos]}
