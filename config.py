import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Never let a hosted deployment silently use an empty, instance-local SQLite
    # database. That makes health checks pass while all application tables vanish.
    _database_url = (os.environ.get("DATABASE_URL") or "").strip()
    _is_render = os.environ.get("RENDER", "").lower() == "true"

    if _is_render and not _database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Configure the Supabase PostgreSQL URL in Render."
        )

    if not _database_url:
        # SQLite remains available for local development only.
        SQLALCHEMY_DATABASE_URI = "sqlite:///car_marketplace.db"
    elif _database_url.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = _database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif _database_url.startswith("postgresql://"):
        SQLALCHEMY_DATABASE_URI = _database_url.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
    elif _database_url.startswith("postgresql+psycopg://"):
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        raise RuntimeError(
            "DATABASE_URL must be a PostgreSQL connection URL in hosted deployments."
        )

    _uses_postgres = SQLALCHEMY_DATABASE_URI.startswith("postgresql+psycopg://")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        **(
            {"connect_args": {"options": "-csearch_path=cars"}}
            if _uses_postgres
            else {}
        ),
    }

    MAX_CONTENT_LENGTH = 40 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    WTF_CSRF_TIME_LIMIT = 3600
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
