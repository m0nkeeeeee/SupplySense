"""
Pydantic schemas shared across the API layer, the agent graph, and MongoDB
serialization. Mongo documents are plain dicts at the storage layer; these
models define the contract at the API boundary and inside agent state.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def utcnow() -> datetime:
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
class InventoryItem(BaseModel):
    sku: str
    name: str
    category: str
    warehouse_id: str
    quantity_on_hand: int
    reorder_point: int
    safety_stock: int
    unit_cost: float
    lead_time_days: int
    supplier_id: Optional[str] = None
    last_updated: datetime = Field(default_factory=utcnow)

    @property
    def is_below_reorder_point(self) -> bool:
        return self.quantity_on_hand <= self.reorder_point

    @property
    def is_critical(self) -> bool:
        return self.quantity_on_hand <= self.safety_stock


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------
class ShipmentStatus(str, Enum):
    PLANNED = "planned"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    CUSTOMS_HOLD = "customs_hold"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Shipment(BaseModel):
    shipment_id: str = Field(default_factory=lambda: new_id("SHP"))
    origin: str
    destination: str
    carrier: str
    mode: str  # ocean | air | road | rail
    status: ShipmentStatus = ShipmentStatus.PLANNED
    sku_list: List[str] = Field(default_factory=list)
    eta: datetime
    etd: Optional[datetime] = None
    delay_days: int = 0
    cost_usd: float = 0.0
    risk_score: float = 0.0
    last_updated: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Suppliers
# ---------------------------------------------------------------------------
class Supplier(BaseModel):
    supplier_id: str
    name: str
    country: str
    reliability_score: float  # 0-1
    avg_lead_time_days: int
    categories: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------
class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskEvent(BaseModel):
    risk_id: str = Field(default_factory=lambda: new_id("RSK"))
    title: str
    description: str
    category: str  # geopolitical | weather | supplier | logistics | demand
    severity: RiskSeverity
    affected_skus: List[str] = Field(default_factory=list)
    affected_shipments: List[str] = Field(default_factory=list)
    region: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
class Recommendation(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: new_id("REC"))
    title: str
    rationale: str
    action_type: str  # reorder | reroute | expedite | switch_supplier | hold
    priority: str  # low | medium | high | urgent
    related_skus: List[str] = Field(default_factory=list)
    related_shipments: List[str] = Field(default_factory=list)
    estimated_impact_usd: Optional[float] = None
    created_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Knowledge documents (vector search corpus)
# ---------------------------------------------------------------------------
class KnowledgeDocument(BaseModel):
    doc_id: str = Field(default_factory=lambda: new_id("DOC"))
    title: str
    content: str
    source: str
    tags: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
class Report(BaseModel):
    report_id: str = Field(default_factory=lambda: new_id("RPT"))
    title: str
    summary: str
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    generated_by: str = "report_agent"
    created_at: datetime = Field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Chat / Agent orchestration API contracts
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class AgentTrace(BaseModel):
    agent: str
    action: str
    output_summary: str
    timestamp: datetime = Field(default_factory=utcnow)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    plan: List[str] = Field(default_factory=list)
    traces: List[AgentTrace] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    risk_events: List[RiskEvent] = Field(default_factory=list)
    citations: List[Dict[str, str]] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    mongodb: bool
    bedrock_configured: bool
    voyage_configured: bool
