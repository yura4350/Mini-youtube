import logging

from fastapi import FastAPI, Depends, Query
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


@app.get("/search")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Filter and rank videos by keyword match on title.
       Called when the user submits a search query.
       Returns full video objects for all matches.
    """
    logger.info("Search requested: %s", q)
    videos = db.query(Video).filter(Video.title.ilike(f"%{q}%")).all()
    return {"query": q, "results": [_video_summary(v) for v in videos]}


@app.get("/search/suggestions")
def search_suggestions(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Return up to 10 video title suggestions matching the query.
       Called when the user types in the search bar (expect to be called for every keystroke).       
       Returns a list of suggested video titles (not full video objects)
    """
    logger.info("Search suggestions requested: %s", q)
    rows = db.query(Video.title).filter(Video.title.ilike(f"%{q}%")).limit(10).all()
    return {"query": q, "suggestions": [row.title for row in rows]}


@app.get("/dashboard/recommend")
def recommend(db: Session = Depends(get_db)):
    """Return videos ordered by newest first.
    TODO: personalize recommendations based on user preferences and watch history in the future.
    """
    logger.info("Recommend requested")
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return {"videos": [_video_summary(v) for v in videos]}
