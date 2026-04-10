import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Must be set before importing service module
os.environ["DATABASE_URL"] = "sqlite://"

from src.user_prefs_and_accounts_service.main import (  # noqa: E402
    Base,
    User,
    app,
    get_current_active_user,
    get_db,
    get_pwd_hash,
)

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def seed_user(
    *,
    name: str,
    email: str,
    role: str,
    password: str,
    is_active: bool = True,
):
    db = TestingSessionLocal()
    try:
        user = User(
            name=name,
            email=email,
            role=role,
            hashed_pwd=get_pwd_hash(password),
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def make_current_user_override(user_id: int):
    def _override():
        db = TestingSessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    return _override


def test_update_own_profile_success(client):
    current = seed_user(
        name="Old Name",
        email="old@example.com",
        role="user",
        password="secret123",
        is_active=True,
    )

    db = TestingSessionLocal()
    try:
        original_hashed_pwd = db.query(User).filter(User.id == current.id).first().hashed_pwd
    finally:
        db.close()

    app.dependency_overrides[get_current_active_user] = make_current_user_override(current.id)

    payload = {
        "name": "New Name",
        "email": "new@example.com",
        "role": "creator",
        # required by UserCreate, but endpoint currently ignores it
        "password": "new-password-that-should-not-be-used",
    }

    resp = client.put("/user/profile/edit", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == current.id
    assert body["name"] == payload["name"]
    assert body["email"] == payload["email"]
    assert body["role"] == payload["role"]
    assert body["is_active"] is True
    assert "hashed_pwd" not in body
    assert "password" not in body

    db = TestingSessionLocal()
    try:
        updated = db.query(User).filter(User.id == current.id).first()
        assert updated is not None
        assert updated.name == payload["name"]
        assert updated.email == payload["email"]
        assert updated.role == payload["role"]
        # current endpoint does not update password/hash
        assert updated.hashed_pwd == original_hashed_pwd
    finally:
        db.close()


def test_update_own_profile_user_not_found(client):
    # Auth dependency returns a user-like object with id that doesn't exist in DB
    # so endpoint hits "User does not exist"
    class MissingUser:
        id = 999999
        is_active = True

    app.dependency_overrides[get_current_active_user] = lambda: MissingUser()

    payload = {
        "name": "Any",
        "email": "any@example.com",
        "role": "user",
        "password": "secret123",
    }

    resp = client.put("/user/profile/edit", json=payload)

    assert resp.status_code == 404
    assert resp.json()["detail"] == "User does not exist"


def test_update_own_profile_requires_auth(client):
    # No auth override -> should fail get_current_active_user dependency
    payload = {
        "name": "No Auth",
        "email": "noauth@example.com",
        "role": "user",
        "password": "secret123",
    }

    resp = client.put("/user/profile/edit", json=payload)

    assert resp.status_code == 401


def test_update_own_profile_invalid_payload_returns_422(client):
    current = seed_user(
        name="User",
        email="user@example.com",
        role="user",
        password="secret123",
        is_active=True,
    )
    app.dependency_overrides[get_current_active_user] = make_current_user_override(current.id)

    # Missing required fields from UserCreate
    payload = {
        "name": "Only Name",
    }

    resp = client.put("/user/profile/edit", json=payload)

    assert resp.status_code == 422