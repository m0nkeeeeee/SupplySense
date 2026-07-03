"""
Planner Agent.

The entry point of the multi-agent graph. Reads the user's natural-language
request and decides which specialist agents must run, and in what order, to
answer it. Produces a short, ordered plan (e.g. ["inventory", "shipment",
"risk", "recommendation"]) that the LangGraph router consumes.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.state import CopilotState
from app.services.bedrock_client import get_bedrock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_AGENTS = ["inventory", "shipment", "knowledge", "risk", "recommendation", "report_agent"]

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent inside an AI Supply Chain \
Copilot. You receive a user's question or request about supply chain \
operations (inventory, shipments, suppliers, risk, or reporting) and decide \
which specialist agents must run to answer it well.

Available specialist agents:
- inventory: stock levels, reorder points, safety stock, SKU-level data
- shipment: shipment tracking, ETAs, delays, carriers, routes
- knowledge: semantic search over SOPs, contracts, customs rules, past incident reports
- risk: identifies and scores supply chain risks (geopolitical, weather, supplier, logistics, demand)
- recommendation: synthesizes findings from other agents into concrete action items
- report: compiles a structured report/summary document from the conversation

Rules:
- Only include agents that are actually needed.
- "recommendation" should usually run after the data-gathering agents it depends on.
- "report" should only run if the user explicitly asks for a report, summary document, or export.
- Order matters: list agents in the sequence they should execute.

Respond with ONLY JSON in this exact shape:
{"plan": ["agent_name", "agent_name"], "reasoning": "one sentence"}
"""


async def planner_node(state: CopilotState) -> Dict[str, Any]:
    user_message = state["user_message"]
    bedrock = get_bedrock_client()

    result = await bedrock.generate_json(
        prompt=f"User request:\n{user_message}",
        system=PLANNER_SYSTEM_PROMPT,
    )

    plan: List[str] = [a for a in result.get("plan", []) if a in VALID_AGENTS]

    if not plan:
        # Safe heuristic fallback if the model output couldn't be parsed.
        plan = _heuristic_plan(user_message)
    else:
        # Ensure recommendation always runs after data-gathering agents
        data_gatherers = {"inventory", "shipment", "knowledge", "risk"}
        if any(a in data_gatherers for a in plan) and "recommendation" not in plan:
            plan.append("recommendation")

    reasoning = result.get("reasoning", "Heuristic fallback plan used.")
    logger.info("planner.plan_created", plan=plan, reasoning=reasoning)

    return {
        "plan": plan,
        "remaining_agents": plan.copy(),
        "iterations": state.get("iterations", 0) + 1,
        "traces": [
            {
                "agent": "planner",
                "action": "create_plan",
                "output_summary": f"Plan: {' -> '.join(plan)}. {reasoning}",
            }
        ],
    }


def _heuristic_plan(message: str) -> List[str]:
    text = message.lower()
    plan: List[str] = []
    if any(k in text for k in ["stock", "inventory", "reorder", "sku", "warehouse"]):
        plan.append("inventory")
    if any(k in text for k in ["shipment", "delivery", "eta", "carrier", "delay", "route", "tracking"]):
        plan.append("shipment")
    if any(k in text for k in ["policy", "sop", "contract", "procedure", "customs", "compliance"]):
        plan.append("knowledge")
    if any(k in text for k in ["risk", "disrupt", "weather", "geopolit", "strike", "outage"]):
        plan.append("risk")
    if not plan:
        plan = ["inventory", "shipment", "risk"]
    plan.append("recommendation")
    if any(k in text for k in ["report", "summary document", "export", "pdf"]):
        plan.append("report_agent")
    return plan
