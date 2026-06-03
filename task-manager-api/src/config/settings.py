import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key-change-in-prod")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASS = os.environ.get("SMTP_PASS", "")


settings = Settings()
