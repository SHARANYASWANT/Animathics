import hashlib
from storage.cache import get_cached_result

def cache_agent(state):
    prompt = state["prompt"]
    key = hashlib.sha256(prompt.encode()).hexdigest()

    cached = get_cached_result(key)
    if cached:
        return {
            **state,
            "manim_code": cached["manim_code"],
            "transcript": cached["transcript"]
        }

    return state
