"""Knowledge router — ingest and search the vector-backed knowledge base
used by the Knowledge Agent."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query

from app.database import get_db
from app.models.schemas import KnowledgeDocument
from app.services.embeddings import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/ingest", status_code=201)
async def ingest_document(doc: KnowledgeDocument):
    db = get_db()
    service = KnowledgeService(db)
    doc_id = await service.ingest_document(doc)
    return {"doc_id": doc_id, "status": "ingested"}


@router.post("/ingest/bulk", status_code=201)
async def ingest_bulk(docs: List[KnowledgeDocument]):
    db = get_db()
    service = KnowledgeService(db)
    doc_ids = await service.ingest_bulk(docs)
    return {"doc_ids": doc_ids, "count": len(doc_ids)}


@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=2), top_k: int = Query(5, le=20)):
    db = get_db()
    service = KnowledgeService(db)
    results = await service.semantic_search(q, top_k=top_k)
    return {"query": q, "results": results}
