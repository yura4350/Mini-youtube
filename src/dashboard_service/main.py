import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Dashboard Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "dashboard"}
