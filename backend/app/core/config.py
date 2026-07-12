import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/epc")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    neo4j_uri: str = os.getenv("NEO4J_URI", "")
    neo4j_user: str = os.getenv("NEO4J_USER", "")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
