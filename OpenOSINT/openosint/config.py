"""Shared configuration helpers."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env() -> bool:
    """Load the project-root .env file regardless of the caller's cwd."""
    return load_dotenv(dotenv_path=ENV_FILE)
