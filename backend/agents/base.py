from dataclasses import dataclass
from typing import Optional, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format="🧠 [%(name)s] %(message)s"
)

@dataclass
class AgentResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class BaseAgent:
    name = "BaseAgent"

    def log(self, msg: str):
        logging.getLogger(self.name).info(msg)

    def run(self, *args, **kwargs):
        raise NotImplementedError
