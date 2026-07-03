"""
Voyage AI embeddings client.

Used by the Knowledge Agent to embed documents at ingestion time and embed
queries at retrieval time for MongoDB Atlas Vector Search.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional

import voyageai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class VoyageEmbeddingClient:
    def __init__(self) -> None:
        self._client = voyageai.Client(api_key=settings.voyage_api_key)
        self.model = settings.voyage_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _embed_sync(self, texts: List[str], input_type: str) -> List[List[float]]:
        result = self._client.embed(texts, model=self.model, input_type=input_type)
        return result.embeddings

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self._embed_sync(texts, settings.voyage_input_type_document)
        )

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None, lambda: self._embed_sync([text], settings.voyage_input_type_query)
        )
        return vectors[0]


_voyage_client: Optional[VoyageEmbeddingClient] = None


def get_voyage_client() -> VoyageEmbeddingClient:
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = VoyageEmbeddingClient()
    return _voyage_client
