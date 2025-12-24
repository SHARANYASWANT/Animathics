import subprocess
from agents.base import BaseAgent, AgentResult

class TestAgent(BaseAgent):
    name = "TestAgent"

    def run(self, script_path: str) -> AgentResult:
        proc = subprocess.run(
            ["python", "-m", "py_compile", script_path],
            capture_output=True,
            text=True
        )

        if proc.returncode == 0:
            return AgentResult(True)

        return AgentResult(False, error=proc.stderr)
