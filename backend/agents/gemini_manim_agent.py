import re
from agents.base import BaseAgent, AgentResult
from utils.prompts import build_gemini_prompt
from utils.manim_cleaner import clean_manim_code

class GeminiManimAgent(BaseAgent):
    name = "GeminiManimAgent"

    def __init__(self, model):
        self.model = model

    def run(self, topic: str) -> AgentResult:
        try:
            prompt = build_gemini_prompt(topic)
            response = self.model.generate_content(prompt)
            text = response.text or ""
            manim_pattern = r"===MANIM_CODE===\s*(.*?)===AUDIO_SCRIPT==="
            manim_match = re.search(manim_pattern, text, re.DOTALL)

            audio_pattern = r"===AUDIO_SCRIPT===\s*(.*)"
            audio_match = re.search(audio_pattern, text, re.DOTALL)

            if not manim_match or not audio_match:
                fallback_manim = re.search(r"MANIM_CODE:\s*```python(.*?)```", text, re.DOTALL | re.IGNORECASE)
                fallback_audio = re.search(r"AUDIO_SCRIPT:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
                
                if fallback_manim and fallback_audio:
                     manim_match = fallback_manim
                     audio_match = fallback_audio
                else:
                    return AgentResult(
                        False,
                        error="Gemini output missing required sections (===MANIM_CODE=== or ===AUDIO_SCRIPT===)"
                    )

            raw_code = manim_match.group(1).strip()
            audio_script = audio_match.group(1).strip()
            if raw_code.startswith("```"):
                lines = raw_code.split('\n')
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw_code = "\n".join(lines).strip()

            manim_code = clean_manim_code(raw_code)

            return AgentResult(
                True,
                {
                    "manim_code": manim_code,
                    "audio_script": audio_script,
                }
            )

        except Exception as e:
            return AgentResult(False, error=str(e))