from abc import ABC, abstractmethod
from typing import Any, Dict

class Planner(ABC):
    @abstractmethod
    def plan(self, user_input: str) -> Dict[str, Any]:
        """
        Abstract method to create a plan based on user input.

        Args:
            user_input: The input provided by the user.

        Returns:
            A dictionary or other data structure representing the execution plan.
        """
        pass