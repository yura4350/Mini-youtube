from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from src.video_crud_service.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    query = Column(String, nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
