from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Application
    app_name: str = "OCR Web Service"
    debug: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent
    models_dir: Path = base_dir / "models"
    upload_dir: Path = base_dir / "uploads"
    result_dir: Path = base_dir / "results"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # File limits
    max_file_size: int = 5 * 1024 * 1024  # 5MB (optimized for speed)
    allowed_extensions: set = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}

    # OCR settings
    ocr_language: str = "ru"
    use_gpu: bool = False

    # Cleanup
    file_retention_hours: int = 24

    class Config:
        env_file = ".env"


settings = Settings()

# Create directories if they don't exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.result_dir.mkdir(parents=True, exist_ok=True)
