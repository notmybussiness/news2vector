"""Configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Naver API
    naver_client_id: str = Field(..., validation_alias="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(..., validation_alias="NAVER_CLIENT_SECRET")

    # Gemini API (optional for now)
    gemini_api_key: Optional[str] = Field(
        default=None, validation_alias="GEMINI_API_KEY"
    )

    # Milvus
    milvus_host: str = Field(default="localhost", validation_alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, validation_alias="MILVUS_PORT")

    # Embedding Service
    embedding_service_url: str = Field(
        default="http://localhost:8001", validation_alias="EMBEDDING_SERVICE_URL"
    )

    # Search settings - Hybrid: 경제 키워드 + 대량 수집
    search_keywords_str: str = Field(
        default="경제,증시,주식시장,코스피,코스닥,삼성전자,SK하이닉스,금융,투자,환율,금리",
        validation_alias="SEARCH_KEYWORDS",
    )
    top_k_results: int = Field(default=5, validation_alias="TOP_K_RESULTS")
    news_per_query: int = Field(default=100, validation_alias="NEWS_PER_QUERY")
    # 페이지네이션으로 더 많이 수집 (start=1, 101로 200개씩)
    max_pages_per_keyword: int = Field(
        default=2, validation_alias="MAX_PAGES_PER_KEYWORD"
    )

    # Data retention
    data_retention_days: int = Field(default=30, validation_alias="DATA_RETENTION_DAYS")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    # Collection settings
    collection_name: str = Field(
        default="stock_news_v1", validation_alias="COLLECTION_NAME"
    )
    embedding_dimension: int = Field(
        default=768, validation_alias="EMBEDDING_DIMENSION"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def search_keywords(self) -> List[str]:
        """Parse comma-separated keywords string into list."""
        return [k.strip() for k in self.search_keywords_str.split(",") if k.strip()]

    @property
    def milvus_uri(self) -> str:
        return f"http://{self.milvus_host}:{self.milvus_port}"


# Singleton instance
settings = Settings()
