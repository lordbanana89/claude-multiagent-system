"""
Basic LangGraph agent example
"""
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    messages: list

def agent_node(state: AgentState):
    return {
        "messages": state["messages"] + ["Hello from LangGraph agent!"]
    }

# Create the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_edge("agent", END)

# Compile the graph
graph = workflow.compile()