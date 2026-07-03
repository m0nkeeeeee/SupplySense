"""
Retrieval-augmented knowledge service.

Embeds text with Voyage AI and queries MongoDB Atlas Vector Search
($vectorSearch aggregation stage) to retrieve the most relevant supply-chain
knowledge documents (SOPs, supplier contracts, customs rules, historical
incident reports, etc.) for grounding agent responses.
"""
from __future__ import annotations

from typing import Any, Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import get_settings
from app.database import COLL_KNOWLEDGE_DOCS
from app.models.schemas import KnowledgeDocument
from app.services.voyage_client import get_voyage_client
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class KnowledgeService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self.collection = db[COLL_KNOWLEDGE_DOCS]
        self.voyage = get_voyage_client()

    async def ingest_document(self, doc: KnowledgeDocument) -> str:
        """Embed and persist a single knowledge document."""
        embedding = await self.voyage.embed_documents([doc.content])
        doc.embedding = embedding[0]
        await self.collection.insert_one(doc.model_dump())
        logger.info("knowledge.ingested", doc_id=doc.doc_id, title=doc.title)
        return doc.doc_id

    async def ingest_bulk(self, docs: List[KnowledgeDocument]) -> List[str]:
        if not docs:
            return []
        contents = [d.content for d in docs]
        embeddings = await self.voyage.embed_documents(contents)
        for doc, emb in zip(docs, embeddings):
            doc.embedding = emb
        await self.collection.insert_many([d.model_dump() for d in docs])
        logger.info("knowledge.bulk_ingested", count=len(docs))
        return [d.doc_id for d in docs]

    async def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Runs a $vectorSearch query against Atlas. Requires a vector search
        index (see scripts/create_vector_index.py) named per settings."""
        query_vector = await self.voyage.embed_query(query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": settings.mongodb_vector_index,
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": max(top_k * 10, 50),
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "doc_id": 1,
                    "title": 1,
                    "content": 1,
                    "source": 1,
                    "tags": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        try:
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=top_k)
        except Exception as exc:  # noqa: BLE001
            logger.warning("knowledge.vector_search_failed_fallback_text", error=str(exc))
            return await self._fallback_text_search(query, top_k)

    async def _fallback_text_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Naive fallback if the Atlas Vector Search index isn't provisioned
        yet (e.g. fresh local Mongo instance during development)."""
        regex = {"$regex": query, "$options": "i"}
        cursor = self.collection.find(
            {"$or": [{"title": regex}, {"content": regex}, {"tags": regex}]},
            {"_id": 0, "embedding": 0},
        ).limit(top_k)
        return await cursor.to_list(length=top_k)
