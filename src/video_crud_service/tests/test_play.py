from pathlib import Path

from src.video_crud_service.models import Video
from .conftest import create_test_video


def test_play_video_increments_view_count(client, test_db, tmp_path):
    """Playing a valid video increments views by one."""
    file_path = tmp_path / "playable.mp4"
    file_path.write_bytes(b"video-data")

    video = create_test_video(test_db, path=str(file_path), views=2)

    response = client.get(f"/videos/{video.id}/play")
    assert response.status_code == 200

    test_db.expire_all()
    updated = test_db.query(Video).filter(Video.id == video.id).first()
    assert updated is not None
    assert updated.views == 3


def test_play_video_not_found_does_not_increment(client, test_db):
    """Missing video returns 404 and does not create/modify records."""
    before = test_db.query(Video).count()

    response = client.get("/videos/does-not-exist/play")
    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"

    after = test_db.query(Video).count()
    assert after == before


def test_play_video_missing_file_does_not_increment(client, test_db, tmp_path):
    """Existing video with missing file returns 404 and leaves views unchanged."""
    missing_path = tmp_path / "missing.mp4"
    video = create_test_video(test_db, path=str(missing_path), views=4)

    response = client.get(f"/videos/{video.id}/play")
    assert response.status_code == 404
    assert response.json()["detail"] == "Stored file not found"

    test_db.expire_all()
    unchanged = test_db.query(Video).filter(Video.id == video.id).first()
    assert unchanged is not None
    assert unchanged.views == 4
