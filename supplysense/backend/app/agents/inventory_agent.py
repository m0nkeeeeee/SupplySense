"""
Inventory Agent.

Reads live inventory data from MongoDB, identifies SKUs at or below reorder
point / safety stock, and produces structured findings for downstream agents
(Risk, Recommendation, Report) plus a natural-language summary for the user.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.state import CopilotState
from app.database import COLL_INVENTORY, get_db
from app.services.bedrock_client import get_bedrock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

INVENTORY_SYSTEM_PROMPT = """You are the Inventory Agent in an AI Supply \
Chain Copilot. You are given raw inventory records (SKU, warehouse, \
quantity on hand, reorder point, safety stock, lead time). Write a concise, \
specific, decision-useful summary (3-6 sentences) of the inventory \
situation relevant to the user's question. Call out SKUs that are below \
reorder point or safety stock by name. Do not invent data not present in \
the records."""


async def inventory_node(state: CopilotState) -> Dict[str, Any]:
    db = get_db()
    user_message = state["user_message"]

    cursor = db[COLL_INVENTORY].find({}, {"_id": 0}).limit(200)
    items: List[Dict[str, Any]] = await cursor.to_list(length=200)

    below_reorder = [i for i in items if i.get("quantity_on_hand", 0) <= i.get("reorder_point", 0)]
    critical = [i for i in items if i.get("quantity_on_hand", 0) <= i.get("safety_stock", 0)]

    bedrock = get_bedrock_client()
    response = await bedrock.converse(
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"User question: {user_message}\n\n"
                            f"Total SKUs tracked: {len(items)}\n"
                            f"Below reorder point ({len(below_reorder)}): {_summarize_items(below_reorder)}\n"
                            f"Critical / below safety stock ({len(critical)}): {_summarize_items(critical)}\n"
                        )
                    }
                ],
            }
        ],
        system=INVENTORY_SYSTEM_PROMPT,
    )
    summary = bedrock.extract_text(response) or _fallback_summary(items, below_reorder, critical)

    findings = [
        {
            "type": "inventory_summary",
            "summary": summary,
            "total_skus": len(items),
            "below_reorder_count": len(below_reorder),
            "critical_count": len(critical),
            "below_reorder_skus": [i["sku"] for i in below_reorder][:25],
            "critical_skus": [i["sku"] for i in critical][:25],
        }
    ]

    logger.info("inventory_agent.completed", total=len(items), critical=len(critical))

    remaining = [a for a in state.get("remaining_agents", []) if a != "inventory"]

    return {
        "inventory_findings": findings,
        "remaining_agents": remaining,
        "traces": [
            {
                "agent": "inventory",
                "action": "analyze_stock_levels",
                "output_summary": (
                    f"Scanned {len(items)} SKUs; {len(below_reorder)} below reorder point, "
                    f"{len(critical)} critical."
                ),
            }
        ],
    }


def _summarize_items(items: List[Dict[str, Any]], limit: int = 15) -> str:
    if not items:
        return "none"
    parts = [
        f"{i['sku']} ({i.get('name', '')}, qty={i.get('quantity_on_hand')}, "
        f"reorder_pt={i.get('reorder_point')}, safety_stock={i.get('safety_stock')}, "
        f"warehouse={i.get('warehouse_id')})"
        for i in items[:limit]
    ]
    suffix = f" ...and {len(items) - limit} more" if len(items) > limit else ""
    return "; ".join(parts) + suffix


def _fallback_summary(items, below_reorder, critical) -> str:
    if not items:
        return "No inventory records found in the database."
    return (
        f"Tracking {len(items)} SKUs. {len(below_reorder)} are at or below their reorder point, "
        f"of which {len(critical)} are at or below safety stock and require urgent replenishment."
    )
