"""
LLM Client implementation for Agri-Advisor (Subtask T-18.1).
Supports Groq (default) and OpenAI GPT-3.5-turbo (alternative provider)
with consistent error handling, timeouts, and configurable generation parameters.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Literal, Optional
import requests

from orchestrator.config import settings
from orchestrator.resilience import request_with_retry

logger = logging.getLogger("agri_advisor.llm_client")


class LLMClientError(RuntimeError):
    """Raised when the LLM provider fails to return a valid completion."""


class LLMClient:
    """
    Unified LLM Client supporting Groq and OpenAI providers.
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        provider: Optional[Literal["groq", "openai"]] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.provider = provider or getattr(settings, "llm_provider", "groq")
        self.timeout_seconds = timeout_seconds

        if self.provider == "openai":
            configured_key = getattr(settings, "openai_api_key", "") or os.getenv("OPENAI_API_KEY", "")
            self.api_key = api_key if api_key is not None else configured_key
            self.model = model or getattr(settings, "openai_model", "gpt-3.5-turbo") or "gpt-3.5-turbo"
        else:
            self.provider = "groq"
            configured_key = getattr(settings, "groq_api_key", "") or os.getenv("GROQ_API_KEY", "")
            self.api_key = api_key if api_key is not None else configured_key
            self.model = model or getattr(settings, "groq_model", "llama-3.1-8b-instant") or "llama-3.1-8b-instant"

        self._groq_sdk_client = None
        if self.provider == "groq" and self.api_key:
            try:
                from groq import Groq
                self._groq_sdk_client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.debug(f"Groq SDK initialization note: {e}. REST endpoint will be used.")

    def is_available(self) -> bool:
        """Check if the client has an active API key configured."""
        return bool(self.api_key and self.api_key.strip())

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> str:
        """
        Generate completion from LLM provider.
        Raises LLMClientError on missing credentials, network failure, or API error.
        """
        if not self.is_available():
            raise LLMClientError(f"No API key configured for LLM provider '{self.provider}'")

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        if self.provider == "groq":
            return self._call_groq(messages, max_tokens=max_tokens, temperature=temperature)
        elif self.provider == "openai":
            return self._call_openai(messages, max_tokens=max_tokens, temperature=temperature)
        else:
            raise LLMClientError(f"Unsupported LLM provider: '{self.provider}'")

    def _call_groq(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> str:
        """Execute chat completion call to Groq API."""
        # Try SDK first if initialized
        if self._groq_sdk_client is not None:
            try:
                response = self._groq_sdk_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout_seconds,
                )
                if response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content or ""
            except Exception as exc:
                logger.warning(f"Groq SDK call failed ({exc}), falling back to REST request.")

        # Fallback to direct HTTP REST request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = request_with_retry(
                lambda: requests.post(
                    self.GROQ_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                ),
                service="groq_llm",
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            raise LLMClientError(f"Groq API completion failed: {exc}") from exc

    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> str:
        """Execute chat completion call to OpenAI API (e.g. gpt-3.5-turbo)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            resp = request_with_retry(
                lambda: requests.post(
                    self.OPENAI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                ),
                service="openai_llm",
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            raise LLMClientError(f"OpenAI API completion failed: {exc}") from exc


# Global singleton client instance
llm_client = LLMClient()
