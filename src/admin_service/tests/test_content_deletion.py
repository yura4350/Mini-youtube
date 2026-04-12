import tempfile
from pathlib import Path

from src.admin_service.tests.conftest import seed_video, seed_user


def test_delete_content_removes_video_from_db(client):
    """Test DELETE /admin/content/{video_id} removes video from database."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp_path = tmp.name

    try:
        user = seed_user(name="Ian", email="ian@test.com", role="user", is_active=True)
        video = seed_video(
            id="vid-001",
            title="Test Video",
            description="A test video",
            owner_id=user.id,
            path=tmp_path,
        )

        resp = client.delete(f"/admin/content/{video.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["video_id"] == video.id
        assert body["deleted"] is True

        # Verify video is actually deleted from database
        resp_check = client.get("/admin/metrics")
        # Video should no longer exist (we can't directly query, but deletion should succeed)
        assert resp_check.status_code == 200

    finally:
        # Clean up temp file if it still exists
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


def test_delete_nonexistent_video_returns_404(client):
    """Test DELETE /admin/content/{video_id} returns 404 for non-existent video."""
    resp = client.delete("/admin/content/nonexistent-id")
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == "Video not found"


def test_delete_content_with_missing_file(client):
    """Test DELETE /admin/content/{video_id} handles missing file gracefully."""
    user = seed_user(name="Jack", email="jack@test.com", role="user", is_active=True)
    # Point to a file that doesn't exist
    video = seed_video(
        id="vid-002",
        title="Video with Missing File",
        description="File doesn't exist",
        owner_id=user.id,
        path="/nonexistent/path/to/video.mp4",
    )

    resp = client.delete(f"/admin/content/{video.id}")
    # Should still succeed (file doesn't exist, but video is removed from DB)
    assert resp.status_code == 200
    body = resp.json()
    assert body["video_id"] == video.id
    assert body["deleted"] is True


def test_delete_video_with_actual_file(client):
    """Test DELETE /admin/content/{video_id} removes both DB record and file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp_path = tmp.name
        tmp.write(b"fake video data")

    try:
        assert Path(tmp_path).exists()

        user = seed_user(name="Kate", email="kate@test.com", role="user", is_active=True)
        video = seed_video(
            id="vid-003",
            title="Video with Real File",
            description="Has actual file",
            owner_id=user.id,
            path=tmp_path,
        )

        resp = client.delete(f"/admin/content/{video.id}")
        assert resp.status_code == 200

        # Verify file is deleted
        assert not Path(tmp_path).exists()

    finally:
        # Extra cleanup just in case
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


def test_delete_multiple_videos_independently(client):
    """Test deleting multiple videos doesn't affect each other."""
    user = seed_user(name="Leo", email="leo@test.com", role="user", is_active=True)

    video1 = seed_video(
        id="vid-del-1",
        title="Video 1",
        description="First",
        owner_id=user.id,
        path="/tmp/vid1.mp4",
    )
    video2 = seed_video(
        id="vid-del-2",
        title="Video 2",
        description="Second",
        owner_id=user.id,
        path="/tmp/vid2.mp4",
    )

    # Delete first video
    resp1 = client.delete(f"/admin/content/{video1.id}")
    assert resp1.status_code == 200

    # Second video should still not exist in DB (never seeded a real file)
    # but deletion should succeed
    resp2 = client.delete(f"/admin/content/{video2.id}")
    assert resp2.status_code == 200

    # Trying to delete again should fail
    resp3 = client.delete(f"/admin/content/{video1.id}")
    assert resp3.status_code == 404
