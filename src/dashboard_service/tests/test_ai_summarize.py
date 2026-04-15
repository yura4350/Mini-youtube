from .conftest import create_test_video, create_test_transcript


def test_ai_health(client):
    response = client.get("/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-intelligence-mvp"


def test_ai_summarize_video_not_found(client):
    response = client.post("/ai/summarize", json={"video_id": "missing"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"


def test_ai_summarize_from_video_metadata(client, test_db):
    video = create_test_video(
        test_db,
        title="Intro to Distributed Systems",
        uploader_id=7,
    )

    response = client.post(
        "/ai/summarize",
        json={"video_id": video.id, "max_sentences": 2},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["video_id"] == video.id
    assert data["source_kind"] == "video_metadata"
    assert isinstance(data["summary"], str)
    assert len(data["summary"]) > 0
    assert "Intro to Distributed Systems" in data["summary"]


def test_ai_summarize_uses_subtitle_text_when_provided(client, test_db):
    video = create_test_video(test_db, title="Any title", uploader_id=8)
    subtitle_text = (
        "This lesson explains rate limiting in API gateways. "
        "Then it compares token bucket and leaky bucket with examples."
    )

    response = client.post(
        "/ai/summarize",
        json={
            "video_id": video.id,
            "subtitle_text": subtitle_text,
            "max_sentences": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["source_kind"] == "subtitle_text"
    assert "rate limiting in API gateways" in data["summary"]


def test_ai_summarize_uses_stored_transcript_when_available(client, test_db):
    video = create_test_video(test_db, title="Cloud databases", uploader_id=9)
    create_test_transcript(
        test_db,
        video_id=video.id,
        transcript_text=(
            "Today we explain replication lag in distributed databases. "
            "Then we compare eventual consistency and strong consistency."
        ),
    )

    response = client.post(
        "/ai/summarize",
        json={
            "video_id": video.id,
            "max_sentences": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source_kind"] == "subtitle_text"
    assert "replication lag in distributed databases" in data["summary"]
