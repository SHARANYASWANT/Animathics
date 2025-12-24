from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class AgentResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class BaseAgent:
    name = "BaseAgent"

    def run(self, *args, **kwargs) -> AgentResult:
        raise NotImplementedError
