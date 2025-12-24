from agents.base import BaseAgent, AgentResult
from utils.manim_cleaner import clean_manim_code
from utils.prompts import build_alignment_prompt

class AlignmentAgent(BaseAgent):
    name = "AlignmentAgent"

    def __init__(self, gemini_model):
        self.model = gemini_model

    def run(self, manim_code: str) -> AgentResult:
        try:
            prompt = build_alignment_prompt(manim_code)
            response = self.model.generate_content(prompt)
            fixed = clean_manim_code(response.text or manim_code)
            return AgentResult(True, fixed)
        except Exception as e:
            return AgentResult(False, error=str(e))
