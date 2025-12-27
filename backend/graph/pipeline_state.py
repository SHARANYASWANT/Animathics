from typing import TypedDict, Optional

class PipelineState(TypedDict):
    prompt: str

    manim_code: Optional[str]
    transcript: Optional[str]

    script_path: Optional[str]
    video_path: Optional[str]
    audio_path: Optional[str]

    error: Optional[str]
    retries: int

    scripts_dir: str
    videos_dir: str
