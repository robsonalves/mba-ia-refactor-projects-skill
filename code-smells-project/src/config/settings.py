import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key-change-in-prod")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    PORT = int(os.environ.get("PORT", 5000))


settings = Settings()
