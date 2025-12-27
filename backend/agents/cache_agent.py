import hashlib
from storage.cache import get_cached_result, save_cached_result

def cache_agent(state):
    prompt = state["prompt"]
    key = hashlib.sha256(prompt.encode()).hexdigest()

    cached = get_cached_result(key)
    if cached:
        return {
            **state,
            "manim_code": cached["manim_code"],
            "transcript": cached["transcript"],
            "video_path": cached["video_path"]
        }

    state["cache_key"] = key
    return state


def cache_writeback_agent(state):
    if state.get("video_path"):
        save_cached_result(
            state["cache_key"],
            {
                "manim_code": state["manim_code"],
                "transcript": state["transcript"],
                "video_path": state["video_path"],
                "audio_path": state.get("audio_path")
            }
        )
    return state
