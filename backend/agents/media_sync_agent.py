import subprocess
import os
import uuid

class MediaSyncAgent:
    def run(self, video_path: str, audio_path: str, output_dir: str):
        try:
            output_name = f"final_{uuid.uuid4().hex}.mp4"
            output_path = os.path.join(output_dir, output_name)

            cmd = [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]

            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            return {
                "success": True,
                "data": output_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
