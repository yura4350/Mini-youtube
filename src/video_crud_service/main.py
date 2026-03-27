from fastapi import FastAPI
from .videos import router as videos_router
from .database import init_db

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Retry DB init to handle startup timing and DNS delays in containers.
    init_db()

@app.get("/health")
def read_root():
    return {"Status": "Active"}

app.include_router(videos_router)