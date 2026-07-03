"""
Knowledge Agent.

Performs retrieval-augmented generation: embeds the user's question with
Voyage AI, retrieves the most relevant documents from MongoDB Atlas Vector
Search (SOPs, supplier contracts, customs regulations, historical incident
reports), and grounds a natural-language answer in those documents.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.state import CopilotState
from app.database import get_db
from app.services.bedrock_client import get_bedrock_client
from app.services.embeddings import KnowledgeService
from app.utils.logger import get_logger

logger = get_logger(__name__)

KNOWLEDGE_SYSTEM_PROMPT = """You are the Knowledge Agent in an AI Supply \
Chain Copilot. You are given excerpts retrieved from internal supply chain \
documents (SOPs, supplier contracts, customs rules, incident reports) via \
semantic search. Answer the user's question using ONLY the retrieved \
excerpts. If the excerpts don't contain a clear answer, say so explicitly \
rather than guessing. Cite the source title in parentheses after each claim."""


async def knowledge_node(state: CopilotState) -> Dict[str, Any]:
    db = get_db()
    user_message = state["user_message"]

    knowledge_service = KnowledgeService(db)
    results = await knowledge_service.semantic_search(user_message, top_k=5)

    bedrock = get_bedrock_client()
    context_block = _format_context(results)
    response = await bedrock.converse(
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": f"User question: {user_message}\n\nRetrieved excerpts:\n{context_block}"}
                ],
            }
        ],
        system=KNOWLEDGE_SYSTEM_PROMPT,
    )
    summary = bedrock.extract_text(response) or _fallback_summary(results)

    findings = [
        {
            "type": "knowledge_summary",
            "summary": summary,
            "sources": [{"title": r.get("title"), "source": r.get("source")} for r in results],
            "retrieved_count": len(results),
        }
    ]

    logger.info("knowledge_agent.completed", retrieved=len(results))

    remaining = [a for a in state.get("remaining_agents", []) if a != "knowledge"]

    return {
        "knowledge_findings": findings,
        "remaining_agents": remaining,
        "traces": [
            {
                "agent": "knowledge",
                "action": "semantic_search",
                "output_summary": f"Retrieved {len(results)} relevant documents via vector search.",
            }
        ],
    }


def _format_context(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No documents retrieved."
    blocks = []
    for r in results:
        content = (r.get("content") or "")[:1200]
        blocks.append(f"[{r.get('title')}] (source: {r.get('source')})\n{content}")
    return "\n\n".join(blocks)


def _fallback_summary(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "No relevant internal documents were found for this question."
    titles = ", ".join(r.get("title", "untitled") for r in results)
    return f"Found potentially relevant documents: {titles}."
