"""
Chat router — the primary entrypoint into the multi-agent copilot.

POST /chat accepts a natural-language supply chain question, runs it through
the full LangGraph agent graph (Planner -> specialist agents -> Recommendation
-> optional Report), persists the conversation turn, and returns a structured
response including the plan, agent traces, recommendations, and risk events.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.agents.graph import run_copilot_graph
from app.database import COLL_CHAT_SESSIONS, get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    session_id = request.session_id or f"SESSION-{uuid.uuid4().hex[:10]}"
    db = get_db()

    try:
        result = await run_copilot_graph(session_id, request.message)
    except Exception as exc:  # noqa: BLE001
        logger.error("chat.graph_failed", error=str(exc), session_id=session_id)
        raise HTTPException(status_code=502, detail=f"Agent graph execution failed: {exc}") from exc

    risk_events = []
    for finding in result.get("risk_findings", []):
        risk_events.extend(finding.get("new_risks", []))

    response = ChatResponse(
        session_id=session_id,
        answer=result.get("final_answer", "") or "No answer was generated.",
        plan=result.get("plan", []),
        traces=result.get("traces", []),
        recommendations=result.get("recommendations", []),
        risk_events=risk_events,
        citations=[
            src
            for finding in result.get("knowledge_findings", [])
            for src in finding.get("sources", [])
        ],
    )

    await db[COLL_CHAT_SESSIONS].update_one(
        {"session_id": session_id},
        {
            "$push": {
                "turns": {
                    "user_message": request.message,
                    "answer": response.answer,
                    "plan": response.plan,
                    "timestamp": datetime.utcnow(),
                }
            },
            "$setOnInsert": {"session_id": session_id, "created_at": datetime.utcnow()},
        },
        upsert=True,
    )

    return response


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    db = get_db()
    session = await db[COLL_CHAT_SESSIONS].find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
