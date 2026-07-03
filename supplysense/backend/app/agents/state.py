"""
Shared state object passed between nodes in the LangGraph agent graph.

LangGraph nodes receive the full state dict and return a partial dict of
updates that get merged in. We use a TypedDict (rather than a Pydantic model)
because LangGraph's StateGraph merges dict updates natively and this avoids
re-validating large nested structures on every hop.
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


def _merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


class AgentTraceEntry(TypedDict):
    agent: str
    action: str
    output_summary: str


class CopilotState(TypedDict, total=False):
    # ---- input ----
    session_id: str
    user_message: str

    # ---- planning ----
    plan: List[str]
    next_agent: Optional[str]
    remaining_agents: List[str]

    # ---- working memory, additive across agent hops ----
    inventory_findings: Annotated[List[Dict[str, Any]], operator.add]
    shipment_findings: Annotated[List[Dict[str, Any]], operator.add]
    knowledge_findings: Annotated[List[Dict[str, Any]], operator.add]
    risk_findings: Annotated[List[Dict[str, Any]], operator.add]
    recommendations: Annotated[List[Dict[str, Any]], operator.add]
    traces: Annotated[List[AgentTraceEntry], operator.add]

    # ---- output ----
    final_answer: str
    report: Optional[Dict[str, Any]] = None
    iterations: int
