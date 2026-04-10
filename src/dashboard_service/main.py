import logging
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal, init_db
from src.video_crud_service.models import Video
from src.video_crud_service.videos import serialize_video
from src.dashboard_service.models import SearchHistory, WatchHistory

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
def search_history(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Return recent search queries for a user in reverse order."""
    logger.info("Search history requested for user %s", user_id)
    rows = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "user_id": user_id,
        "history": [
            {"query": r.query, "searched_at": r.searched_at.isoformat()}
            for r in rows
        ],
    }


@app.get("/subscriptions/feed")
def subscriptions_feed(user_id: str = Query(...)):
    """Return latest videos from channels the user subscribes to, in chronological order.
    TODO: implement once user DB is available
    """
    logger.info("Subscriptions feed requested for user %s", user_id)
    return {"user_id": user_id, "videos": []}


@app.post("/user/history/watched")
def record_watch(
    user_id: str = Query(...),
    video_id: str = Query(...),
    position_seconds: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Record or update a watch event for a user.
       Upserts: if the user has watched this video before, updates last_watched_at and last_position_seconds.
    """
    logger.info("Recording watch for user %s, video %s", user_id, video_id)
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    row = db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.video_id == video_id,
    ).first()

    if row:
        row.last_watched_at = datetime.now(timezone.utc)
        row.last_position_seconds = position_seconds
    else:
        db.add(WatchHistory(
            user_id=user_id,
            video_id=video_id,
            last_position_seconds=position_seconds,
            last_watched_at=datetime.now(timezone.utc),
        ))
    db.commit()
    return {"status": "recorded", "user_id": user_id, "video_id": video_id}


@app.get("/user/history/watched")
def watched_history(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return recently watched videos for a user in reverse chronological order."""
    logger.info("Watch history requested for user %s", user_id)
    rows = (
        db.query(WatchHistory)
        .filter(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.last_watched_at.desc())
        .limit(limit)
        .all()
    )
    video_ids = [r.video_id for r in rows]
    videos_by_id = {
        v.id: v for v in db.query(Video).filter(Video.id.in_(video_ids)).all()
    }
    result = []
    for r in rows:
        if r.video_id in videos_by_id:
            video_data = serialize_video(videos_by_id[r.video_id])
            video_data["last_watched_at"] = r.last_watched_at.isoformat()
            video_data["last_position_seconds"] = r.last_position_seconds
            result.append(video_data)
    return {"user_id": user_id, "videos": result}


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
