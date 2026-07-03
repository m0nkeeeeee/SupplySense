"""
Recommendation Agent.

Synthesizes everything gathered by upstream agents (inventory, shipment,
knowledge, risk) into a prioritized list of concrete action items, persists
them to MongoDB, and produces the user-facing final answer.
"""
from __future__ import annotations

from typing import Any, Dict, List
import json
import re

from app.agents.state import CopilotState
from app.database import COLL_RECOMMENDATIONS, get_db
from app.models.schemas import Recommendation
from app.services.bedrock_client import get_bedrock_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

RECOMMENDATION_SYSTEM_PROMPT = """You are the Recommendation Agent in an AI \
Supply Chain Copilot — the final synthesis step the user actually reads. \
You receive findings already gathered by other specialist agents (inventory, \
shipment, knowledge, risk). Your job:
1. Write a direct, well-organized answer to the user's original question.
2. Propose concrete, prioritized recommendations (action_type one of: \
reorder, reroute, expedite, switch_supplier, hold).

Ground every claim in the provided findings. Do not fabricate numbers. If \
findings are sparse, say so plainly rather than inventing detail.

Respond with ONLY JSON in this exact shape:
{"answer": "full markdown-formatted answer to the user", \
"recommendations": [{"title": "...", "rationale": "...", \
"action_type": "reorder|reroute|expedite|switch_supplier|hold", \
"priority": "low|medium|high|urgent", "related_skus": ["..."], \
"related_shipments": ["..."], "estimated_impact_usd": null}]}
"""


async def recommendation_node(state: CopilotState) -> Dict[str, Any]:
    db = get_db()
    context = _build_context(state)

    bedrock = get_bedrock_client()
    result = await bedrock.generate_json(prompt=context, system=RECOMMENDATION_SYSTEM_PROMPT)
    parse_error = bool(result.get("_parse_error"))
    raw_recs: List[Any] = []
    if parse_error:
        logger.warning("recommendation_agent.parse_error", detail="Bedrock JSON parse failed")
        raw_text = result.get("_raw", "")
        formatted_answer, candidate_recs = _format_raw_model_output(raw_text, state)
        final_answer = formatted_answer or _fallback_answer(state)
        raw_recs = candidate_recs if isinstance(candidate_recs, list) else []
    else:
        final_answer = (result.get("answer") or _fallback_answer(state)).strip()
        raw_recs = result.get("recommendations", [])

    persisted: List[Dict[str, Any]] = []
    for r in raw_recs:
        if not isinstance(r, dict):
            logger.warning("recommendation_agent.invalid_rec_skipped", rec=repr(r))
            continue
        try:
            rec = Recommendation(
                title=r.get("title", "Recommendation"),
                rationale=r.get("rationale", ""),
                action_type=r.get("action_type", "hold"),
                priority=r.get("priority", "medium"),
                related_skus=r.get("related_skus", []),
                related_shipments=r.get("related_shipments", []),
                estimated_impact_usd=r.get("estimated_impact_usd"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("recommendation_agent.invalid_rec_error", error=str(exc), rec=repr(r))
            continue
        await db[COLL_RECOMMENDATIONS].insert_one(rec.model_dump())
        persisted.append(rec.model_dump(mode="json"))

    logger.info("recommendation_agent.completed", count=len(persisted), parse_error=parse_error)
    # If inventory findings are present, produce a deterministic Markdown
    # summary to ensure neat, consistent formatting for users.
    inventory_findings = state.get("inventory_findings", [])
    if inventory_findings:
        final_answer = _format_inventory_findings_markdown(inventory_findings[0])

    remaining = [a for a in state.get("remaining_agents", []) if a != "recommendation"]

    return {
        "recommendations": persisted,
        "final_answer": final_answer,
        "remaining_agents": remaining,
        "traces": [
            {
                "agent": "recommendation",
                "action": "synthesize_recommendations",
                "output_summary": f"Produced {len(persisted)} prioritized recommendation(s) and final answer.",
            }
        ],
    }


def _ensure_professional_format(text: str, state: CopilotState) -> str:
    """Convert a plain or lightly-structured answer into a professional Markdown summary.

    Uses simple heuristics to extract counts and SKU lists for clearer presentation.
    """
    if not text:
        return _fallback_answer(state)

    # If already looks like Markdown with headings, return as-is
    if text.strip().startswith("**") or text.strip().startswith("#") or "**Recommendations**" in text:
        return text

    cleaned = text.strip()

    # Extract total SKUs
    total_match = re.search(r"(\d+)\s+total\s+SKUs", cleaned, re.I)
    total = total_match.group(1) if total_match else None

    # Extract list after 'including'
    incl_match = re.search(r"including\s+([^\.]+)", cleaned, re.I)
    below_list = []
    if incl_match:
        raw = incl_match.group(1)
        # split on commas and ' and '
        items = re.split(r",\s*|\s+and\s+", raw)
        below_list = [i.strip().strip('.') for i in items if i.strip()]

    # Extract safety-stock-critical items
    safety_match = re.search(r"below their safety stock levels[,\s]*(.*?)\.|below their safety stock levels\s*(.*)$", cleaned, re.I)
    safety_list = []
    if safety_match:
        candidate = safety_match.group(1) or safety_match.group(2) or ""
        items = re.split(r",\s*|\s+and\s+", candidate)
        safety_list = [i.strip().strip('.') for i in items if i.strip()]

    # Build professional Markdown
    parts: List[str] = []
    parts.append("**Summary**")
    # Use first sentence as summary
    first_sentence = cleaned.split(".")[0].strip()
    if first_sentence:
        parts.append(first_sentence + ".")

    parts.append("\n**Key Metrics**")
    if total:
        parts.append(f"- Total SKUs tracked: {total}")
    if below_list:
        parts.append(f"- SKUs below reorder point: {len(below_list)}")
        for sku in below_list:
            parts.append(f"  - {sku}")
    if safety_list:
        parts.append(f"- SKUs below safety stock (critical): {len(safety_list)}")
        for sku in safety_list:
            parts.append(f"  - {sku}")

    parts.append("\n**Recommended Actions**")
    if safety_list:
        parts.append(f"- Prioritize immediate replenishment for: {', '.join(safety_list)}.")
        parts.append("- Notify Procurement to expedite orders and confirm lead times.")
    elif below_list:
        parts.append("- Replenish the SKUs listed above according to standard reorder policies.")
    else:
        parts.append("- No critical stock issues were detected based on the provided findings.")

    parts.append("\n**Notes**")
    parts.append("- Review supplier lead times and consider safety stock adjustments for items with repeated shortfalls.")

    return "\n\n".join(parts)


def _format_inventory_findings_markdown(finding: Dict[str, Any]) -> str:
    """Format inventory findings into a neat, professional Markdown summary.

    `finding` is expected to include keys produced by `inventory_agent`:
    - summary, total_skus, below_reorder_count, critical_count,
      below_reorder_skus, critical_skus
    """
    summary = finding.get("summary", "")
    total = finding.get("total_skus")
    below_count = finding.get("below_reorder_count")
    critical_count = finding.get("critical_count")
    below_skus = finding.get("below_reorder_skus", [])
    critical_skus = finding.get("critical_skus", [])

    parts: List[str] = []
    parts.append("**Summary**")
    if summary:
        parts.append(summary.strip())

    parts.append("\n**Key Metrics**")
    if total is not None:
        parts.append(f"- Total SKUs tracked: {total}")
    if below_count is not None:
        parts.append(f"- SKUs below reorder point: {below_count}")

    # Present SKUs, marking critical ones
    if below_skus:
        parts.append("\n**SKUs below reorder point**")
        for sku in below_skus:
            # Try to see if the summary contains a name for this sku: "SKU-0001 (Name)"
            name_match = None
            name_search = re.search(rf"{re.escape(sku)}\s*\(([^)]+)\)", summary)
            if name_search:
                name_match = name_search.group(1).strip()
            display = f"{sku} — {name_match}" if name_match else sku
            if sku in critical_skus:
                parts.append(f"- {display} (CRITICAL: below safety stock)")
            else:
                parts.append(f"- {display}")

    if critical_skus and not below_skus:
        # If critical SKUs exist but below_skus not provided, list critical separately
        parts.append("\n**SKUs below safety stock (critical)**")
        for sku in critical_skus:
            name_search = re.search(rf"{re.escape(sku)}\s*\(([^)]+)\)", summary)
            name = name_search.group(1).strip() if name_search else sku
            parts.append(f"- {sku} — {name}")

    parts.append("\n**Recommended actions**")
    if critical_skus:
        parts.append(f"- Prioritize immediate replenishment for: {', '.join(critical_skus)}.")
        parts.append("- Notify Procurement to expedite orders and confirm lead times.")
    elif below_skus:
        parts.append("- Replenish the SKUs above according to standard reorder policies.")
    else:
        parts.append("- No immediate replenishment actions detected.")

    parts.append("\n**Notes**")
    parts.append("- Review supplier lead times and consider safety stock adjustments for repeatedly shortfalling SKUs.")

    return "\n\n".join(parts)


def _format_raw_model_output(raw: str, state: CopilotState) -> tuple[str, List[Any]]:
    """Try to turn raw model text into a professional, user-friendly answer.

    Returns a tuple of (formatted_text, candidate_recommendations_list).
    """
    if not raw:
        return "", []

    # Strip Markdown fences and leading/trailing whitespace
    cleaned = re.sub(r"^```(?:json)?\\n|```$", "", raw.strip())

    # Try to parse as JSON first
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            answer = parsed.get("answer") or parsed.get("_raw") or ""
            recs = parsed.get("recommendations", [])
            formatted = answer.strip() if isinstance(answer, str) else json.dumps(answer)
            # If there are structured recommendations, format them into Markdown
            if recs and isinstance(recs, list):
                lines = [formatted, "\n**Recommendations:**"]
                for r in recs:
                    if isinstance(r, dict):
                        title = r.get("title", "Recommendation")
                        rationale = r.get("rationale", "")
                        lines.append(f"- **{title}**: {rationale}")
                    else:
                        lines.append(f"- {repr(r)}")
                formatted = "\n\n".join(lines)
            return formatted, recs
    except Exception:
        # Not JSON — fall through
        pass

    # Attempt to extract JSON substring if model wrapped JSON inside text
    json_match = re.search(r"(\{[\s\S]*\})", cleaned)
    if json_match:
        candidate = json_match.group(1)
        try:
            parsed = json.loads(candidate)
            answer = parsed.get("answer") or ""
            return (answer.strip() if isinstance(answer, str) else json.dumps(answer)), parsed.get("recommendations", [])
        except Exception:
            pass

    # As a last resort, return the cleaned raw text as a professional paragraph
    # Remove stray braces and excessive newlines
    text = re.sub(r"\{\s*\}\s*", "", cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    # If the text looks like JSON (starts with {) but couldn't be parsed, try to extract an "answer" field via regex
    m = re.search(r'"answer"\s*:\s*"([\s\S]*?)"\s*(,|})', text)
    if m:
        ans = m.group(1)
        ans = ans.replace('\\n', '\n')
        return ans.strip(), []

    return text, []


def _build_context(state: CopilotState) -> str:
    parts = [f"Original user question: {state['user_message']}\n"]

    for finding in state.get("inventory_findings", []):
        parts.append(f"INVENTORY FINDINGS:\n{finding.get('summary', '')}")
    for finding in state.get("shipment_findings", []):
        parts.append(f"SHIPMENT FINDINGS:\n{finding.get('summary', '')}")
    for finding in state.get("knowledge_findings", []):
        parts.append(f"KNOWLEDGE FINDINGS:\n{finding.get('summary', '')}")
    for finding in state.get("risk_findings", []):
        parts.append(f"RISK FINDINGS:\n{finding.get('narrative', '')}")
        new_risks = finding.get("new_risks", [])
        if new_risks:
            titles = "; ".join(f"{r['title']} ({r['severity']})" for r in new_risks)
            parts.append(f"Newly identified risks: {titles}")

    if len(parts) == 1:
        parts.append("No upstream findings were gathered; answer using general supply chain best practice and note the data gap.")

    return "\n\n".join(parts)


def _fallback_answer(state: CopilotState) -> str:
    parts: List[str] = []
    parts.append("**Summary of Findings**")

    inv = state.get("inventory_findings", [])
    if inv:
        parts.append("- Inventory findings:")
        for f in inv:
            summary = f.get("summary", "(no summary)")
            parts.append(f"  - {summary}")

    ship = state.get("shipment_findings", [])
    if ship:
        parts.append("- Shipment findings:")
        for f in ship:
            summary = f.get("summary", "(no summary)")
            parts.append(f"  - {summary}")

    know = state.get("knowledge_findings", [])
    if know:
        parts.append("- Knowledge findings:")
        for f in know:
            summary = f.get("summary", "(no summary)")
            parts.append(f"  - {summary}")

    risk = state.get("risk_findings", [])
    if risk:
        parts.append("- Risk findings:")
        for f in risk:
            narrative = f.get("narrative", "(no narrative)")
            parts.append(f"  - {narrative}")

    if len(parts) == 1:
        parts.append("No upstream findings were gathered. I couldn't assemble a confident answer from available data.")

    parts.append("\n**Recommendations**")
    parts.append("- No automated recommendations could be generated. Ensure data sources are populated and try again, or ask for a manual review.")

    parts.append("\nIf you need this as a formal report, ask: 'generate report' and include any additional constraints.")

    return "\n\n".join(parts)
