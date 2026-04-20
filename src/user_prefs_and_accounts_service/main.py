from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, mapped_column

from pydantic import BaseModel, field_validator
from typing import Optional, List, Any, Dict

from passlib.context import CryptContext # Used to help with hashing and password verification
import jwt
from datetime import datetime, timedelta

from fastapi.middleware.cors import CORSMiddleware

import os
import re
from dotenv import load_dotenv

from fastapi import BackgroundTasks
import smtplib
from email.message import EmailMessage

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

load_dotenv() # Load the variables from .env file

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRES = 30
RESET_TOKEN_EXPIRES = 15

# password hashing (bcrypt)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Email setup
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Database Model

# Main User Table
class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, index=True)
    name = Column(String, nullable = False)
    email = Column(String, nullable = False, unique=True)
    role = Column(String, nullable = False)
    bio = Column(String, nullable = True)
    avatar = Column(String, nullable = True)
    hashed_pwd = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")

# User Preferences Table
class UserPreferences(Base):
    """Table to store user preferences"""

    __tablename__ = "user_preferences"

    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    privacy = mapped_column(String, nullable=False, default="public")
    notifications = mapped_column(Boolean, nullable=False, default=True)
    ui_theme = mapped_column(String, nullable=False, default="dark")

    user = relationship("User", back_populates="preferences")

Base.metadata.create_all(engine)


def _ensure_users_schema() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    required_columns = {
        "bio": "VARCHAR",
        "avatar": "VARCHAR",
    }

    statements = []
    for column_name, column_definition in required_columns.items():
        if column_name not in existing_columns:
            statements.append(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}"))

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(statement)


_ensure_users_schema()

# Pydantic Models (Dataclass). Definitions of API Models
PASSWORD_MIN_LENGTH = 8


def validate_password_strength(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters.")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must include at least one letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must include at least one number.")
    return password


class UserCreate(BaseModel):
    name:str
    email:str
    role:str
    password:str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

class UserUpdate(BaseModel):
    name:Optional[str] = None
    bio:Optional[str] = None
    avatar:Optional[str] = None

class UserResponse(BaseModel): # Determines what is given by a model
    id:int
    name:str
    email:str
    role:str
    bio:Optional[str] = None
    avatar:Optional[str] = None
    is_active: bool

    # Return data as objects instead of dictionaries
    class Config:
        from_attributes = True

# New Pydantic Models
class PublicUserResponse(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserPreferencesResponse(BaseModel):
    user_id: int
    privacy: str
    notifications: bool
    ui_theme: str

    class Config:
        from_attributes = True

class UserPreferencesUpdate(BaseModel):
    privacy: Optional[str] = None
    notifications: Optional[bool] = None
    ui_theme: Optional[str] = None

# Pydantic Models for Password Reset
class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

# Function to return user preferences (or create them with default valuesif they don't exist)
def _get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    user_prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()

    # Create new preferences if they don't exist
    if not user_prefs:
        user_prefs = UserPreferences(user_id=user_id)
        db.add(user_prefs)
        db.commit()
        db.refresh(user_prefs)

    return user_prefs

# Security Functions
def verify_pwd(plain_pwd: str, hashed_pwd: str) -> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)

def get_pwd_hash(password:str) -> str:
    return pwd_context.hash(password)

def seed_admin_user() -> None:
    email = (os.getenv("SEED_ADMIN_EMAIL") or "").strip()
    password = (os.getenv("SEED_ADMIN_PASSWORD") or "").strip()
    if not email or not password:
        return

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return
        db.add(
            User(
                name=(os.getenv("SEED_ADMIN_NAME") or "Admin").strip() or "Admin",
                email=email,
                role="admin",
                hashed_pwd=get_pwd_hash(password),
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

# generate dicrionary to hold access token
def create_access_token(data:dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

# create dictionary to hold reset tokens
def create_password_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRES)
    to_encode = {"sub": email, "exp": expire, "type": "reset"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except jwt.PyJWTError:
        return None

# Send the dummy reset email
def send_reset_email(recipient_email: str, token: str):
    # The frontend URL where the user will type their new password
    reset_link = f"http://localhost:5173/sreset-password?token={token}"
    
    # For local testing, just print to the console
    print(f"Dummy email sent to {recipient_email}")
    print(f"Subject: Password Reset Request")
    print(f"Body: Click the link to reset your password: {reset_link}")

def verify_token(token:str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify credentials",
                headers={"WWW-Authenticate":"Bearer"}
            )
        return TokenData(email=email)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify credentials",
            headers={"WWW-Authenticate":"Bearer"}
        )



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Dependencies
def get_current_user(token:str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = verify_token(token)
    user = db.query(User).filter(User.email == token_data.email).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(
            status_code=404,
            detail="Incative User",
        )
    return current_user

app = FastAPI(title="User Accounts Service")

seed_admin_user() # add admin user to the database on startup

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://vcm-52418.vm.duke.edu:5173",
        "http://vcm-52527.vm.duke.edu:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.user_prefs_and_accounts_service.avatars import router as avatars_router

app.include_router(avatars_router)

### USER TABLE RELATED ENDPOINTS ###

# Health Check Endpoint
@app.get("/health")
def health():
    return {"status": "ok", "service": "user-accounts-prefs"}

# Auth Endpoints
@app.post("/auth/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=404,
            detail="User already created!"
        )
    
    hashed_password = get_pwd_hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_pwd=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login/", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session=Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=TOKEN_EXPIRES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type":"bearer"}

# API Endpoints (CRUD Operations)
@app.get("/")
def root():
    return {"message":"Welcome to User Preferences and Accounts Service"}

@app.get("/profile/", response_model=UserResponse) # Get personal profile
def get_profile(current_user:User = Depends(get_current_active_user)):
    return current_user

@app.get("/verify-token/")
def verify_token_endpoint(current_user:User = Depends(get_current_active_user)):
    return {
        "valid" : True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
        }
    }

# Get public user info
@app.get("/user/profile/{user_id}", response_model=UserResponse)
def get_user(user_id:int, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Owner always sees their own profile
    if current_user.id == user_id:
        return user
    
    prefs = (db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first())

    if prefs is not None and prefs.privacy == "private":
        raise HTTPException(status_code=404, detail="User is private")

    return user

# Endpoint to let user update himself
@app.put("/user/profile/edit", response_model=UserResponse)
def update_user(update_user:UserUpdate, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == current_user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")
    
    if update_user.name is not None:
        db_user.name = update_user.name
    if update_user.bio is not None:
        db_user.bio = update_user.bio
    if update_user.avatar is not None:
        db_user.avatar = update_user.avatar


    db.commit()
    db.refresh(db_user)
    return db_user




# Delete user
@app.delete("/users/{user_id}")
def delete(user_id:int, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")
    
    if db_user.id == current_user.id:
        raise HTTPException(status_code=404, detail="You cannot delete yourself!")

    db.delete(db_user)
    db.commit()
    return {"message":"User deleted!"}


# Get all users (authenticated)
@app.get("/users/", response_model=List[UserResponse])
def get_all_users(current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    return db.query(User).all()

# Public endpoints — no auth required, returns only non-sensitive fields
@app.get("/users/public/", response_model=List[PublicUserResponse])
def get_all_public_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_active == True).all()

@app.get("/user/public/{user_id}", response_model=PublicUserResponse)
def get_public_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

### RESET PASSWORD ENDPOINTS ###
@app.post("/auth/forgot-password")
def forgot_password(request: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    # Process if user exists and active. Send the same message regardless of the outcome
    if user and user.is_active:
        token = create_password_reset_token(user.email)
        background_tasks.add_task(send_reset_email, user.email, token)
    
    return {"message": "If that email is in our system, a reset link has been sent."}

@app.post("/auth/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    email = verify_password_reset_token(request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
        
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    # Hash the new password and save it
    user.hashed_pwd = get_pwd_hash(request.new_password)
    db.commit()
    
    return {"message": "Password has been reset successfully"}

### USER PREFERENCES TABLE RELATED ENDPOINTS ###
# Get user's own preferences
@app.get("/user/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    user_prefs = _get_or_create_user_preferences(db, current_user.id)
    return user_prefs

# Update user's own preferences
@app.patch("/user/preferences/update", response_model=UserPreferencesResponse)
def update_user_preferences(update_prefs:UserPreferencesUpdate, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    user_prefs = _get_or_create_user_preferences(db, current_user.id)
    if update_prefs.privacy is not None:
        user_prefs.privacy = update_prefs.privacy
    if update_prefs.notifications is not None:
        user_prefs.notifications = update_prefs.notifications
    if update_prefs.ui_theme is not None:
        user_prefs.ui_theme = update_prefs.ui_theme

    db.commit()
    db.refresh(user_prefs)
    return user_prefs




