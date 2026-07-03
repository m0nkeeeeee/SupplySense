"""
Risk Agent.

Synthesizes findings from the Inventory, Shipment, and Knowledge agents
(whatever has run so far), combines them with any externally logged risk
events in MongoDB, and produces severity-scored risk findings. Persists
newly identified risks to MongoDB for the dashboard and audit trail.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.state import CopilotState
from app.database import COLL_RISK_EVENTS, get_db
from app.models.schemas import RiskEvent, RiskSeverity
from app.services.bedrock_client import get_bedrock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

RISK_SYSTEM_PROMPT = """You are the Risk Agent in an AI Supply Chain \
Copilot. You receive findings from other agents (inventory levels, shipment \
delays, knowledge base excerpts) plus any logged risk events. Identify and \
score the most important supply chain risks implied by this information. \
For each risk, classify category (geopolitical, weather, supplier, \
logistics, demand) and severity (low, medium, high, critical).

Respond with ONLY JSON in this exact shape:
{"risks": [{"title": "...", "description": "...", "category": "...", \
"severity": "low|medium|high|critical", "affected_skus": ["..."], \
"affected_shipments": ["..."]}], "narrative": "2-4 sentence overview"}
"""


async def risk_node(state: CopilotState) -> Dict[str, Any]:
    db = get_db()

    cursor = db[COLL_RISK_EVENTS].find({}, {"_id": 0}).sort("created_at", -1).limit(20)
    logged_risks: List[Dict[str, Any]] = await cursor.to_list(length=20)

    context = _build_context(state, logged_risks)

    bedrock = get_bedrock_client()
    result = await bedrock.generate_json(prompt=context, system=RISK_SYSTEM_PROMPT)

    new_risks = result.get("risks", []) if not result.get("_parse_error") else []
    narrative = result.get("narrative", _fallback_narrative(state, logged_risks))

    persisted: List[Dict[str, Any]] = []
    for r in new_risks:
        try:
            severity = RiskSeverity(r.get("severity", "medium"))
        except ValueError:
            severity = RiskSeverity.MEDIUM
        event = RiskEvent(
            title=r.get("title", "Untitled risk"),
            description=r.get("description", ""),
            category=r.get("category", "logistics"),
            severity=severity,
            affected_skus=r.get("affected_skus", []),
            affected_shipments=r.get("affected_shipments", []),
        )
        await db[COLL_RISK_EVENTS].insert_one(event.model_dump())
        persisted.append(event.model_dump(mode="json"))

    findings = [
        {
            "type": "risk_summary",
            "narrative": narrative,
            "new_risks": persisted,
            "logged_risks": logged_risks[:10],
        }
    ]

    logger.info("risk_agent.completed", new_risks=len(persisted), logged=len(logged_risks))

    remaining = [a for a in state.get("remaining_agents", []) if a != "risk"]

    return {
        "risk_findings": findings,
        "remaining_agents": remaining,
        "traces": [
            {
                "agent": "risk",
                "action": "assess_risk",
                "output_summary": f"Identified {len(persisted)} new risk(s); {len(logged_risks)} previously logged.",
            }
        ],
    }


def _build_context(state: CopilotState, logged_risks: List[Dict[str, Any]]) -> str:
    parts = [f"User question: {state['user_message']}\n"]
    for finding in state.get("inventory_findings", []):
        parts.append(f"Inventory findings: {finding.get('summary', '')}")
    for finding in state.get("shipment_findings", []):
        parts.append(f"Shipment findings: {finding.get('summary', '')}")
    for finding in state.get("knowledge_findings", []):
        parts.append(f"Knowledge findings: {finding.get('summary', '')}")
    if logged_risks:
        titles = "; ".join(r.get("title", "") for r in logged_risks[:10])
        parts.append(f"Previously logged risks: {titles}")
    return "\n".join(parts)


def _fallback_narrative(state: CopilotState, logged_risks: List[Dict[str, Any]]) -> str:
    return (
        f"Risk assessment based on {len(state.get('inventory_findings', []))} inventory finding(s), "
        f"{len(state.get('shipment_findings', []))} shipment finding(s), and "
        f"{len(logged_risks)} previously logged risk event(s)."
    )
