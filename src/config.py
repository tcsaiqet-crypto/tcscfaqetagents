"""Central Configuration for QET Agent Accelerator (V1)."""

import os
import re
from pathlib import Path
from typing import Set, Literal, List, Iterable
from pydantic import BaseModel, Field
from src.services.ai_settings_store import load_ai_settings_dict


class ExecutionFeatureFlags(BaseModel):
    """Execution feature enablement map for V1."""
    playwright_ui_enabled: bool = True
    url_execution_enabled: bool = False
    api_testing_enabled: bool = False
    performance_testing_enabled: bool = False
    accessibility_execution_enabled: bool = False
    security_scanning_enabled: bool = False
    enable_requirement_categorization: bool = Field(default_factory=lambda: os.getenv("QET_ENABLE_REQUIREMENT_CATEGORIZATION", "0") in {"1", "true", "yes"})


class AppConfig(BaseModel):
    """Application configuration and limit parameters."""
    app_name: str = "QET Agent Accelerator — CFA Digital Journey"
    version: str = "1.0.0"
    
    # Safe ZIP Extraction Limits
    # Applied only to *useful* files remaining after junk_dir_patterns exclusion,
    # so legitimate codebases with large dependency trees aren't rejected outright.
    max_zip_file_count: int = 20000
    max_zip_total_bytes: int = 300 * 1024 * 1024  # 300 MB
    max_single_file_bytes: int = 10 * 1024 * 1024  # 10 MB
    forbidden_extensions: Set[str] = Field(
        default_factory=lambda: {
            ".exe", ".dll", ".bat", ".cmd", ".sh", ".ps1", ".vbs", ".pyc", ".so", ".dylib"
        }
    )
    # Directory names skipped during ZIP extraction (dependency/build/vcs noise, not useful for analysis)
    junk_dir_patterns: Set[str] = Field(
        default_factory=lambda: {
            "node_modules", ".git", ".hg", ".svn", "dist", "build", "out",
            ".next", ".nuxt", "venv", ".venv", "env", "__pycache__",
            ".pytest_cache", ".mypy_cache", "target", "vendor", "bin", "obj",
            "coverage", ".idea", ".vscode", ".tox", "site-packages",
            ".gradle", ".terraform", "egg-info",
        }
    )
    
    # Working Directories
    workspace_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "QET_WORKSPACE_DIR",
                str(Path(__file__).parent.parent / "workspace")
            )
        )
    )
    
    # Feature Flags
    features: ExecutionFeatureFlags = Field(default_factory=ExecutionFeatureFlags)

    _placeholder_key_patterns = (
        re.compile(r"^test[-_].*key$", re.IGNORECASE),
        re.compile(r"^your[_-].*key$", re.IGNORECASE),
        re.compile(r"^replace[_-].*key$", re.IGNORECASE),
        re.compile(r"^paste[_-].*key$", re.IGNORECASE),
        re.compile(r"^dummy[-_].*", re.IGNORECASE),
    )

    def get_extracted_source_dir(self) -> Path:
        p = self.workspace_dir / "extracted_source"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_reports_dir(self) -> Path:
        p = self.workspace_dir / "reports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_keys_dir(self) -> Path:
        """Return optional local keys directory for developer environments."""
        return Path(__file__).parent.parent / "keys"

    def _read_candidate_keys_from_files(self, file_paths: Iterable[Path]) -> List[str]:
        keys: List[str] = []
        for file_path in file_paths:
            if not file_path.exists():
                continue
            try:
                raw_value = file_path.read_text(encoding="utf-8").strip()
            except Exception:
                continue
            sanitized = self._sanitize_provider_key(raw_value)
            if sanitized and sanitized not in keys:
                keys.append(sanitized)
        return keys

    def get_provider_api_keys(self, provider: Literal["gemini", "gpt"]) -> List[str]:
        """Return all usable API keys for a provider in priority order."""
        runtime_keys = load_ai_settings_dict().get("provider_keys", {})
        keys: List[str] = []

        def add_candidate(raw_value: object) -> None:
            if isinstance(raw_value, list):
                for item in raw_value:
                    add_candidate(item)
                return
            sanitized = self._sanitize_provider_key(str(raw_value or ""))
            if sanitized and sanitized not in keys:
                keys.append(sanitized)

        if isinstance(runtime_keys, dict):
            add_candidate(runtime_keys.get(provider, ""))

        if provider == "gemini":
            add_candidate(os.getenv("GEMINI_API_KEY"))
            add_candidate(os.getenv("GOOGLE_API_KEY"))
            keys_dir = self.get_keys_dir()
            project_keys_dir = Path(__file__).resolve().parents[2] / "keys"
            keys.extend(
                [
                    key for key in self._read_candidate_keys_from_files(
                        [
                            keys_dir / "gemini keys.txt",
                            keys_dir / "gemini keys 2.txt",
                            keys_dir / "gemapikey1.txt",
                            keys_dir / "gemapikey2.txt",
                            project_keys_dir / "gemini keys.txt",
                            project_keys_dir / "gemini keys 2.txt",
                            project_keys_dir / "gemapikey1.txt",
                            project_keys_dir / "gemapikey2.txt",
                            Path(__file__).parent.parent / "api" / "gemapikey1.txt",
                            Path(__file__).parent.parent / "api" / "gemapikey2.txt",
                        ]
                    )
                    if key not in keys
                ]
            )
        else:
            add_candidate(os.getenv("OPENAI_API_KEY"))
            keys_dir = self.get_keys_dir()
            project_keys_dir = Path(__file__).resolve().parents[2] / "keys"
            keys.extend(
                [
                    key for key in self._read_candidate_keys_from_files(
                        [
                            keys_dir / "openai keys.txt",
                            keys_dir / "openai_api_key.txt",
                            project_keys_dir / "openai keys.txt",
                            project_keys_dir / "openai_api_key.txt",
                        ]
                    )
                    if key not in keys
                ]
            )

        return keys

    def get_active_provider(self) -> Literal["gemini", "gpt"]:
        runtime_provider = str(load_ai_settings_dict().get("active_provider", "")).strip().lower()
        if runtime_provider in {"gemini", "gpt"}:
            return "gpt" if runtime_provider == "gpt" else "gemini"
        provider = os.getenv("QET_AI_PROVIDER", "gemini").strip().lower()
        return "gpt" if provider == "gpt" else "gemini"

    def _sanitize_provider_key(self, raw_value: str) -> str:
        key = str(raw_value or "").strip()
        if not key:
            return ""
        lowered = key.lower()
        if "placeholder" in lowered or "example" in lowered:
            return ""
        for pattern in self._placeholder_key_patterns:
            if pattern.match(key):
                return ""
        return key

    def is_llm_enabled(self) -> bool:
        """LLM calls are enabled by default when provider credentials are present."""
        raw = os.getenv("QET_ENABLE_LLM", "1").strip().lower()
        if raw in {"0", "false", "no", "off"}:
            return False
        return True

    def get_provider_api_key(self, provider: Literal["gemini", "gpt"]) -> str:
        keys = self.get_provider_api_keys(provider)
        return keys[0] if keys else ""

    def get_api_key(self) -> str:
        """Backward-compatible accessor for active provider key."""
        active = self.get_active_provider()
        return self.get_provider_api_key(active) or self.get_provider_api_key("gemini") or self.get_provider_api_key("gpt")


config = AppConfig()

