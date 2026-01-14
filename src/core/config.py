"""
Configuration management for the Content Crew system.

Loads settings from YAML files and environment variables.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    """LLM provider settings."""

    default_provider: str = "anthropic"
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7


class RAGSettings(BaseModel):
    """RAG system settings."""

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    vector_store_path: str = "data/vector_store"
    chunk_size: int = 500
    chunk_overlap: int = 50
    default_n_results: int = 5


class ContentSettings(BaseModel):
    """Content creation settings."""

    default_target_length: int = 1500
    min_quality_score: int = 75
    max_revision_cycles: int = 3
    output_directory: str = "output/articles"
    output_format: str = "markdown"


class PipelineSettings(BaseModel):
    """Pipeline execution settings."""

    max_concurrent_tasks: int = 5
    task_timeout: int = 600
    retry_attempts: int = 2


class NotionSettings(BaseModel):
    """Notion integration settings."""

    enabled: bool = False
    database_id: str = ""
    default_status: str = "Rascunho"


class Settings(BaseModel):
    """Main application settings."""

    debug: bool = False
    log_level: str = "INFO"
    llm: LLMSettings = Field(default_factory=LLMSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    content: ContentSettings = Field(default_factory=ContentSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    notion: NotionSettings = Field(default_factory=NotionSettings)

    # API keys from environment
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    notion_token: str | None = None

    @classmethod
    def load_from_yaml(cls, config_dir: str | Path = "config") -> "Settings":
        """Load settings from YAML files."""
        config_dir = Path(config_dir)
        data: dict[str, Any] = {}

        # Load main settings
        settings_file = config_dir / "settings.yaml"
        if settings_file.exists():
            with open(settings_file) as f:
                data = yaml.safe_load(f) or {}

        # Load RAG config
        rag_file = config_dir / "rag_config.yaml"
        if rag_file.exists():
            with open(rag_file) as f:
                rag_data = yaml.safe_load(f) or {}
                if "rag" in rag_data:
                    data["rag"] = rag_data["rag"]

        # Override with environment variables
        data["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
        data["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        data["notion_token"] = os.getenv("NOTION_TOKEN")

        # Notion settings from env
        if os.getenv("NOTION_DATABASE_ID"):
            if "notion" not in data:
                data["notion"] = {}
            data["notion"]["database_id"] = os.getenv("NOTION_DATABASE_ID")
            data["notion"]["enabled"] = True

        if os.getenv("DEBUG"):
            data["debug"] = os.getenv("DEBUG", "").lower() == "true"

        if os.getenv("LOG_LEVEL"):
            data["log_level"] = os.getenv("LOG_LEVEL", "INFO")

        return cls(**data)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.load_from_yaml()
