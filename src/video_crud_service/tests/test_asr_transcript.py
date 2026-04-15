from src.video_crud_service.models import VideoTranscript
from src.video_crud_service.videos import _generate_and_store_transcript_for_video
from sqlalchemy.orm import sessionmaker


def test_generate_and_store_transcript_persists_result(test_db, monkeypatch, tmp_path):
    video_id = "video-asr-1"
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"fake video")

    def fake_transcribe(_path):
        return ("This is generated transcript text.", "en")

    monkeypatch.setattr(
        "src.video_crud_service.videos._transcribe_video_audio_to_text",
        fake_transcribe,
    )
    testing_session_local = sessionmaker(bind=test_db.get_bind(), autocommit=False, autoflush=False)
    monkeypatch.setattr("src.video_crud_service.videos.SessionLocal", testing_session_local)

    _generate_and_store_transcript_for_video(video_id, str(video_path))

    row = test_db.query(VideoTranscript).filter(VideoTranscript.video_id == video_id).first()
    assert row is not None
    assert row.transcript_text == "This is generated transcript text."
    assert row.source == "faster_whisper"
    assert row.status == "ready"
    assert row.error_message is None
    assert row.language == "en"


def test_generate_and_store_transcript_no_result_does_not_write(test_db, monkeypatch, tmp_path):
    video_id = "video-asr-2"
    video_path = tmp_path / "sample2.mp4"
    video_path.write_bytes(b"fake video")

    monkeypatch.setattr(
        "src.video_crud_service.videos._transcribe_video_audio_to_text",
        lambda _path: None,
    )
    testing_session_local = sessionmaker(bind=test_db.get_bind(), autocommit=False, autoflush=False)
    monkeypatch.setattr("src.video_crud_service.videos.SessionLocal", testing_session_local)

    _generate_and_store_transcript_for_video(video_id, str(video_path))

    row = test_db.query(VideoTranscript).filter(VideoTranscript.video_id == video_id).first()
    assert row is not None
    assert row.status == "failed"
    assert "ASR produced no transcript or failed" in (row.error_message or "")
