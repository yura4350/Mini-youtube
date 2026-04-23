from fastapi import APIRouter

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "user-accounts-prefs"}


@router.get("/")
def root() -> dict:
    return {"message": "Welcome to User Preferences and Accounts Service"}