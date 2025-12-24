import subprocess, glob, os
from agents.base import BaseAgent, AgentResult

class RenderAgent(BaseAgent):
    name = "RenderAgent"

    def run(self, script_path: str, videos_dir: str) -> AgentResult:
        proc = subprocess.run(
            ["manim", "-pql", script_path, "GeneratedScene"],
            capture_output=True,
            text=True
        )

        if proc.returncode != 0:
            return AgentResult(False, error=proc.stderr)

        name = os.path.splitext(os.path.basename(script_path))[0]
        matches = glob.glob(f"media/videos/{name}/**/GeneratedScene.mp4", recursive=True)

        if not matches:
            return AgentResult(False, error="Video not found")

        final_path = os.path.join(videos_dir, f"{name}.mp4")
        os.rename(matches[0], final_path)
        return AgentResult(True, final_path)
