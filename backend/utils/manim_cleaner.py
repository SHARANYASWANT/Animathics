import re

def clean_manim_code(manim_code: str) -> str:
    manim_code = re.sub(r"^```(?:python)?", "", manim_code, flags=re.MULTILINE)
    manim_code = re.sub(r"```$", "", manim_code, flags=re.MULTILINE).strip()

    manim_code = manim_code.replace(r"\c", r"\\c")

    manim_code = re.sub(r"class\s+\w+\s*\(", "class GeneratedScene(", manim_code)

    if "class GeneratedScene" in manim_code and "Scene" not in manim_code.split("class GeneratedScene")[1]:
        manim_code = manim_code.replace(
            "class GeneratedScene(",
            "class GeneratedScene(Scene):"
        )

    if "class GeneratedScene" not in manim_code:
        manim_code = (
            "from manim import *\n\n"
            "class GeneratedScene(Scene):\n"
            "    def construct(self):\n"
            "        self.add(Text('Error: Scene could not be generated'))\n"
        )

    return manim_code
