from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False, default="")
    category = Column(String, nullable=False, default="Education")
    tags = Column(String, nullable=False, default="")
    thumbnail_url = Column(String, nullable=False, default="")
    uploader_id = Column(Integer, nullable=False)
    original_filename = Column(String, nullable=False)
    saved_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    views = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)