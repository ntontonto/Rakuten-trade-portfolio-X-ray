"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql://portfolio_user:portfolio_pass@localhost:5432/portfolio_db"

    # API Keys
    GEMINI_API_KEY: Optional[str] = None

    # ML Models
    ML_MODELS_PATH: str = "/app/ml_models"

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Portfolio X-Ray"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".csv"}

    # Name Mappings for CSV parsing (from original JavaScript)
    NAME_MAPPINGS: dict = {
        "eMAXIS Slim 全世界株式(オール・カントリー)": "eMAXIS Slim 全世界株式(オール・カントリー)(オルカン)",
        "eMAXIS Slim 先進国リートインデックス": "eMAXIS Slim 先進国リートインデックス(除く日本)"
    }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
