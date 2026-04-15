import re
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Intelligence Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SummarizeRequest(BaseModel):
    video_id: str = Field(..., min_length=1)
    source_text: str = Field(..., min_length=1, max_length=20000)
    source_kind: str = Field(default="video_metadata", min_length=1, max_length=64)
    max_sentences: int = Field(default=3, ge=1, le=5)


def _clip_text(value: str, max_length: int) -> str:
    compact = " ".join(value.strip().split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."


def _summarize_mvp(source_text: str, max_sentences: int) -> str:
    normalized = " ".join(source_text.split())
    sentence_candidates = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized) if s.strip()]
    chosen = sentence_candidates[:max_sentences]
    if not chosen:
        chosen = [_clip_text(normalized, 220)]
    return _clip_text(" ".join(chosen), 500)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "intelligence"}


@app.get("/ai/health")
def ai_health() -> dict:
    return {
        "status": "ok",
        "service": "ai-intelligence",
        "provider": "rules-based-mvp",
    }


@app.post("/ai/summarize")
def ai_summarize(payload: SummarizeRequest) -> dict:
    summary = _summarize_mvp(payload.source_text, payload.max_sentences)
    return {
        "video_id": payload.video_id,
        "summary": summary,
        "source_kind": payload.source_kind,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "intelligence_service",
    }
