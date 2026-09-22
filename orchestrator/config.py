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

    def require_api_key(self) -> None:
        missing = []
        if not self.openweather_api_key:
        if not self.groq_api_key:
            missing.append("GROQ_API_KEY")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

settings = Settings()