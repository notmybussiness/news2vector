"""Configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Naver API
    naver_client_id: str = Field(..., env="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(..., env="NAVER_CLIENT_SECRET")

    # Gemini API
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # Milvus
    milvus_host: str = Field(default="localhost", env="MILVUS_HOST")
    milvus_port: int = Field(default=19530, env="MILVUS_PORT")

    # Embedding Service
    embedding_service_url: str = Field(
        default="http://localhost:8001", env="EMBEDDING_SERVICE_URL"
    )

    # Search settings - broad queries for daily stock market news
    search_keywords: List[str] = Field(
        default=["증시", "주식시장", "코스피", "코스닥"],
        env="SEARCH_KEYWORDS",
    )
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    news_per_query: int = Field(default=100, env="NEWS_PER_QUERY")  # Max per query

    # Data retention
    data_retention_days: int = Field(default=30, env="DATA_RETENTION_DAYS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Collection settings
    collection_name: str = Field(default="stock_news_v1", env="COLLECTION_NAME")
    embedding_dimension: int = Field(default=768, env="EMBEDDING_DIMENSION")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def milvus_uri(self) -> str:
        return f"http://{self.milvus_host}:{self.milvus_port}"


# Singleton instance
settings = Settings()
