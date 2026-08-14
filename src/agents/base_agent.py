"""Base Agent Contract Interface for QET Agent Accelerator."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from src.models.schemas import AppState
from src.utils.logger import logger


class BaseAgent(ABC):
    """Abstract base agent providing clean interface for specialist agents."""

    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description

    @abstractmethod
    def run(self, state: AppState) -> AppState:
        """Execute agent task and return updated state."""
        pass

    def log_start(self) -> None:
        logger.info(f"🤖 [Agent: {self.agent_name}] Starting execution...")

    def log_complete(self) -> None:
        logger.info(f"✅ [Agent: {self.agent_name}] Execution complete.")
