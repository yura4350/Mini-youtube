import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Set DATABASE_URL before importing main.py
os.environ["DATABASE_URL"] = "sqlite://"

from src.admin_service.main import app, get_db  # noqa: E402
from src.admin_service.models import AdminBase, User  # noqa: E402
from src.video_crud_service.models import Base as VideoBase  # noqa: E402
from src.video_crud_service.models import Video  # noqa: E402

# Create in-memory SQLite engine for testing
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the get_db dependency to use test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    """Create and drop database schema for each test."""
    # Create both User and Video tables
    AdminBase.metadata.create_all(bind=engine)
    VideoBase.metadata.create_all(bind=engine)
    yield
    AdminBase.metadata.drop_all(bind=engine)
    VideoBase.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    """Provide direct database session for seeding test data."""
    db_session = TestingSessionLocal()
    yield db_session
    db_session.close()


@pytest.fixture
def client(db):
    """Provide a TestClient with overridden database dependency."""
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def seed_user(
    db: Session,
    *,
    name: str,
    email: str,
    role: str,
    is_active: bool = True,
):
    """Seed a test user into the test database."""
    user = User(
        name=name,
        email=email,
        role=role,
        hashed_pwd="hashed_password_mock",
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_video(
    db: Session,
    *,
    id: str,
    title: str,
    description: str,
    owner_id: int,
    path: str,
    views: int = 0,
):
    """Seed a test video into the test database."""
    video = Video(
        id=id,
        title=title,
        description=description,
        owner_id=owner_id,
        path=path,
        views=views,
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video
