from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Set
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.video_crud_service.database import SessionLocal, init_db
from .models import Notification

app = FastAPI(title="Communication Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://vcm-52418.vm.duke.edu:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_rooms: Dict[str, Set[WebSocket]] = {}
chat_history: Dict[str, List[dict]] = {}
MAX_CHAT_HISTORY_PER_ROOM = 100
direct_chat_rooms: Dict[str, Set[WebSocket]] = {}
direct_chat_history: Dict[str, List[dict]] = {}
MAX_DIRECT_CHAT_HISTORY_PER_ROOM = 200


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def broadcast_to_room(video_id: str, payload: dict):
    sockets = list(chat_rooms.get(video_id, set()))
    stale_sockets: List[WebSocket] = []

    for socket in sockets:
        try:
            await socket.send_json(payload)
        except Exception:
            stale_sockets.append(socket)

    if stale_sockets and video_id in chat_rooms:
        for socket in stale_sockets:
            chat_rooms[video_id].discard(socket)


def _direct_room_key(user_a: str, user_b: str) -> str:
    left, right = sorted([user_a, user_b])
    return f"{left}::{right}"


async def broadcast_to_direct_room(room_key: str, payload: dict):
    sockets = list(direct_chat_rooms.get(room_key, set()))
    stale_sockets: List[WebSocket] = []

    for socket in sockets:
        try:
            await socket.send_json(payload)
        except Exception:
            stale_sockets.append(socket)

    if stale_sockets and room_key in direct_chat_rooms:
        for socket in stale_sockets:
            direct_chat_rooms[room_key].discard(socket)


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


@app.websocket("/comm/real-time-chat")
async def real_time_chat(websocket: WebSocket):
    await websocket.accept()

    video_id = (websocket.query_params.get("video_id") or "").strip()
    user_id = (websocket.query_params.get("user_id") or "").strip()
    username = (websocket.query_params.get("username") or "").strip()

    if not video_id or not user_id or not username:
        await websocket.send_json(
            {
                "type": "error",
                "message": "video_id, user_id and username are required",
            }
        )
        await websocket.close(code=1008)
        return

    room = chat_rooms.setdefault(video_id, set())
    room.add(websocket)

    history = chat_history.get(video_id, [])
    await websocket.send_json(
        {
            "type": "history",
            "video_id": video_id,
            "messages": history[-50:],
        }
    )

    await broadcast_to_room(
        video_id,
        {
            "type": "system",
            "video_id": video_id,
            "user_id": user_id,
            "username": username,
            "message": f"{username} joined the chat",
            "timestamp": _now_iso(),
        },
    )

    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message") or "").strip()
            if not message:
                continue

            event = {
                "type": "chat_message",
                "video_id": video_id,
                "user_id": user_id,
                "username": username,
                "message": message[:2000],
                "timestamp": _now_iso(),
            }

            room_history = chat_history.setdefault(video_id, [])
            room_history.append(event)
            if len(room_history) > MAX_CHAT_HISTORY_PER_ROOM:
                chat_history[video_id] = room_history[-MAX_CHAT_HISTORY_PER_ROOM:]

            await broadcast_to_room(video_id, event)
    except WebSocketDisconnect:
        pass
    finally:
        if video_id in chat_rooms:
            chat_rooms[video_id].discard(websocket)
            if not chat_rooms[video_id]:
                chat_rooms.pop(video_id, None)

        await broadcast_to_room(
            video_id,
            {
                "type": "system",
                "video_id": video_id,
                "user_id": user_id,
                "username": username,
                "message": f"{username} left the chat",
                "timestamp": _now_iso(),
            },
        )


@app.websocket("/comm/direct-chat")
async def direct_chat(websocket: WebSocket):
    await websocket.accept()

    user_id = (websocket.query_params.get("user_id") or "").strip()
    username = (websocket.query_params.get("username") or "").strip()
    peer_id = (websocket.query_params.get("peer_id") or "").strip()

    if not user_id or not username or not peer_id:
        await websocket.send_json(
            {
                "type": "error",
                "message": "user_id, username and peer_id are required",
            }
        )
        await websocket.close(code=1008)
        return

    if user_id == peer_id:
        await websocket.send_json(
            {
                "type": "error",
                "message": "peer_id must be different from user_id",
            }
        )
        await websocket.close(code=1008)
        return

    room_key = _direct_room_key(user_id, peer_id)
    room = direct_chat_rooms.setdefault(room_key, set())
    room.add(websocket)

    history = direct_chat_history.get(room_key, [])
    await websocket.send_json(
        {
            "type": "history",
            "room_key": room_key,
            "messages": history[-80:],
        }
    )

    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message") or "").strip()
            if not message:
                continue

            event = {
                "type": "direct_message",
                "room_key": room_key,
                "sender_user_id": user_id,
                "sender_username": username,
                "peer_user_id": peer_id,
                "message": message[:2000],
                "timestamp": _now_iso(),
            }

            room_history = direct_chat_history.setdefault(room_key, [])
            room_history.append(event)
            if len(room_history) > MAX_DIRECT_CHAT_HISTORY_PER_ROOM:
                direct_chat_history[room_key] = room_history[-MAX_DIRECT_CHAT_HISTORY_PER_ROOM:]

            await broadcast_to_direct_room(room_key, event)
    except WebSocketDisconnect:
        pass
    finally:
        if room_key in direct_chat_rooms:
            direct_chat_rooms[room_key].discard(websocket)
            if not direct_chat_rooms[room_key]:
                direct_chat_rooms.pop(room_key, None)
