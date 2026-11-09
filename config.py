import os
from datetime import timedelta

from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=10)
    MAX_CONTENT_LENGTH = 512 * 1024
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    TIMEZONE = "America/Sao_Paulo"
    JSON_AS_ASCII = False


class DevelopmentConfig(Config):
    DEBUG = False


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    PROPAGATE_EXCEPTIONS = False
    SECRET_KEY = "chave-de-teste-apenas-para-pytest"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = True
    LOG_LEVEL = "ERROR"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
