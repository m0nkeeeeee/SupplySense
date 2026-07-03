"""
Creates the MongoDB Atlas Vector Search index required by the Knowledge
Agent. Atlas Search/Vector Search indexes cannot be created through the
standard `create_index` driver call — they go through the Atlas Search
index management API, exposed in PyMongo/Motor as `create_search_index`
(available on Atlas clusters running MongoDB 7.0+ / Atlas Search-enabled
tiers).

Run with: python -m scripts.create_vector_index (from backend/).
"""
from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import SearchIndexModel

from app.config import get_settings
from app.database import COLL_KNOWLEDGE_DOCS

settings = get_settings()


async def create_vector_index() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]
    collection = db[COLL_KNOWLEDGE_DOCS]

    index_model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": settings.mongodb_vector_dimensions,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "tags"},
                {"type": "filter", "path": "source"},
            ]
        },
        name=settings.mongodb_vector_index,
        type="vectorSearch",
    )

    try:
        result = await collection.create_search_index(index_model)
        print(f"Vector search index creation requested: {result}")
        print(
            "Note: Atlas Search indexes build asynchronously. Check the Atlas UI "
            "(Search tab) or `db.collection.listSearchIndexes()` until status is READY "
            "before relying on $vectorSearch queries."
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Index creation failed (it may already exist, or this cluster tier may "
              f"not support Atlas Vector Search): {exc}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_vector_index())
