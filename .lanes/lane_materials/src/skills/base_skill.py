from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseSkill(ABC):
    """
    Abstract Base Class for all Research Skills.
    Enforces a common interface for verification, configuration, and logging.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    def verify(self) -> bool:
        """
        Self-check: Is this skill ready to use?
        Should check for binary paths, API keys, or network connectivity.
        Returns:
            True if ready, False otherwise.
        """
        pass

    def log(self, message: str, level: str = "INFO"):
        """Standardized logging."""
        print(f"[{self.name}] {message}")
