"""Lightweight LLM service wrapper for Gemini and GPT text generation.

Gemini's model catalog changes over time and hardcoded model names can 404
for a given API key/version, so the active Gemini model is auto-discovered
from the caller's own key via the ListModels endpoint and cached in-process.
"""

import json
import os
import re
from typing import Any, Dict, Optional, Tuple

import requests

from src.config import config
from src.utils.logger import logger

# Process-wide caches keyed by API key: full ranked candidate list, and the
# first candidate that has actually succeeded a real generateContent call
# (ListModels metadata can list models that are deprecated/restricted per-key
# even though they claim to support generateContent).
_GEMINI_CANDIDATES_CACHE: Dict[str, list] = {}
_GEMINI_WORKING_MODEL_CACHE: Dict[str, str] = {}

# Preview/specialized model families excluded from text-generation candidate ranking.
_GEMINI_EXCLUDE_KEYWORDS = (
    "preview", "tts", "image", "computer-use", "robotics",
    "lyria", "deep-research", "antigravity", "nano-banana", "customtools", "gemma",
)


class LLMService:
    """Provider wrapper. Callers must treat a None return as a real failure -
    inspect `last_error` for diagnostics rather than substituting sample data."""

    def __init__(self) -> None:
        self.gemini_model = "gemini-3.7-flash"
        self.gpt_model = "gpt-4o-mini"
        self.timeout_seconds = 30
        self.last_error: Optional[Dict[str, Any]] = None

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

    @staticmethod
    def _provider_keys(provider: str) -> list[str]:
        provider_keys_getter = getattr(config, "get_provider_api_keys", None)
        if callable(provider_keys_getter):
            try:
                keys = provider_keys_getter("gpt" if provider == "gpt" else "gemini")
                if isinstance(keys, list):
                    return [str(key) for key in keys if str(key).strip()]
            except Exception:
                pass
        key = LLMService._provider_key(provider)
        return [key] if key else []

    def is_enabled(self) -> bool:
        provider = self._active_provider()
        llm_enabled = True
        llm_enabled_getter = getattr(config, "is_llm_enabled", None)
        if callable(llm_enabled_getter):
            try:
                llm_enabled = bool(llm_enabled_getter())
            except Exception:
                llm_enabled = True
        return llm_enabled and bool(self._provider_keys(provider))

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
        provider_keys = self._provider_keys(provider)
        has_key = bool(provider_keys)
        model = None
        if has_key:
            if provider == "gpt":
                model = self.gpt_model
            else:
                for candidate_key in provider_keys:
                    model = self.get_gemini_model(candidate_key)
                    if model:
                        break
        if not enabled:
            state = "Disabled"
        elif has_key:
            state = "Ready"
        else:
            state = "Misconfigured"
        return {"provider": provider, "enabled": enabled, "has_key": has_key, "state": state, "model": model}

    def generate_text(self, prompt: str) -> Optional[str]:
        """Return model text when available; otherwise return None (see `last_error`)."""
        self.last_error = None
        if not self.is_enabled():
            self.last_error = {"error_code": "provider_disabled", "error_message": "LLM provider disabled or missing API key."}
            return None

        provider = self._active_provider()
        if provider == "gpt":
            for api_key in self._provider_keys("gpt"):
                text = self._generate_with_gpt(prompt, api_key)
                if text is not None:
                    return text
            return None

        api_keys = self._provider_keys("gemini")
        if not api_keys:
            self.last_error = {"error_code": "provider_key_missing", "error_message": "Gemini API key not configured."}
            return None
        text, attempts = self.generate_with_gemini(prompt, api_keys)
        if text is None and attempts:
            self.last_error = attempts[-1]
        return text

    def get_gemini_model(self, api_key: str) -> Optional[str]:
        """Return the best-known working Gemini model for this key (for display/provenance)."""
        if api_key in _GEMINI_WORKING_MODEL_CACHE:
            return _GEMINI_WORKING_MODEL_CACHE[api_key]
        candidates = self.list_gemini_candidates(api_key)
        return candidates[0] if candidates else None

    @staticmethod
    def _rank_gemini_candidates(names: list) -> list:
        def excluded(name: str) -> bool:
            return any(keyword in name for keyword in _GEMINI_EXCLUDE_KEYWORDS)

        filtered = [n for n in names if n and not excluded(n)] or [n for n in names if n]

        def score(name: str) -> tuple:
            is_latest = name.endswith("-latest")
            is_flash = "flash" in name and "lite" not in name
            is_flash_lite = "flash" in name and "lite" in name
            is_pro = "pro" in name
            tier = 0 if is_flash else (1 if is_flash_lite else (2 if is_pro else 3))
            return (0 if is_latest else 1, tier, name)

        return sorted(filtered, key=score)

    def list_gemini_candidates(self, api_key: str) -> list:
        """Discover and rank Gemini models supporting generateContent for this API key, caching the list."""
        if api_key in _GEMINI_CANDIDATES_CACHE:
            return _GEMINI_CANDIDATES_CACHE[api_key]

        try:
            response = requests.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key},
                timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                self.last_error = {
                    "error_code": "model_discovery_failed",
                    "error_message": f"Gemini ListModels returned status {response.status_code}.",
                    "diagnostics": {"status_code": response.status_code, "response": response.text[:300]},
                }
                return []

            models = response.json().get("models") or []
            names = [
                m.get("name", "").removeprefix("models/")
                for m in models
                if "generateContent" in (m.get("supportedGenerationMethods") or [])
            ]
            names = [n for n in names if n]
            if not names:
                self.last_error = {
                    "error_code": "model_discovery_failed",
                    "error_message": "No Gemini models supporting generateContent are available for this API key.",
                    "diagnostics": {"model_count": len(models)},
                }
                return []

            ranked = self._rank_gemini_candidates(names)
            _GEMINI_CANDIDATES_CACHE[api_key] = ranked
            return ranked
        except Exception as exc:
            self.last_error = {
                "error_code": "model_discovery_failed",
                "error_message": f"Gemini ListModels request error: {exc}",
                "diagnostics": {"exception": str(exc)},
            }
            return []

    def _call_gemini_model(self, model: str, api_key: str, prompt: str) -> Optional[str]:
        """Single-attempt raw call to one Gemini model. Sets `last_error` and returns None on failure."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2500},
            "contents": [{"parts": [{"text": prompt}]}],
        }
        try:
            response = requests.post(
                url, json=payload, headers={"Content-Type": "application/json"}, timeout=self.timeout_seconds,
            )
            if response.status_code != 200:
                self.last_error = {
                    "error_code": "provider_disabled" if response.status_code == 404 else "invalid_model_json",
                    "error_message": f"Gemini model '{model}' returned status {response.status_code}.",
                    "diagnostics": {"status_code": response.status_code, "response": response.text[:300], "model": model},
                }
                return None

            body = response.json()
            candidates = body.get("candidates") or []
            parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
            text = parts[0].get("text") if parts else None
            if not isinstance(text, str) or not text.strip():
                self.last_error = {"error_code": "invalid_model_json", "error_message": f"Gemini model '{model}' returned no usable content.", "diagnostics": {"model": model}}
                return None
            return text.strip()
        except requests.exceptions.Timeout:
            self.last_error = {"error_code": "model_timeout", "error_message": f"Gemini model '{model}' request timed out.", "diagnostics": {"model": model, "timeout_seconds": self.timeout_seconds}}
            return None
        except Exception as exc:
            self.last_error = {"error_code": "invalid_model_json", "error_message": f"Gemini connection error: {exc}", "diagnostics": {"model": model, "exception": str(exc)}}
            return None

    def generate_with_gemini(self, prompt: str, api_keys: str | list[str]) -> Tuple[Optional[str], list]:
        """Try candidate Gemini models in priority order until one actually succeeds.

        Returns (text, attempts). `text` is None only if every candidate failed;
        `attempts` always lists every model tried with its failure diagnostics.
        """
        candidate_keys = [api_keys] if isinstance(api_keys, str) else list(api_keys)
        candidate_keys = [str(key).strip() for key in candidate_keys if str(key).strip()]
        attempts = []

        for key_index, api_key in enumerate(candidate_keys):
            candidates = self.list_gemini_candidates(api_key)
            if not candidates:
                attempts.append({"key_index": key_index, "provider_key": True, "error_code": "model_discovery_failed", **(self.last_error or {})})
                continue

            working = _GEMINI_WORKING_MODEL_CACHE.get(api_key)
            order = ([working] if working else []) + [c for c in candidates if c != working]

            for model in order:
                text = self._call_gemini_model(model, api_key, prompt)
                if text:
                    _GEMINI_WORKING_MODEL_CACHE[api_key] = model
                    return text, attempts
                attempts.append({"key_index": key_index, "model": model, **(self.last_error or {})})
        return None, attempts

    def _generate_with_gpt(self, prompt: str, api_key: Optional[str] = None) -> Optional[str]:
        api_key = api_key or config.get_provider_api_key("gpt")
        if not api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.gpt_model,
            "temperature": 0.2,
            "max_tokens": 2500,
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
                logger.warning("GPT call failed with status %s.", response.status_code)
                self.last_error = {
                    "error_code": "provider_disabled",
                    "error_message": f"OpenAI API returned status {response.status_code}.",
                    "diagnostics": {"status_code": response.status_code, "response": response.text[:300]},
                }
                return None

            body = response.json()
            choices = body.get("choices") or []
            if not choices:
                self.last_error = {"error_code": "invalid_model_json", "error_message": "OpenAI returned no choices.", "diagnostics": {}}
                return None

            message = choices[0].get("message", {})
            content = message.get("content")
            if not isinstance(content, str):
                self.last_error = {"error_code": "invalid_model_json", "error_message": "OpenAI choice had no text content.", "diagnostics": {}}
                return None

            return content.strip()
        except Exception as exc:
            logger.warning("GPT call error: %s", exc)
            self.last_error = {"error_code": "invalid_model_json", "error_message": f"OpenAI connection error: {exc}", "diagnostics": {"exception": str(exc)}}
            return None

    @staticmethod
    def parse_json_payload(text: Optional[str]) -> Optional[dict]:
        """Backward compatible parser returning only parsed dict or None."""
        parsed, _ = LLMService.parse_json_payload_with_diagnostics(text)
        return parsed

    @staticmethod
    def parse_json_payload_with_diagnostics(text: Optional[str]) -> Tuple[Optional[dict], Optional[Dict[str, Any]]]:
        """Parse JSON with fence handling, light repair, and diagnostics.

        Returns a tuple: (parsed_dict_or_none, diagnostics_or_none)
        """
        if not text:
            return None, {
                "parser_stage": "input",
                "issue": "Empty model response",
                "recovery_attempted": False,
            }

        cleaned = text.strip()
        recovery_attempted = False

        if cleaned.startswith("```"):
            # Accept clean fenced content like ```json ... ``` while rejecting malformed blocks.
            full_fence_match = re.match(r"^```(?:json|JSON)?\s*([\s\S]*?)\s*```$", cleaned)
            if full_fence_match:
                cleaned = full_fence_match.group(1).strip()
            else:
                partial_match = re.search(r"```(?:json|JSON)?\s*([\s\S]*?)\s*```", cleaned)
                if partial_match:
                    cleaned = partial_match.group(1).strip()
                    recovery_attempted = True
                else:
                    return None, {
                        "parser_stage": "fence_extraction",
                        "issue": "Detected markdown fence but could not extract a closed JSON block.",
                        "recovery_attempted": recovery_attempted,
                        "raw_preview": cleaned[:300],
                    }

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return data, None
            return None, {
                "parser_stage": "type_check",
                "issue": f"Parsed payload type is {type(data).__name__}; expected object.",
                "recovery_attempted": recovery_attempted,
                "raw_preview": cleaned[:300],
            }
        except json.JSONDecodeError as first_error:
            # Lightweight repair: remove trailing commas before } or ]
            repaired = re.sub(r",\s*([}\]])", r"\1", cleaned)
            if repaired != cleaned:
                recovery_attempted = True
                try:
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        return data, {
                            "parser_stage": "repair",
                            "issue": "Recovered by removing trailing commas.",
                            "recovery_attempted": True,
                        }
                    return None, {
                        "parser_stage": "type_check",
                        "issue": f"Parsed repaired payload type is {type(data).__name__}; expected object.",
                        "recovery_attempted": True,
                        "raw_preview": repaired[:300],
                    }
                except json.JSONDecodeError:
                    pass

            likely_truncated = LLMService._looks_truncated_json(cleaned)
            return None, {
                "parser_stage": "json_decode",
                "issue": "Likely truncated JSON output." if likely_truncated else "JSON syntax decode failed.",
                "recovery_attempted": recovery_attempted,
                "line": first_error.lineno,
                "column": first_error.colno,
                "raw_preview": cleaned[:350],
            }
        except Exception as exc:
            return None, {
                "parser_stage": "unknown",
                "issue": f"Unexpected parser failure: {exc}",
                "recovery_attempted": recovery_attempted,
                "raw_preview": cleaned[:300],
            }

    @staticmethod
    def _looks_truncated_json(text: str) -> bool:
        depth = 0
        in_string = False
        escape = False

        for ch in text:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch in "[{":
                depth += 1
            elif ch in "]}":
                depth -= 1

        return depth != 0 or in_string or escape



