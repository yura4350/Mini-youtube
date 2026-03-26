from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    uploader_id = Column(Integer, nullable=False)
    original_filename = Column(String, nullable=False)
    saved_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)