from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .videos import router as videos_router
from .database import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Retry DB init to handle startup timing and DNS delays in containers.
    init_db()

@app.get("/health")
def read_root():
    return {"Status": "Active"}

app.include_router(videos_router)