from agents.base import BaseAgent, AgentResult
from utils.prompts import build_fix_prompt
from utils.manim_cleaner import clean_manim_code

class FixAgent(BaseAgent):
    name = "FixAgent"

    def __init__(self, model):
        self.model = model

    def run(self, state: dict) -> AgentResult:
        try:
            # Safety check: Ensure we actually have an error and code to fix
            if not state.get("error") or not state.get("manim_code"):
                return AgentResult(False, error="No error or code available to fix")

            # Build prompt and generate fix
            prompt = build_fix_prompt(
                original_code=state["manim_code"],
                error_output=state["error"],
                topic=state["prompt"]
            )

            response = self.model.generate_content(prompt)
            fixed_code = clean_manim_code(response.text or state["manim_code"])

            return AgentResult(True, fixed_code)

        except Exception as e:
            return AgentResult(False, error=str(e))