from datetime import datetime, timezone
from enum import Enum
from typing import List
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal, init_db
from .models import Notification

app = FastAPI(title="Communication Service")


class NotificationType(str, Enum):
    NEW_VIDEO = "new_video"
    SUBSCRIPTION = "subscription"


class NotificationCreate(BaseModel):
    type: NotificationType
    recipient_user_ids: List[str] = Field(..., min_items=1)
    title: str = Field(..., min_length=1, max_length=120)
    message: str = Field(..., min_length=1, max_length=2000)
    actor_user_id: str | None = None
    channel_id: str | None = None
    video_id: str | None = None


class NotificationRecord(BaseModel):
    notification_id: str
    type: NotificationType
    recipient_user_id: str
    title: str
    message: str
    actor_user_id: str | None
    channel_id: str | None
    video_id: str | None
    created_at: str


class MarkNotificationReadRequest(BaseModel):
    notification_ids: List[str] = Field(..., min_items=1)
    recipient_user_id: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    # Ensure notification table exists before serving requests.
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "communication"}


@app.post("/comm/notifications")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)) -> dict:
    """Create and route notification alerts to recipient inboxes."""
    created_at = datetime.now(timezone.utc)
    routed_to: List[str] = []
    created_ids: List[str] = []
    db_rows: List[Notification] = []

    for recipient_user_id in payload.recipient_user_ids:
        notification_id = str(uuid4())
        record = Notification(
            notification_id=notification_id,
            type=payload.type.value,
            recipient_user_id=recipient_user_id,
            title=payload.title,
            message=payload.message,
            actor_user_id=payload.actor_user_id,
            channel_id=payload.channel_id,
            video_id=payload.video_id,
            created_at=created_at,
        )
        db_rows.append(record)
        routed_to.append(recipient_user_id)
        created_ids.append(notification_id)

    db.add_all(db_rows)
    db.commit()

    return {
        "status": "routed",
        "notification_type": payload.type,
        "routed_count": len(routed_to),
        "routed_to": routed_to,
        "notification_ids": created_ids,
        "created_at": created_at.isoformat(),
    }


@app.get("/comm/notifications")
def get_notifications(
    user_id: str = Query(..., min_length=1),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    """Fetch notifications for a user inbox."""
    query = db.query(Notification).filter(Notification.recipient_user_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    rows = (
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    notifications = [
        {
            "notification_id": row.notification_id,
            "type": row.type,
            "recipient_user_id": row.recipient_user_id,
            "title": row.title,
            "message": row.message,
            "actor_user_id": row.actor_user_id,
            "channel_id": row.channel_id,
            "video_id": row.video_id,
            "is_read": row.is_read,
            "read_at": row.read_at.isoformat() if row.read_at else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]

    return {
        "user_id": user_id,
        "count": len(notifications),
        "unread_only": unread_only,
        "notifications": notifications,
    }


@app.patch("/comm/notifications/read")
def mark_notifications_read(
    payload: MarkNotificationReadRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Mark one or more notifications as read."""
    query = db.query(Notification).filter(Notification.notification_id.in_(payload.notification_ids))
    if payload.recipient_user_id:
        query = query.filter(Notification.recipient_user_id == payload.recipient_user_id)

    rows = query.all()
    if not rows:
        raise HTTPException(status_code=404, detail="Notification not found")

    read_at = datetime.now(timezone.utc)
    updated_count = 0
    for row in rows:
        if not row.is_read:
            row.is_read = True
            row.read_at = read_at
            updated_count += 1

    db.commit()

    return {
        "status": "updated",
        "matched_count": len(rows),
        "updated_count": updated_count,
        "read_at": read_at.isoformat(),
    }
