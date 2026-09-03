from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "mysql+aiomysql://chatbot:changeme@localhost:3306/chatbot"

    # JWT
    secret_key: str = "change-me-in-production-at-least-32-chars"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # LLM
    default_llm_provider: str = "xingchen"
    xingchen_api_key: str = ""
    xingchen_base_url: str = ""
    xingchen_model: str = "xingchen-pro"
    xingchen_embed_model: str = "xingchen-embedding"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"

    # Rate Limiting
    rate_limit_general: str = "60/minute"
    rate_limit_llm: str = "20/minute"

    # File Upload
    max_file_size: int = 10485760
    sync_process_threshold: int = 5242880

    # RAG
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50


settings = Settings()
