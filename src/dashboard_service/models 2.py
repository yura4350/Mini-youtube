from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from src.video_crud_service.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    query = Column(String, nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    video_id = Column(String, nullable=False)
    last_position_seconds = Column(Integer, nullable=False, default=0)
    last_watched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Ensure a user can only have one watch history entry per video
    __table_args__ = (UniqueConstraint("user_id", "video_id", name="uq_watch_history_user_video"),)


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscriber_user_id = Column(String, primary_key=True, nullable=False, index=True)
    channel_user_id = Column(String, primary_key=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
