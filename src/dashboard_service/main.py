import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal, init_db
from src.video_crud_service.models import Video
from src.video_crud_service.videos import serialize_video
from src.dashboard_service.models import SearchHistory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dashboard Service")

_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard"}


@app.get("/search")
def search(
    q: str = Query(..., min_length=1),
    user_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """Filter and rank videos by keyword match on title.
       Called when the user submits a search query.
       If user_id is provided, the query is recorded in search history.
       Returns full video objects for all matches.
    """
    logger.info("Search requested: %s", q)
    videos = db.query(Video).filter(Video.title.ilike(f"%{q}%")).all()

    if user_id:
        db.add(SearchHistory(user_id=user_id, query=q, searched_at=datetime.now(timezone.utc)))
        db.commit()

    return {"query": q, "results": [serialize_video(v) for v in videos]}


@app.get("/search/suggestions")
def search_suggestions(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Return up to 10 video title suggestions matching the query.
       Called when the user types in the search bar (expect to be called for every keystroke).       
       Returns a list of suggested video titles (not full video objects)
    """
    logger.info("Search suggestions requested: %s", q)
    rows = db.query(Video.title).filter(Video.title.ilike(f"%{q}%")).limit(10).all()
    return {"query": q, "suggestions": [row.title for row in rows]}


@app.get("/search/history")
def search_history(user_id: str = Query(...)):
    """Return recent search queries for a user.
    TODO: implement once user DB is available.
    """
    logger.info("Search history requested for user %s", user_id)
    return {"user_id": user_id, "history": []}


@app.get("/subscriptions/feed")
def subscriptions_feed(user_id: str = Query(...)):
    """Return latest videos from channels the user subscribes to, in chronological order.
    TODO: implement once user DB is available
    """
    logger.info("Subscriptions feed requested for user %s", user_id)
    return {"user_id": user_id, "videos": []}


@app.get("/user/history/watched")
def watched_history(user_id: str = Query(...)):
    """Return recently watched videos for a user in reverse chronological order.
    TODO: implement once user DB is available.
    """
    logger.info("Watch history requested for user %s", user_id)
    return {"user_id": user_id, "videos": []}


@app.get("/user/notifications")
def notifications(user_id: str = Query(...)):
    """Return recent notifications (read/unread) for a user.
    TODO: implement once user DB is available.
    """
    logger.info("Notifications requested for user %s", user_id)
    return {"user_id": user_id, "notifications": []}


@app.get("/dashboard/recommend")
def recommend(db: Session = Depends(get_db)):
    """Return videos ordered by newest first.
    TODO: personalize recommendations based on user preferences and watch history in the future.
    """
    logger.info("Recommend requested")
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return {"videos": [serialize_video(v) for v in videos]}
