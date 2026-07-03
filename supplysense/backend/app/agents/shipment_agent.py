"""
Shipment Agent.

Reads shipment tracking data from MongoDB and surfaces delays, in-transit
risk, and ETA information relevant to the user's question.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.agents.state import CopilotState
from app.database import COLL_SHIPMENTS, get_db
from app.services.bedrock_client import get_bedrock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

SHIPMENT_SYSTEM_PROMPT = """You are the Shipment Agent in an AI Supply \
Chain Copilot. You are given live shipment tracking records (origin, \
destination, carrier, mode, status, ETA, delay days). Write a concise, \
specific summary (3-6 sentences) of shipment status relevant to the user's \
question. Call out delayed or at-risk shipments by shipment_id. Do not \
invent data not present in the records."""


async def shipment_node(state: CopilotState) -> Dict[str, Any]:
    db = get_db()
    user_message = state["user_message"]

    cursor = db[COLL_SHIPMENTS].find({}, {"_id": 0}).limit(200)
    shipments: List[Dict[str, Any]] = await cursor.to_list(length=200)

    delayed = [s for s in shipments if s.get("status") in ("delayed", "customs_hold") or s.get("delay_days", 0) > 0]
    in_transit = [s for s in shipments if s.get("status") == "in_transit"]

    bedrock = get_bedrock_client()
    response = await bedrock.converse(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"User question: {user_message}\n\n"
                            f"Total shipments tracked: {len(shipments)}\n"
                            f"In transit: {len(in_transit)}\n"
                            f"Delayed / on hold ({len(delayed)}): {_summarize_shipments(delayed)}\n"
                        )
                    }
                ],
            }
        ],
        system=SHIPMENT_SYSTEM_PROMPT,
    )
    summary = bedrock.extract_text(response) or _fallback_summary(shipments, delayed)

    findings = [
        {
            "type": "shipment_summary",
            "summary": summary,
            "total_shipments": len(shipments),
            "in_transit_count": len(in_transit),
            "delayed_count": len(delayed),
            "delayed_shipment_ids": [s["shipment_id"] for s in delayed][:25],
        }
    ]

    logger.info("shipment_agent.completed", total=len(shipments), delayed=len(delayed))

    remaining = [a for a in state.get("remaining_agents", []) if a != "shipment"]

    return {
        "shipment_findings": findings,
        "remaining_agents": remaining,
        "traces": [
            {
                "agent": "shipment",
                "action": "analyze_shipments",
                "output_summary": (
                    f"Scanned {len(shipments)} shipments; {len(delayed)} delayed or on hold."
                ),
            }
        ],
    }


def _summarize_shipments(shipments: List[Dict[str, Any]], limit: int = 15) -> str:
    if not shipments:
        return "none"
    parts = []
    for s in shipments[:limit]:
        eta = s.get("eta")
        eta_str = eta.isoformat() if isinstance(eta, datetime) else str(eta)
        parts.append(
            f"{s['shipment_id']} ({s.get('origin')}->{s.get('destination')}, "
            f"carrier={s.get('carrier')}, status={s.get('status')}, "
            f"delay_days={s.get('delay_days', 0)}, eta={eta_str})"
        )
    suffix = f" ...and {len(shipments) - limit} more" if len(shipments) > limit else ""
    return "; ".join(parts) + suffix


def _fallback_summary(shipments, delayed) -> str:
    if not shipments:
        return "No shipment records found in the database."
    return (
        f"Tracking {len(shipments)} shipments; {len(delayed)} are currently delayed or held at customs."
    )
