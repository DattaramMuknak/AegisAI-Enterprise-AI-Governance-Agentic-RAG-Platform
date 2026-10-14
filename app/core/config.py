"""
Centralized application configuration.
Reads from environment variables / .env file via pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AegisAI"
    ENV: str = "development"
    SECRET_KEY: str = "dev-secret"
    LOG_LEVEL: str = "INFO"

    # MySQL
    DATABASE_URL: str = "mysql+pymysql://aegis:aegis_password@localhost:3306/aegis_governance"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "aegis-governance-rag"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "aegis-governance"

    # Governance thresholds
    RISK_BLOCK_THRESHOLD: int = 75
    GROUNDING_MIN_SCORE: float = 0.55
    TOXICITY_BLOCK_THRESHOLD: float = 0.7

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
