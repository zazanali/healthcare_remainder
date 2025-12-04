from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Security
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALG: str = "HS256"
    WEBHOOK_SECRET: str = "dev-webhook-secret-change-in-production"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""

    # Twilio Settings
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///reminders.db"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
