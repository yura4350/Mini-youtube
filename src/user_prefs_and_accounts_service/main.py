from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "fc42e6a3e2c0cd478aaea480e41fdcc1d4bb802c7d41fccbff59465f6945f190"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="User Accounts Service")

# In-memory demo DB (replace with real DB later)
db = {
    "iurii": {
        "username": "iurii",
        "email": "iurii@gmail.com",
        # password for this hash should match what you generated
        "hashed_password": "$2b$12$IXmKdX2J.7Slc0w6zm5OZu3Yqhd0Ef5rlRnyN0b9zmenRQQPtNXqu",
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(users_db: dict, username: str) -> Optional[UserInDB]:
    user_data = users_db.get(username)
    if not user_data:
        return None
    return UserInDB(**user_data)


def authenticate_user(users_db: dict, username: str, password: str) -> Optional[UserInDB]:
    user = get_user(users_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(db, token_data.username or "")
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserInDB:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=User)
async def read_users_me(
    current_user: Annotated[UserInDB, Depends(get_current_active_user)],
):
    return current_user


@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/auth/register")
def register():
    return {"message": "TODO: /auth/register not implemented yet"}

@app.post("/auth/login")
def login():
    return {"message": "TODO: /auth/login not implemented yet"}

@app.post("/auth/logout")
def logout():
    return {"message": "TODO: /auth/logout not implemented yet"}

@app.post("/auth/reset-password")
def reset_password():
    return {"message": "TODO: /auth/reset-password not implemented yet"}

@app.get("/user/profile/{id}")
def get_profile(id: str):
    return {"message": "TODO: /user/profile/{id} not implemented yet", "id": id}

@app.patch("/user/profile/edit")
def edit_profile():
    return {"message": "TODO: /user/profile/edit not implemented yet"}

@app.patch("/user/settings/privacy")
def update_privacy_settings():
    return {"message": "TODO: /user/settings/privacy not implemented yet"}

@app.patch("/user/settings/notifications")
def update_notification_settings():
    return {"message": "TODO: /user/settings/notifications not implemented yet"}

@app.patch("/user/settings/ui")
def update_ui_settings():
    return {"message": "TODO: /user/settings/ui not implemented yet"}




