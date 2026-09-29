from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    openweather_city: str = os.getenv("OPENWEATHER_CITY", "Colombo")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    disease_agent_timeout_seconds: float = float(os.getenv("DISEASE_AGENT_TIMEOUT_SECONDS", "2.0"))
    weather_agent_timeout_seconds: float = float(os.getenv("WEATHER_AGENT_TIMEOUT_SECONDS", "1.5"))
    rag_agent_timeout_seconds: float = float(os.getenv("RAG_AGENT_TIMEOUT_SECONDS", "1.0"))
    crop_agent_timeout_seconds: float = float(os.getenv("CROP_AGENT_TIMEOUT_SECONDS", "2.0"))

    def require_api_key(self) -> None:
        missing = []
        if not self.openweather_api_key:
            missing.append("OPENWEATHER_API_KEY")
        if self.llm_provider == "openai" and not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        elif self.llm_provider == "groq" and not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()