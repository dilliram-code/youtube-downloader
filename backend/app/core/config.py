from pathlib import Path
from typing import List
import shutil
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

class Settings(BaseSettings):
    APP_NAME: str = "Vidora"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    # Security & CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
    SECRET_KEY: str = "vidora-secret-key-development-mode-only"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./vidora.db"

    # Media Paths
    FFMPEG_PATH: str = Field(default_factory=lambda: shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg")
    FFPROBE_PATH: str = Field(default_factory=lambda: shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe")
    DOWNLOADS_DIR: str = "./storage/downloads"
    TEMP_DIR: str = "./storage/temp"

    # Limits & Concurrency
    MAX_DOWNLOAD_SIZE_MB: int = 2048
    MAX_CONCURRENT_JOBS: int = 3
    JOB_RETENTION_HOURS: int = 6
    JOB_TIMEOUT_SECONDS: int = 600

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Provider Credentials
    YOUTUBE_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def parsed_allowed_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    def setup_directories(self) -> None:
        Path(self.DOWNLOADS_DIR).resolve().mkdir(parents=True, exist_ok=True)
        Path(self.TEMP_DIR).resolve().mkdir(parents=True, exist_ok=True)

settings = Settings()
