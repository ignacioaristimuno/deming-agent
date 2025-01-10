"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from react_agent.actions import (
    plan_action,
    do_action,
    check_action,
    act_action,
    generate_final_answer,
    route_after_check_phase,
    route_after_act_phase,
    route_tools_usage,
    clean_step_vars,
)
from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS


# Define a new graph
workflow = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the nodes in the desired order
workflow.add_node("plan", plan_action)
workflow.add_node("do", do_action)
workflow.add_node("check", check_action)
workflow.add_node("act", act_action)
workflow.add_node("tools", ToolNode(TOOLS))
workflow.add_node("clean_vars", clean_step_vars)
workflow.add_node("final_answer_generation", generate_final_answer)

# Add edges
workflow.add_edge("__start__", "plan")
workflow.add_edge("plan", "do")
workflow.add_conditional_edges("do", route_tools_usage)
workflow.add_edge("tools", "do")
workflow.add_conditional_edges("check", route_after_check_phase)
workflow.add_conditional_edges("act", route_after_act_phase)
workflow.add_edge("clean_vars", "plan")
workflow.add_edge("final_answer_generation", "__end__")


# Compile the workflow into an executable graph
graph = workflow.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "PDCA Agent"
