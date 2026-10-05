"""Verify imports, local model loading, and configured external API access."""

import argparse
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

IMPORTS = {
    "streamlit": "streamlit",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "chromadb": "chromadb",
    "sentence-transformers": "sentence_transformers",
    "spacy": "spacy",
    "transformers": "transformers",
    "groq": "groq",
    "requests": "requests",
    "python-jose": "jose",
    "pytest": "pytest",
}

def verify_imports() -> None:
    failures = []
    for package, module in IMPORTS.items():
        try:
            importlib.import_module(module)
        except Exception as error:
            failures.append(f"{package}: {error}")
    if failures:
        raise RuntimeError(f"Failed to import {', '.join(failures)}")
    print(f"Successfully imported {', '.join(IMPORTS)}")

def verify_models() -> None:
    import spacy
    from sentence_transformers import SentenceTransformer

    nlp = spacy.load("en_core_web_sm")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    if not nlp("health crop").text or embedding_model.encode("healthy crop").size == 0:
        raise RuntimeError("A local model returned no output")
    print("OK: loaded spaCy en_core_web_sm")
    print("OK: loaded Sentence-Transformers all-MiniLM-L6-v2")

def verify_apis() -> None:
    import requests
    from groq import Groq

    from orchestrator.config import settings

    settings.require_api_key()
    weather_response = requests.get("https://api.openweathermap.org/data/2.5/weather",
                                    params={"q": settings.openweather_city,
                                            "appid": settings.openweather_api_key,
                                            "units": "metric",
                                            },
                                    timeout=15
                                    )
    weather_response.raise_for_status()
    weather = weather_response.json()
    if not weather.get("main") or not weather.get("weather"):
        raise RuntimeError("A local model returned no output")
    print(f"OK: OpenWeather returned data for {weather.get('name', settings.openweather_city)}")

    completion = Groq(api_key=settings.groq_api_key).chat.completions.create(
        model = settings.groq_model,
        messages=[{"role": "user", "content": "Reply with the word OK."}],
        max_tokens = 5,
    )
    if not completion.choices[0].message.content:
        raise RuntimeError("Groq returned an empty completion")
    print("OK: Groq completion succeeded")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-apis", action="store_true")
    args = parser.parse_args()
    try:
        verify_imports()
        if not args.skip_models:
            verify_models()
        if not args.skip_apis:
            verify_apis()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Environment verification complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())