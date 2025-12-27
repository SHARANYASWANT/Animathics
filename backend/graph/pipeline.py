from langgraph.graph import StateGraph, END
from graph.pipeline_state import PipelineState
from agents.langgraph_nodes import fix_node


from agents.langgraph_nodes import (
    gemini_node,
    alignment_node,
    save_script_node,
    test_node,
    render_node,
    audio_node,
)

def route_after_test(state):
    # 1. Success!
    if state.get("test_passed"):
        return "render"

    # 2. Fixable Error: We have an error AND code exists AND retries left
    if (state.get("error") and 
        state.get("manim_code") and  # <--- ADD THIS CHECK
        state.get("retries", 0) < 2):
        return "fix"

    # 3. Critical Failure (No code generated) or Max Retries
    return "end"

def build_pipeline(agents):
    graph = StateGraph(PipelineState)

    graph.add_node("gemini", lambda s: gemini_node(s, agents))
    graph.add_node("align", lambda s: alignment_node(s, agents))
    graph.add_node("save_script", lambda s: save_script_node(s, agents))
    graph.add_node("test", lambda s: test_node(s, agents))
    graph.add_node("render", lambda s: render_node(s, agents))
    graph.add_node("audio", lambda s: audio_node(s, agents))
    graph.add_node("fix", lambda s: fix_node(s, agents))




    graph.set_entry_point("gemini")

    graph.add_edge("gemini", "align")
    graph.add_edge("align", "save_script")
    graph.add_edge("save_script", "test")

    graph.add_conditional_edges(
    "test",
    route_after_test,
    {
        "render": "render",
        "fix": "fix",
        "end": END,
    }
)

    graph.add_edge("fix", "save_script")



    # Parallel
    graph.add_edge("render", "audio")
    # graph.add_edge("render", END)
    graph.add_edge("audio", END)

    return graph.compile()
