"""Persistence for runtime AI provider selection and key overrides."""

import json
from pathlib import Path
from typing import Any, Dict


def _settings_path() -> Path:
    return Path(__file__).resolve().parents[2] / "workspace" / "ai_settings.json"


def load_ai_settings_dict() -> Dict[str, Any]:
    path = _settings_path()
    if not path.exists():
        return {"active_provider": "gemini", "provider_keys": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"active_provider": "gemini", "provider_keys": {}}
        provider_keys = data.get("provider_keys")
        return {
            "active_provider": str(data.get("active_provider", "gemini")).strip().lower() or "gemini",
            "provider_keys": provider_keys if isinstance(provider_keys, dict) else {},
        }
    except Exception:
        return {"active_provider": "gemini", "provider_keys": {}}


def save_ai_settings_dict(active_provider: str, provider_keys: Dict[str, str]) -> Path:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized_keys = {
        str(provider).strip().lower(): str(value).strip()
        for provider, value in provider_keys.items()
        if str(value).strip()
    }
    payload = {
        "active_provider": "gpt" if str(active_provider).strip().lower() == "gpt" else "gemini",
        "provider_keys": sanitized_keys,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
