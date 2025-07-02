import os
from dotenv import load_dotenv
load_dotenv()

CORS_HEADERS = "Content-Type"

class Config:
    # Flask + DB
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql://root:password@localhost/nexpertia")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret")
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_NAME = "refresh_token"
    JWT_ACCESS_TOKEN_EXPIRES = 900             # 15 min
    JWT_REFRESH_TOKEN_EXPIRES = 7 * 24 * 3600  # 7 dage
    JWT_COOKIE_SECURE = False                  # True i production m. HTTPS
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_COOKIE_HTTPONLY = True
