"""Configuration settings for Outbreak Sentinel Agent."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load root .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class SentinelSettings:
    """Sentinel agent environment settings and thresholds."""

    def __init__(self) -> None:
        self.app_env: str = os.getenv("APP_ENV", "development").lower()
        self.db_path: str = os.getenv("SENTINEL_DATABASE_PATH", str(ROOT_DIR / "data" / "sentinel.sqlite3"))
        
        # Microservice URLs (default pointing to local Orchestrator Hub)
        self.weather_agent_url: str = os.getenv("WEATHER_AGENT_URL", "http://127.0.0.1:8000/api/weather/advice")
        self.rag_agent_url: str = os.getenv("RAG_AGENT_URL", "http://127.0.0.1:8000/api/rag/retrieve")
        self.disease_agent_url: str = os.getenv("DISEASE_AGENT_URL", "http://127.0.0.1:8000/api/disease/diagnose")
        
        # LLM Configurations
        self.llm_provider: str = os.getenv("LLM_PROVIDER", "groq").lower()
        self.groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Statistical & Operational Thresholds
        self.min_cases: int = int(os.getenv("SENTINEL_MIN_CASES", "5"))
        self.confidence_threshold: float = float(os.getenv("SENTINEL_CONFIDENCE_THRESHOLD", "0.7"))
        self.cooldown_hours: int = int(os.getenv("SENTINEL_COOLDOWN_HOURS", "24"))
        self.scan_interval_hours: int = int(os.getenv("SENTINEL_SCAN_INTERVAL_HOURS", "3"))
        self.eval_interval_hours: int = int(os.getenv("SENTINEL_EVAL_INTERVAL_HOURS", "24"))
        
        # Notification Settings
        self.sms_enabled: bool = os.getenv("SENTINEL_ENABLE_SMS", "false").lower() in ("1", "true", "yes")
        self.twilio_account_sid: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_from_number: Optional[str] = os.getenv("TWILIO_FROM_NUMBER")


settings = SentinelSettings()
