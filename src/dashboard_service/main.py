import logging
import os
import re
import hashlib
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from src.video_crud_service.database import SessionLocal, init_db
from src.video_crud_service.models import Video, VideoTranscript, VideoSummary
from src.video_crud_service.videos import serialize_video
from src.communication_service.models import Notification
from src.dashboard_service.models import SearchHistory, WatchHistory, Subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
COMMUNICATION_API_BASE_URL = os.getenv("COMMUNICATION_API_BASE_URL", "").strip().rstrip("/")
INTELLIGENCE_API_BASE_URL = os.getenv("INTELLIGENCE_API_BASE_URL", "").strip().rstrip("/")
SUMMARY_WAIT_TRANSCRIPT_SECONDS = int(os.getenv("SUMMARY_WAIT_TRANSCRIPT_SECONDS", "12"))
SUMMARY_WAIT_TRANSCRIPT_POLL_SECONDS = float(os.getenv("SUMMARY_WAIT_TRANSCRIPT_POLL_SECONDS", "1.0"))

app = FastAPI(title="Dashboard Service")

_default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://vcm-52418.vm.duke.edu:5173",
    "http://vcm-52527.vm.duke.edu:5173",
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
    force_refresh: bool = Field(default=False)


def _clip_text(value: str, max_length: int) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."


def _build_summary_source_text(
    *,
    db: Session,
    video: Video,
    subtitle_text: str | None,
) -> tuple[str, str]:
    if subtitle_text and subtitle_text.strip():
        return subtitle_text.strip(), "subtitle_text"

    transcript_row = db.query(VideoTranscript).filter(VideoTranscript.video_id == video.id).first()
    transcript_ready = transcript_row and (
        not getattr(transcript_row, "status", None) or getattr(transcript_row, "status", "ready") == "ready"
    )
    if transcript_ready and transcript_row and transcript_row.transcript_text and transcript_row.transcript_text.strip():
        return transcript_row.transcript_text.strip(), "subtitle_text"

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


def _summary_input_hash(source_text: str, source_kind: str, max_sentences: int) -> str:
    material = f"{source_kind}|{max_sentences}|{source_text}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _serialize_summary_row(row: VideoSummary, *, cached: bool = False) -> dict:
    return {
        "video_id": row.video_id,
        "status": row.status,
        "summary": row.summary,
        "source_kind": row.source_kind,
        "generated_at": row.generated_at.isoformat() if row.generated_at else None,
        "provider": row.provider,
        "error_message": row.error_message,
        "cached": cached,
        "retry_count": row.retry_count,
        "duration_ms": row.duration_ms,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _upsert_summary_job(
    db: Session,
    *,
    video_id: str,
    status: str,
    source_kind: str,
    max_sentences: int,
    input_hash: str,
    summary: str | None = None,
    provider: str | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
    bump_retry: bool = False,
) -> VideoSummary:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    row = db.query(VideoSummary).filter(VideoSummary.video_id == video_id).first()
    if row:
        row.status = status
        row.source_kind = source_kind
        row.max_sentences = max_sentences
        row.input_hash = input_hash
        row.summary = summary
        row.provider = provider
        row.error_message = error_message
        row.duration_ms = duration_ms
        row.generated_at = now if status == "ready" else row.generated_at
        row.updated_at = now
        if bump_retry:
            row.retry_count = (row.retry_count or 0) + 1
    else:
        row = VideoSummary(
            video_id=video_id,
            status=status,
            summary=summary,
            source_kind=source_kind,
            provider=provider,
            error_message=error_message,
            input_hash=input_hash,
            max_sentences=max_sentences,
            retry_count=1 if bump_retry else 0,
            duration_ms=duration_ms,
            generated_at=now if status == "ready" else None,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


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


def _proxy_ai_summarize_sync(payload: dict) -> dict | None:
    if not INTELLIGENCE_API_BASE_URL:
        return None

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                f"{INTELLIGENCE_API_BASE_URL}/ai/summarize",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            result["provider"] = "intelligence_service"
            return result
    except Exception:
        logger.exception("Failed to proxy AI summarize synchronously to intelligence service")
        return None


def _run_summary_job(
    *,
    db_bind,
    video_id: str,
    source_text: str,
    source_kind: str,
    max_sentences: int,
    input_hash: str,
) -> None:
    session_factory = sessionmaker(bind=db_bind, autocommit=False, autoflush=False)
    db = session_factory()
    started = time.perf_counter()
    try:
        _upsert_summary_job(
            db,
            video_id=video_id,
            status="processing",
            source_kind=source_kind,
            max_sentences=max_sentences,
            input_hash=input_hash,
            summary=None,
            provider=None,
            error_message=None,
            duration_ms=None,
        )

        if source_kind == "video_metadata":
            deadline = time.time() + max(0, SUMMARY_WAIT_TRANSCRIPT_SECONDS)
            while time.time() < deadline:
                transcript_row = (
                    db.query(VideoTranscript)
                    .filter(VideoTranscript.video_id == video_id)
                    .first()
                )
                if not transcript_row:
                    break
                transcript_status = (transcript_row.status or "").strip().lower()
                if transcript_status == "ready" and (transcript_row.transcript_text or "").strip():
                    source_text = transcript_row.transcript_text.strip()
                    source_kind = "subtitle_text"
                    input_hash = _summary_input_hash(source_text, source_kind, max_sentences)
                    break
                if transcript_status == "failed":
                    break
                if transcript_status in {"queued", "processing", "pending", ""}:
                    time.sleep(max(0.1, SUMMARY_WAIT_TRANSCRIPT_POLL_SECONDS))
                    continue
                break

        proxied = _proxy_ai_summarize_sync(
            {
                "video_id": video_id,
                "source_text": source_text,
                "source_kind": source_kind,
                "max_sentences": max_sentences,
            }
        )
        if proxied and proxied.get("summary"):
            summary = _clip_text(str(proxied["summary"]), 500)
            provider = str(proxied.get("provider") or "intelligence_service")
        else:
            summary = _summarize_mvp(source_text, max_sentences)
            provider = "dashboard_fallback"

        duration_ms = int((time.perf_counter() - started) * 1000)
        row = _upsert_summary_job(
            db,
            video_id=video_id,
            status="ready",
            source_kind=source_kind,
            max_sentences=max_sentences,
            input_hash=input_hash,
            summary=summary,
            provider=provider,
            error_message=None,
            duration_ms=duration_ms,
        )
        logger.info(
            "ai_summary_ready video_id=%s status=%s source_kind=%s provider=%s chars=%s duration_ms=%s retries=%s",
            row.video_id,
            row.status,
            row.source_kind,
            row.provider,
            len(row.summary or ""),
            row.duration_ms,
            row.retry_count,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        try:
            row = _upsert_summary_job(
                db,
                video_id=video_id,
                status="failed",
                source_kind=source_kind,
                max_sentences=max_sentences,
                input_hash=input_hash,
                summary=None,
                provider=None,
                error_message=str(exc)[:500],
                duration_ms=duration_ms,
            )
            logger.error(
                "ai_summary_failed video_id=%s status=%s source_kind=%s duration_ms=%s error=%s",
                row.video_id,
                row.status,
                row.source_kind,
                row.duration_ms,
                row.error_message,
            )
        except Exception:
            logger.exception("Failed to persist failed ai summary state video_id=%s", video_id)
    finally:
        db.close()


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


@app.get("/ai/summarize/{video_id}")
def ai_summarize_status(video_id: str, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    row = db.query(VideoSummary).filter(VideoSummary.video_id == video_id).first()
    if not row:
        return {
            "video_id": video_id,
            "status": "pending",
            "summary": None,
            "source_kind": None,
            "generated_at": None,
            "provider": None,
            "error_message": None,
            "cached": False,
            "retry_count": 0,
            "duration_ms": None,
            "updated_at": None,
        }
    return _serialize_summary_row(row, cached=False)


@app.post("/ai/summarize")
async def ai_summarize(
    payload: SummarizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    video = db.query(Video).filter(Video.id == payload.video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    source_text, source_kind = _build_summary_source_text(
        db=db,
        video=video,
        subtitle_text=payload.subtitle_text,
    )
    input_hash = _summary_input_hash(source_text, source_kind, payload.max_sentences)
    row = db.query(VideoSummary).filter(VideoSummary.video_id == video.id).first()
    if row and row.input_hash == input_hash and not payload.force_refresh:
        if row.status == "ready":
            return _serialize_summary_row(row, cached=True)
        if row.status in {"queued", "processing"}:
            return _serialize_summary_row(row, cached=False)

    queued = _upsert_summary_job(
        db,
        video_id=video.id,
        status="queued",
        source_kind=source_kind,
        max_sentences=payload.max_sentences,
        input_hash=input_hash,
        summary=None,
        provider=None,
        error_message=None,
        duration_ms=None,
        bump_retry=payload.force_refresh,
    )
    background_tasks.add_task(
        _run_summary_job,
        db_bind=db.get_bind(),
        video_id=video.id,
        source_text=source_text,
        source_kind=source_kind,
        max_sentences=payload.max_sentences,
        input_hash=input_hash,
    )
    return _serialize_summary_row(queued, cached=False)


@app.post("/ai/summarize/{video_id}/retry")
async def ai_summarize_retry(
    video_id: str,
    background_tasks: BackgroundTasks,
    max_sentences: int = Query(3, ge=1, le=5),
    db: Session = Depends(get_db),
):
    payload = SummarizeRequest(
        video_id=video_id,
        subtitle_text=None,
        max_sentences=max_sentences,
        force_refresh=True,
    )
    return await ai_summarize(payload=payload, background_tasks=background_tasks, db=db)


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
