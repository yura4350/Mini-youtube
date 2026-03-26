from fastapi import FastAPI
from videos import router as videos_router

app = FastAPI()

@app.get("/health")
def read_root():
    return {"Status": "Active"}

app.include_router(videos_router)