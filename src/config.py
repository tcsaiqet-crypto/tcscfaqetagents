"""Central Configuration for QET Agent Accelerator (V1)."""

import os
from pathlib import Path
from typing import Set, Literal
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

    def get_active_provider(self) -> Literal["gemini", "gpt"]:
        runtime_provider = str(load_ai_settings_dict().get("active_provider", "")).strip().lower()
        if runtime_provider in {"gemini", "gpt"}:
            return "gpt" if runtime_provider == "gpt" else "gemini"
        provider = os.getenv("QET_AI_PROVIDER", "gemini").strip().lower()
        return "gpt" if provider == "gpt" else "gemini"

    def is_llm_enabled(self) -> bool:
        """LLM calls are enabled by default when provider credentials are present."""
        raw = os.getenv("QET_ENABLE_LLM", "1").strip().lower()
        if raw in {"0", "false", "no", "off"}:
            return False
        return True

    def get_provider_api_key(self, provider: Literal["gemini", "gpt"]) -> str:
        runtime_keys = load_ai_settings_dict().get("provider_keys", {})
        runtime_key = str(runtime_keys.get(provider, "")).strip() if isinstance(runtime_keys, dict) else ""
        if runtime_key:
            return runtime_key

        if provider == "gemini":
            env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key.strip()

            keys_dir = self.get_keys_dir()
            for key_file in ["gemini keys.txt", "gemapikey1.txt", "gemapikey2.txt"]:
                f_path = keys_dir / key_file
                if f_path.exists():
                    try:
                        with open(f_path, "r", encoding="utf-8") as f:
                            key_val = f.read().strip()
                            if key_val:
                                return key_val
                    except Exception:
                        pass

            api_dir = Path(__file__).parent.parent / "api"
            for key_file in ["gemapikey1.txt", "gemapikey2.txt"]:
                f_path = api_dir / key_file
                if f_path.exists():
                    try:
                        with open(f_path, "r", encoding="utf-8") as f:
                            key_val = f.read().strip()
                            if key_val:
                                return key_val
                    except Exception:
                        pass
            return ""

        env_key = os.getenv("OPENAI_API_KEY")
        if env_key:
            return env_key.strip()

        keys_dir = self.get_keys_dir()
        for key_file in ["openai keys.txt", "openai_api_key.txt"]:
            f_path = keys_dir / key_file
            if f_path.exists():
                try:
                    with open(f_path, "r", encoding="utf-8") as f:
                        key_val = f.read().strip()
                        if key_val:
                            return key_val
                except Exception:
                    pass
        return ""

    def get_api_key(self) -> str:
        """Backward-compatible accessor for active provider key."""
        return self.get_provider_api_key(self.get_active_provider())


config = AppConfig()
