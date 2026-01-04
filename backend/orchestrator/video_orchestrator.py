import uuid, os
from agents.test_agent import TestAgent
from agents.render_agent import RenderAgent

class VideoOrchestrator:
    def __init__(
        self,
        manim_agent,
        align_agent,
        audio_agent,
        scripts_dir,
        videos_dir
    ):
        self.manim_agent = manim_agent
        self.align_agent = align_agent
        self.audio_agent = audio_agent
        self.scripts_dir = scripts_dir
        self.videos_dir = videos_dir

        self.test_agent = TestAgent()
        self.render_agent = RenderAgent()

    def run(self, topic: str):
        manim = self.manim_agent.run(topic)
        if not manim.success:
            return manim

        aligned = self.align_agent.run(manim.data)
        code = aligned.data if aligned.success else manim.data

        script_name = f"video_{uuid.uuid4().hex}.py"
        script_path = os.path.join(self.scripts_dir, script_name)
        with open(script_path, "w") as f:
            f.write(code)

        test = self.test_agent.run(script_path)
        if not test.success:
            return test

        video = self.render_agent.run(script_path, self.videos_dir)
        if not video.success:
            return video

        return video
