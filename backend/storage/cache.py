from langgraph.graph import StateGraph, END
from backend.agents.cache_agent import cache_agent
from backend.agents.gemini_manim_agent import gemini_agent
from backend.agents.alignment_agent import alignment_agent
from backend.agents.test_agent import test_agent
from backend.agents.fix_agent import fix_agent
from backend.agents.render_agent import render_agent
from backend.agents.audio_agent import audio_agent

graph = StateGraph(PipelineState)

graph.add_node("cache", cache_agent)
graph.add_node("gemini", gemini_agent)
graph.add_node("align", alignment_agent)
graph.add_node("test", test_agent)
graph.add_node("fix", fix_agent)
graph.add_node("render", render_agent)
graph.add_node("audio", audio_agent)

graph.set_entry_point("cache")

graph.add_edge("cache", "gemini")
graph.add_edge("gemini", "align")
graph.add_edge("align", "test")

graph.add_conditional_edges(
    "test",
    lambda s: "fix" if s["error"] else "render",
    {"fix": "fix", "render": "render"}
)

graph.add_edge("fix", "test")

# 🔥 PARALLEL EXECUTION
graph.add_edge("render", "audio")
graph.add_edge("render", END)
graph.add_edge("audio", END)

pipeline = graph.compile()
