from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.user_prefs_and_accounts_service.avatars import router as avatars_router
from src.user_prefs_and_accounts_service.config import CORS_ALLOW_ORIGINS
from src.user_prefs_and_accounts_service.database import Base, get_db, engine, SessionLocal
from src.user_prefs_and_accounts_service.models import User, UserPreferences
from src.user_prefs_and_accounts_service.schemas import UserResponse
from src.user_prefs_and_accounts_service.dependencies import get_current_active_user, get_current_user
from src.user_prefs_and_accounts_service.services.seed import seed_admin_user


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
    if db.query(User).filter(User.name == user.name).first():
        raise HTTPException(
            status_code=400,
            detail="That username is already taken."
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
async def forgot_password(request: PasswordResetRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
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




