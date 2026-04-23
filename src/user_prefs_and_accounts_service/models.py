from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapped_column, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    avatar = Column(String, nullable=True)
    hashed_pwd = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserPreferences(Base):
    """Table to store user preferences"""

    __tablename__ = "user_preferences"

    user_id = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    privacy = mapped_column(String, nullable=False, default="public")
    notifications = mapped_column(Boolean, nullable=False, default=True)
    ui_theme = mapped_column(String, nullable=False, default="dark")

    user = relationship("User", back_populates="preferences")