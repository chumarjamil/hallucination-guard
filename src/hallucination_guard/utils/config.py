"""Centralised configuration — reads from environment variables with sensible defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Application-wide settings.

    Override via ``HALLUCINATION_GUARD_*`` environment variables.
    """

    # NLP / Models
    spacy_model: str = field(
        default_factory=lambda: os.getenv("HALLUCINATION_GUARD_SPACY_MODEL", "en_core_web_sm")
    )
    transformer_model: str = field(
        default_factory=lambda: os.getenv("HALLUCINATION_GUARD_TRANSFORMER_MODEL", "all-MiniLM-L6-v2")
    )

    # Wikipedia
    wiki_language: str = field(
        default_factory=lambda: os.getenv("HALLUCINATION_GUARD_WIKI_LANG", "en")
    )

    # Verification
    support_threshold: float = field(
        default_factory=lambda: float(os.getenv("HALLUCINATION_GUARD_SUPPORT_THRESHOLD", "0.45"))
    )

    # Server
    host: str = field(
        default_factory=lambda: os.getenv("HALLUCINATION_GUARD_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("HALLUCINATION_GUARD_PORT", "8000"))
    )

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("HALLUCINATION_GUARD_LOG_LEVEL", "INFO")
    )


def get_settings() -> Settings:
    """Return a fresh Settings instance (reads env vars each call)."""
    return Settings()
