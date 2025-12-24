from agents.base import BaseAgent, AgentResult
from utils.prompts import build_gemini_prompt
from utils.manim_cleaner import clean_manim_code

class GeminiManimAgent(BaseAgent):
    name = "GeminiManimAgent"

    def __init__(self, gemini_model):
        self.model = gemini_model

    def run(self, topic: str) -> AgentResult:
        try:
            prompt = build_gemini_prompt(topic)
            response = self.model.generate_content(prompt)
            text = response.text or ""
            manim_code = clean_manim_code(text)
            return AgentResult(True, manim_code)
        except Exception as e:
            return AgentResult(False, error=str(e))
        