from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "example@gmail.com"
    SMTP_PASSWORD: str = "password"
    EMAIL_FROM: str = "example@gmail.com"
    EMAIL_TO_OWNER: str = "admin@gmail.com"
    
    AI_BASE_URL: Optional[str] = None
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "gpt-3.5-turbo"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
settings = Settings()