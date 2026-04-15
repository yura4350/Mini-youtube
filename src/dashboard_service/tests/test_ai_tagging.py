from .conftest import create_test_video, create_test_transcript
from src.video_crud_service.models import TagTaxonomy


def test_ai_tagging_video_not_found(client):
    response = client.post("/ai/tagging", json={"video_id": "missing", "max_tags": 5})
    assert response.status_code == 404
    assert response.json()["detail"] == "Video not found"


def test_ai_tagging_requires_ready_transcript(client, test_db):
    video = create_test_video(test_db, title="Tag target", uploader_id=21)
    create_test_transcript(
        test_db,
        video_id=video.id,
        transcript_text="This transcript is still processing.",
        status="processing",
    )

    response = client.post("/ai/tagging", json={"video_id": video.id, "max_tags": 5})
    assert response.status_code == 409
    assert "Transcript not ready" in response.json()["detail"]


def test_ai_tagging_and_fetch_tags(client, test_db):
    video = create_test_video(test_db, title="Neural search", uploader_id=22)
    create_test_transcript(
        test_db,
        video_id=video.id,
        transcript_text=(
            "We discuss embeddings, vector databases, semantic search and retrieval augmented generation. "
            "Then we compare chunking and reranking tradeoffs."
        ),
        status="ready",
    )

    response = client.post("/ai/tagging", json={"video_id": video.id, "max_tags": 4})
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == video.id
    assert isinstance(data["tags"], list)
    assert len(data["tags"]) <= 4
    assert "primary_category" in data
    assert "confidence_mode" in data
    assert "max_confidence" in data
    if data["confidence_mode"] == "low_confidence_category_only":
        assert data["tags"] == []
        assert data["primary_category"] is not None
    else:
        assert 1 <= len(data["tags"]) <= 4
    active_tags = {
        row.canonical_tag
        for row in test_db.query(TagTaxonomy).filter(TagTaxonomy.active == 1).all()
    }
    assert set(data["tags"]).issubset(active_tags)

    fetch = client.get(f"/ai/tags/{video.id}")
    assert fetch.status_code == 200
    payload = fetch.json()
    assert payload["video_id"] == video.id
    assert payload["tags"] == data["tags"]
    assert payload.get("primary_category") is not None


def test_ai_tag_taxonomy(client):
    response = client.get("/ai/tag-taxonomy")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("tags"), list)
    assert len(data["tags"]) > 0
    first = data["tags"][0]
    assert {"canonical_tag", "display_name", "category"}.issubset(first.keys())
