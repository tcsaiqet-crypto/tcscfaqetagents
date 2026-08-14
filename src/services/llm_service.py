"""Lightweight LLM service wrapper for Gemini and GPT text generation with safe fallbacks."""

import json
import os
from typing import Optional

import requests

from src.config import config
from src.utils.logger import logger


class LLMService:
    """Provider wrapper that keeps failures non-fatal for pipeline stability."""

    def __init__(self) -> None:
        self.gemini_model = "gemini-1.5-flash"
        self.gpt_model = "gpt-4o-mini"
        self.timeout_seconds = 20
        self.last_error: Optional[dict] = None

    @staticmethod
    def _active_provider() -> str:
        provider_getter = getattr(config, "get_active_provider", None)
        if callable(provider_getter):
            try:
                provider = str(provider_getter()).strip().lower()
                return "gpt" if provider == "gpt" else "gemini"
            except Exception:
                pass
        provider = os.getenv("QET_AI_PROVIDER", "gemini").strip().lower()
        return "gpt" if provider == "gpt" else "gemini"

    @staticmethod
    def _provider_key(provider: str) -> str:
        provider_key_getter = getattr(config, "get_provider_api_key", None)
        if callable(provider_key_getter):
            try:
                return str(provider_key_getter("gpt" if provider == "gpt" else "gemini"))
            except Exception:
                pass
        generic_key_getter = getattr(config, "get_api_key", None)
        if callable(generic_key_getter):
            try:
                return str(generic_key_getter())
            except Exception:
                return ""
        return ""

    def is_enabled(self) -> bool:
        provider = self._active_provider()
        llm_enabled = True
        llm_enabled_getter = getattr(config, "is_llm_enabled", None)
        if callable(llm_enabled_getter):
            try:
                llm_enabled = bool(llm_enabled_getter())
            except Exception:
                llm_enabled = True
        return llm_enabled and bool(self._provider_key(provider))

    def get_runtime_status(self) -> dict:
        try:
            provider = self._active_provider()
        except Exception:
            provider = os.getenv("QET_AI_PROVIDER", "gemini").strip().lower()
            provider = "gpt" if provider == "gpt" else "gemini"
        enabled = True
        llm_enabled_getter = getattr(config, "is_llm_enabled", None)
        if callable(llm_enabled_getter):
            try:
                enabled = bool(llm_enabled_getter())
            except Exception:
                enabled = True
        has_key = bool(self._provider_key(provider))
        if not enabled:
            state = "Disabled"
        elif has_key:
            state = "Ready"
        else:
            state = "Misconfigured"
        return {"provider": provider, "enabled": enabled, "has_key": has_key, "state": state}

    def generate_text(self, prompt: str) -> Optional[str]:
        """Return model text when available; otherwise return None."""
        self.last_error = None
        if not self.is_enabled():
            self.last_error = {"reason": "disabled_or_missing_key"}
            return None

        provider = self._active_provider()
        return self._generate_with_gpt(prompt) if provider == "gpt" else self._generate_with_gemini(prompt)

    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        api_key = self._provider_key("gemini")
        if not api_key:
            self.last_error = {"reason": "missing_gemini_api_key"}
            return None

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={api_key}"
        )
        payload = {
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 900,
            },
            "contents": [{"parts": [{"text": prompt}]}],
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                logger.warning(
                    "Gemini call failed with status %s. Falling back to deterministic output.",
                    response.status_code,
                )
                self.last_error = {"status_code": response.status_code, "response": response.text}
                return None

            body = response.json()
            candidates = body.get("candidates") or []
            if not candidates:
                self.last_error = {"reason": "empty_candidates", "response": body}
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                self.last_error = {"reason": "empty_parts", "response": body}
                return None

            text = parts[0].get("text")
            return text.strip() if isinstance(text, str) else None
        except Exception as exc:
            logger.warning("Gemini call error: %s. Using deterministic fallback.", exc)
            self.last_error = {"exception": str(exc)}
            return None

    def _generate_with_gpt(self, prompt: str) -> Optional[str]:
        api_key = self._provider_key("gpt")
        if not api_key:
            self.last_error = {"reason": "missing_gpt_api_key"}
            return None

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.gpt_model,
            "temperature": 0.2,
            "max_tokens": 900,
            "messages": [
                {"role": "system", "content": "You are a QA automation engineering assistant."},
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                logger.warning(
                    "GPT call failed with status %s. Falling back to deterministic output.",
                    response.status_code,
                )
                self.last_error = {"status_code": response.status_code, "response": response.text}
                return None

            body = response.json()
            choices = body.get("choices") or []
            if not choices:
                self.last_error = {"reason": "empty_choices", "response": body}
                return None

            message = choices[0].get("message", {})
            content = message.get("content")
            if not isinstance(content, str):
                self.last_error = {"reason": "non_str_content", "response": body}
                return None

            return content.strip()
        except Exception as exc:
            logger.warning("GPT call error: %s. Using deterministic fallback.", exc)
            self.last_error = {"exception": str(exc)}
            return None

    @staticmethod
    def parse_json_payload(text: Optional[str]) -> Optional[dict]:
        """Parse JSON from plain or fenced model output."""
        if not text:
            return None

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            data = json.loads(cleaned)
            return data if isinstance(data, dict) else None
        except Exception:
            return None
