import re
import os
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Intelligence Service")
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip()
OPENAI_SUMMARY_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
OPENAI_SUMMARY_MAX_OUTPUT_TOKENS = int(os.getenv("OPENAI_SUMMARY_MAX_OUTPUT_TOKENS", "220"))
OPENAI_SUMMARY_ENABLED = os.getenv("OPENAI_SUMMARY_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}

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


def _openai_summarize(source_text: str, max_sentences: int, source_kind: str) -> str | None:
    if not OPENAI_SUMMARY_ENABLED or not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI  # type: ignore
    except Exception as exc:
        logger.warning("OpenAI SDK unavailable, using rules fallback: %s", exc)
        return None

    source_note = (
        "Source is transcript text with spoken content."
        if source_kind == "subtitle_text"
        else "Source is metadata only (title/description/tags). Be conservative and avoid overclaiming specifics."
    )
    system_prompt = (
        "You summarize one video for end users.\n"
        "Rules:\n"
        "1) Be faithful to source; do not invent details.\n"
        "2) Plain English only, no markdown, no bullet points.\n"
        f"3) Output at most {max_sentences} sentence(s), under 500 characters.\n"
        "4) Keep the most informative points first.\n"
        "5) If source is weak, state uncertainty briefly instead of hallucinating."
    )
    user_prompt = f"Source kind: {source_kind}\n{source_note}\n\nSource text:\n{source_text}"

    try:
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL or None)
        response = client.responses.create(
            model=OPENAI_SUMMARY_MODEL,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            max_output_tokens=OPENAI_SUMMARY_MAX_OUTPUT_TOKENS,
        )
        output_text = getattr(response, "output_text", None)
        if not output_text or not str(output_text).strip():
            return None
        return _clip_text(str(output_text), 500)
    except Exception:
        logger.exception("OpenAI summarize request failed, using rules fallback")
        return None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "intelligence"}


@app.get("/ai/health")
def ai_health() -> dict:
    provider = "openai" if OPENAI_SUMMARY_ENABLED and OPENAI_API_KEY else "rules-based-mvp"
    return {
        "status": "ok",
        "service": "ai-intelligence",
        "provider": provider,
        "model": OPENAI_SUMMARY_MODEL if provider == "openai" else None,
        "base_url": OPENAI_BASE_URL if provider == "openai" else None,
        "openai_configured": provider == "openai",
    }


@app.post("/ai/summarize")
def ai_summarize(payload: SummarizeRequest) -> dict:
    summary = _openai_summarize(payload.source_text, payload.max_sentences, payload.source_kind)
    provider = "openai" if summary else "rules-based-mvp"
    if not summary:
        summary = _summarize_mvp(payload.source_text, payload.max_sentences)

    return {
        "video_id": payload.video_id,
        "summary": summary,
        "source_kind": payload.source_kind,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": OPENAI_SUMMARY_MODEL if provider == "openai" else None,
    }
