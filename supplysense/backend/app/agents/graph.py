"""
LangGraph orchestration graph.

Wires the Planner, Inventory, Shipment, Knowledge, Risk, Recommendation, and
Report agents into a single StateGraph. The Planner produces an ordered plan;
a router node dispatches to the next agent in `remaining_agents` after every
hop until the plan is exhausted, at which point the graph ends.
"""
from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from app.agents.inventory_agent import inventory_node
from app.agents.knowledge_agent import knowledge_node
from app.agents.planner_agent import planner_node
from app.agents.recommendation_agent import recommendation_node
from app.agents.report_agent import report_node
from app.agents.risk_agent import risk_node
from app.agents.shipment_agent import shipment_node
from app.agents.state import CopilotState
from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

AGENT_NODE_NAMES = {
    "inventory": "inventory",
    "shipment": "shipment",
    "knowledge": "knowledge",
    "risk": "risk",
    "recommendation": "recommendation",
    "report": "report_agent",
}


def route_after_planner(state: CopilotState) -> str:
    return _route_next(state)


def route_after_agent(state: CopilotState) -> str:
    return _route_next(state)


def _route_next(state: CopilotState) -> str:
    remaining = state.get("remaining_agents", [])
    iterations = state.get("iterations", 0)

    if iterations >= settings.agent_max_iterations:
        logger.warning("graph.max_iterations_reached", iterations=iterations)
        return END

    if not remaining:
        return END

    next_agent = remaining[0]
    return AGENT_NODE_NAMES.get(next_agent, END)


def _bump_iterations(state: CopilotState) -> CopilotState:
    state["iterations"] = state.get("iterations", 0) + 1
    return state


def build_graph():
    graph = StateGraph(CopilotState)

    graph.add_node("planner", planner_node)
    graph.add_node("inventory", inventory_node)
    graph.add_node("shipment", shipment_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("risk", risk_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("report_agent", report_node)

    graph.set_entry_point("planner")

    routing_map = {
        "inventory": "inventory",
        "shipment": "shipment",
        "knowledge": "knowledge",
        "risk": "risk",
        "recommendation": "recommendation",
        "report_agent": "report_agent",
        END: END,
    }

    graph.add_conditional_edges("planner", route_after_planner, routing_map)
    graph.add_conditional_edges("inventory", route_after_agent, routing_map)
    graph.add_conditional_edges("shipment", route_after_agent, routing_map)
    graph.add_conditional_edges("knowledge", route_after_agent, routing_map)
    graph.add_conditional_edges("risk", route_after_agent, routing_map)
    graph.add_conditional_edges("recommendation", route_after_agent, routing_map)
    graph.add_conditional_edges("report_agent", route_after_agent, routing_map)

    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
        logger.info("graph.compiled")
    return _compiled_graph


async def run_copilot_graph(session_id: str, user_message: str) -> CopilotState:
    graph = get_compiled_graph()
    initial_state: CopilotState = {
        "session_id": session_id,
        "user_message": user_message,
        "plan": [],
        "remaining_agents": [],
        "inventory_findings": [],
        "shipment_findings": [],
        "knowledge_findings": [],
        "risk_findings": [],
        "recommendations": [],
        "traces": [],
        "final_answer": "",
        "report_agent": None,
        "iterations": 0,
    }
    result = await graph.ainvoke(
        initial_state,
        config={"recursion_limit": settings.agent_recursion_limit},
    )
    return result
