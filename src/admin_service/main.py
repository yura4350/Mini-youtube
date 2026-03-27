import logging
from datetime import datetime, timezone

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Admin Service")

_logs: list[dict] = []


def _log(level: str, message: str) -> None:
    _logs.append(
        {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
    )


@app.get("/health")
def health():
    """Admin service liveness check."""
    _log("INFO", "Health check requested")
    return {"status": "ok", "service": "admin"}


@app.get("/admin/health")
def get_system_health():
    """Return admin service health status for the admin dashboard."""
    _log("INFO", "System health check requested")
    return {"status": "ok", "service": "admin"}


@app.get("/admin/logs")
def get_logs():
    """Return recent system logs."""
    _log("INFO", "Logs requested")
    return {"logs": _logs[-200:]}
