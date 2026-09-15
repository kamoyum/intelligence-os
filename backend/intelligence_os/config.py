from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv("INTELLIGENCE_DATA_DIR", BASE / "data"))
    db_path: Path = Path(os.getenv("INTELLIGENCE_DB", BASE / "data" / "intelligence.db"))
    token_path: Path = Path(os.getenv("INTELLIGENCE_TOKEN_PATH", BASE / "data" / "local_api_token.txt"))
    model: str = os.getenv("INTELLIGENCE_MODEL", "")
    eval_model: str = os.getenv("INTELLIGENCE_EVAL_MODEL", "")
    verify_model: str = os.getenv("INTELLIGENCE_VERIFY_MODEL", "")
    research_model: str = os.getenv("INTELLIGENCE_RESEARCH_MODEL", "")
    embedding_model: str = os.getenv("INTELLIGENCE_EMBEDDING_MODEL", "")
    external_llm_mode: str = os.getenv("INTELLIGENCE_EXTERNAL_LLM_MODE", "opt_in").strip().lower()
    embedding_daily_inputs: int = int(os.getenv("INTELLIGENCE_EMBEDDING_DAILY_INPUTS", "100"))
    web_search_daily_queries: int = int(os.getenv("INTELLIGENCE_WEB_SEARCH_DAILY_QUERIES", "10"))
    research_max_sources: int = int(os.getenv("INTELLIGENCE_RESEARCH_MAX_SOURCES", "6"))
    research_timeout_seconds: float = float(os.getenv("INTELLIGENCE_RESEARCH_TIMEOUT_SECONDS", "20"))
    research_max_bytes: int = int(os.getenv("INTELLIGENCE_RESEARCH_MAX_BYTES", str(2_500_000)))
    research_mode: str = os.getenv("INTELLIGENCE_RESEARCH_MODE", "auto_public").strip().lower()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    google_client_secret_file: Path = Path(os.getenv("GOOGLE_CLIENT_SECRET_FILE", BASE / "google_client_secret.json"))
    google_token_file: Path = Path(os.getenv("GOOGLE_TOKEN_FILE", BASE / "data" / "google_token.json"))
    google_mode: str = os.getenv("INTELLIGENCE_GOOGLE_MODE", "off").strip().lower()
    core_origin: str = os.getenv("INTELLIGENCE_CORE_ORIGIN", "http://127.0.0.1:8765")

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.google_token_file.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
