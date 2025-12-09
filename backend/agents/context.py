"""Configuration context for the agents system."""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(kw_only=True)
class AgentContext:
    """Configuration context for the AI agents system."""

    # Database
    db_session: Optional[Any] = field(default=None)
    """Database session for queries."""

    # LLM Configuration
    chat_model: str = field(
        default="gpt-4o-mini",
        metadata={"description": "Chat model for AI responses"}
    )

    embedding_model: str = field(
        default="text-embedding-3-small",
        metadata={"description": "Embedding model for semantic search"}
    )

    temperature: float = field(
        default=0.3,
        metadata={"description": "Temperature for LLM generation"}
    )

    # Search Configuration
    default_k: int = field(
        default=5,
        metadata={"description": "Default number of results to return"}
    )

    similarity_threshold: float = field(
        default=0.20,  # Lowered further for hybrid scoring with short brand queries
        metadata={"description": "Minimum similarity score for results (0.0-1.0)"}
    )

    enable_reranking: bool = field(
        default=False,
        metadata={"description": "Enable Cohere reranking for search results"}
    )

    # Intent Detection
    intent_confidence_threshold: float = field(
        default=0.6,
        metadata={"description": "Minimum confidence for intent detection"}
    )

    def __post_init__(self):
        """Initialize from environment variables if not provided."""
        # You can add environment variable loading here if needed
        pass
