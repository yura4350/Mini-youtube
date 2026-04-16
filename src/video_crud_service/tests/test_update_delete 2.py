from src.video_crud_service.models import Video
from .conftest import create_test_video


def test_update_video_title(client, test_db):
    """Test updating video title."""
    video = create_test_video(test_db, title="Original Title", uploader_id=1)
    
    response = client.patch(
        f"/videos/{video.id}",
        data={
            "title": "Updated Title",
            "requester_uploader_id": 1,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


def test_update_video_multiple_fields(client, test_db):
    """Test updating multiple fields."""
    video = create_test_video(test_db)
    
    response = client.patch(
        f"/videos/{video.id}",
        data={
            "title": "New Title",
            "description": "New description",
            "category": "Sports",
            "tags": "new, tags",
            "requester_uploader_id": 1,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == "New description"
    assert data["category"] == "Sports"


def test_update_video_unauthorized(client, test_db):
    """Test that non-owner cannot update video."""
    video = create_test_video(test_db, uploader_id=1)
    
    response = client.patch(
        f"/videos/{video.id}",
        data={
            "title": "Hacked!",
            "requester_uploader_id": 999,  # Different user
        },
    )
    
    assert response.status_code == 403
    assert "do not own" in response.json()["detail"]


def test_update_nonexistent_video(client):
    """Test updating non-existent video."""
    response = client.patch(
        "/videos/nonexistent",
        data={"title": "New", "requester_uploader_id": 1},
    )
    
    assert response.status_code == 404


def test_delete_video(client, test_db):
    """Test deleting a video."""
    video = create_test_video(test_db, uploader_id=1)
    video_id = video.id
    
    response = client.delete(f"/videos/{video_id}?requester_uploader_id=1")
    
    assert response.status_code == 200
    assert response.json()["id"] == video_id
    
    # Verify deleted from database
    deleted = test_db.query(Video).filter(Video.id == video_id).first()
    assert deleted is None


def test_delete_video_unauthorized(client, test_db):
    """Test that non-owner cannot delete video."""
    video = create_test_video(test_db, uploader_id=1)
    
    response = client.delete(f"/videos/{video.id}?requester_uploader_id=999")
    
    assert response.status_code == 403
    assert "do not own" in response.json()["detail"]


def test_delete_nonexistent_video(client):
    """Test deleting non-existent video."""
    response = client.delete("/videos/nonexistent?requester_uploader_id=1")
    
    assert response.status_code == 404
