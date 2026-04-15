from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

from pydantic import BaseModel
from typing import Optional, List, Any, Dict

from passlib.context import CryptContext # Used to help with hashing and password verification
import jwt
from datetime import datetime, timedelta

from fastapi.middleware.cors import CORSMiddleware

import os
from dotenv import load_dotenv

load_dotenv() # Load the variables from .env file

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRES = 30

# password hashing (bcrypt)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

    preferences = relationship("UserPreferences", back_populates="user")

# User Preferences Table
class UserPreferences(Base):
    """Table to store user preferences"""

    __tablename__ = "user_preferences"

    user_id = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)
    privacy = mapped_column(String, nullable=False, default="public")
    notifications = mapped_column(Boolean, nullable=False, default=True)
    ui_theme = mapped_column(String, nullable=False, default="system")

    user = relationship("User", back_populates="preferences")

Base.metadata.create_all(engine)

# Pydantic Models (Dataclass). Definitions of API Models
class UserCreate(BaseModel):
    name:str
    email:str
    role:str
    password:str

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

    class Config:
        from_attributes = True

# New Pydantic Models
class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.user_prefs_and_accounts_service.avatars import router as avatars_router

app.include_router(avatars_router)


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

    return user

# Update any user (should be removed in the future)
@app.put("/user/{user_id}", response_model=UserResponse)
def update_user(user_id:int, update_user:UserCreate, current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User does not exist")
    
    db_user.name = update_user.name
    db_user.email = update_user.email
    db_user.role = update_user.role


    db.commit()
    db.refresh(db_user)
    return db_user

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


# Get all users
@app.get("/users/", response_model=List[UserResponse])
def get_all_users(current_user:User = Depends(get_current_active_user), db:Session = Depends(get_db)):
    return db.query(User).all()





