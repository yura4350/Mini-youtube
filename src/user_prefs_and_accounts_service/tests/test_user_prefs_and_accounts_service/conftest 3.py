import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "super-secret-test-key"
os.environ["ALGORITHM"] = "HS256"                  

from src.user_prefs_and_accounts_service.main import Base, User, app, get_db