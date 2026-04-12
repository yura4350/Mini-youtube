import logging
import os
import re
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal, init_db
from src.video_crud_service.models import Video
from src.video_crud_service.videos import serialize_video
from src.communication_service.models import Notification
from src.dashboard_service.models import SearchHistory, WatchHistory, Subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
COMMUNICATION_API_BASE_URL = os.getenv("COMMUNICATION_API_BASE_URL", "").strip().rstrip("/")
INTELLIGENCE_API_BASE_URL = os.getenv("INTELLIGENCE_API_BASE_URL", "").strip().rstrip("/")

app = FastAPI(title="Dashboard Service")

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://vcm-52418.vm.duke.edu:5173",
]
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


async def _send_subscription_notifications(subscriber_user_id: str, channel_user_id: str) -> None:
    if not COMMUNICATION_API_BASE_URL:
        return

    payloads = [
        {
            "type": "subscription",
            "recipient_user_ids": [subscriber_user_id],
            "title": "Subscription confirmed",
            "message": f"You subscribed to channel {channel_user_id}.",
            "actor_user_id": channel_user_id,
            "channel_id": channel_user_id,
            "video_id": None,
        },
        {
            "type": "subscription",
            "recipient_user_ids": [channel_user_id],
            "title": "New subscriber",
            "message": f"User {subscriber_user_id} subscribed to your channel.",
            "actor_user_id": subscriber_user_id,
            "channel_id": channel_user_id,
            "video_id": None,
        },
    ]

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            for payload in payloads:
                response = await client.post(
                    f"{COMMUNICATION_API_BASE_URL}/comm/notifications",
                    json=payload,
                )
                response.raise_for_status()
    except Exception:
        # Notification is best-effort. Core subscription flow should still succeed.
        logger.exception(
            "Failed to send subscription notifications subscriber=%s channel=%s",
            subscriber_user_id,
            channel_user_id,
        )


class SummarizeRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    subtitle_text: str | None = Field(default=None, min_length=1, max_length=20000)
    max_sentences: int = Field(default=3, ge=1, le=5)


def _clip_text(value: str, max_length: int) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."


def _build_summary_source_text(video: Video, subtitle_text: str | None) -> tuple[str, str]:
    if subtitle_text and subtitle_text.strip():
        return subtitle_text.strip(), "subtitle_text"

    tags = ", ".join([tag.strip() for tag in (video.tags or "").split(",") if tag.strip()])
    metadata_text = (
        f"Title: {video.title}. "
        f"Description: {video.description or 'No description provided.'}. "
        f"Category: {video.category or 'General'}. "
        f"Tags: {tags or 'none'}."
    )
    return metadata_text, "video_metadata"


def _summarize_mvp(source_text: str, max_sentences: int) -> str:
    normalized = " ".join(source_text.split())
    sentence_candidates = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
    chosen = sentence_candidates[:max_sentences]

    if not chosen:
        chosen = [_clip_text(normalized, 220)]

    summary = " ".join(chosen)
    return _clip_text(summary, 500)


async def _proxy_ai_health() -> dict | None:
    if not INTELLIGENCE_API_BASE_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{INTELLIGENCE_API_BASE_URL}/ai/health")
            response.raise_for_status()
            payload = response.json()
            payload["provider"] = "intelligence_service"
            return payload
    except Exception:
        logger.exception("Failed to fetch AI health from intelligence service")
        return None


async def _proxy_ai_summarize(payload: dict) -> dict | None:
    if not INTELLIGENCE_API_BASE_URL:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{INTELLIGENCE_API_BASE_URL}/ai/summarize",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            result["provider"] = "intelligence_service"
            return result
    except Exception:
        logger.exception("Failed to proxy AI summarize to intelligence service")
        return None


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard"}


@app.get("/ai/health")
async def ai_health():
    proxied = await _proxy_ai_health()
    if proxied:
        return proxied

    return {
        "status": "ok",
        "service": "ai-intelligence-mvp",
        "provider": "dashboard_fallback",
    }


@app.post("/ai/summarize")
async def ai_summarize(payload: SummarizeRequest, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == payload.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    source_text, source_kind = _build_summary_source_text(video, payload.subtitle_text)
    proxied = await _proxy_ai_summarize(
        {
            "video_id": video.id,
            "source_text": source_text,
            "source_kind": source_kind,
            "max_sentences": payload.max_sentences,
        }
    )
    if proxied:
        return proxied

    summary = _summarize_mvp(source_text, payload.max_sentences)

    return {
        "video_id": video.id,
        "summary": summary,
        "source_kind": source_kind,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "dashboard_fallback",
    }


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
def subscriptions_feed(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Return latest videos from channels the user subscribes to, in reverse chronological order."""
    logger.info("Subscriptions feed requested for user %s", user_id)
    subs = db.query(Subscription).filter(Subscription.subscriber_user_id == user_id).all()
    channel_ids = [s.channel_user_id for s in subs]
    if not channel_ids:
        return {"user_id": user_id, "videos": []}
    videos = (
        db.query(Video)
        .filter(Video.uploader_id.in_([int(c) for c in channel_ids]))
        .order_by(Video.created_at.desc())
        .limit(limit)
        .all()
    )
    return {"user_id": user_id, "videos": [serialize_video(v) for v in videos]}


@app.get("/subscriptions")
def list_subscriptions(
    user_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """List channel user IDs that the given user is subscribed to."""
    rows = (
        db.query(Subscription)
        .filter(Subscription.subscriber_user_id == user_id)
        .order_by(Subscription.created_at.desc())
        .all()
    )
    return {
        "user_id": user_id,
        "channel_user_ids": [row.channel_user_id for row in rows],
        "count": len(rows),
    }


@app.post("/subscriptions")
async def subscribe(
    subscriber_user_id: str = Query(..., min_length=1),
    channel_user_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Create a subscription relationship (idempotent)."""
    if subscriber_user_id == channel_user_id:
        raise HTTPException(status_code=400, detail="You cannot subscribe to yourself")

    existing = (
        db.query(Subscription)
        .filter(Subscription.subscriber_user_id == subscriber_user_id)
        .filter(Subscription.channel_user_id == channel_user_id)
        .first()
    )
    if existing:
        return {
            "subscriber_user_id": subscriber_user_id,
            "channel_user_id": channel_user_id,
            "subscribed": True,
        }

    db.add(
        Subscription(
            subscriber_user_id=subscriber_user_id,
            channel_user_id=channel_user_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()
    await _send_subscription_notifications(subscriber_user_id, channel_user_id)

    return {
        "subscriber_user_id": subscriber_user_id,
        "channel_user_id": channel_user_id,
        "subscribed": True,
    }


@app.delete("/subscriptions")
def unsubscribe(
    subscriber_user_id: str = Query(..., min_length=1),
    channel_user_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """Delete an existing subscription relationship."""
    row = (
        db.query(Subscription)
        .filter(Subscription.subscriber_user_id == subscriber_user_id)
        .filter(Subscription.channel_user_id == channel_user_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(row)
    db.commit()

    return {
        "subscriber_user_id": subscriber_user_id,
        "channel_user_id": channel_user_id,
        "subscribed": False,
    }


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
def notifications(
    user_id: str = Query(...),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Return recent notifications (read/unread) for a user in reverse chronological order."""
    logger.info("Notifications requested for user %s", user_id)
    query = db.query(Notification).filter(Notification.recipient_user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    rows = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return {
        "user_id": user_id,
        "notifications": [
            {
                "notification_id": r.notification_id,
                "type": r.type,
                "title": r.title,
                "message": r.message,
                "actor_user_id": r.actor_user_id,
                "video_id": r.video_id,
                "is_read": r.is_read,
                "read_at": r.read_at.isoformat() if r.read_at else None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@app.get("/dashboard/recommend")
def recommend(db: Session = Depends(get_db)):
    """Return videos ordered by newest first.
    TODO: personalize recommendations based on user preferences and watch history in the future.
    """
    logger.info("Recommend requested")
    videos = db.query(Video).order_by(Video.created_at.desc()).all()
    return {"videos": [serialize_video(v) for v in videos]}
