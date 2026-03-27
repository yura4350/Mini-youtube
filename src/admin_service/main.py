import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Admin Service")


@app.get("/health")
def health():
    """Admin service liveness check."""
    logger.info("Health check requested")
    return {"status": "ok", "service": "admin"}


@app.get("/admin/health")
def get_system_health():
    """Return admin service health status for the admin dashboard."""
    logger.info("System health check requested")
    return {"status": "ok", "service": "admin"}
