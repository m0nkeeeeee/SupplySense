"""
MongoDB Atlas connection management using Motor (async PyMongo driver).

Exposes a single AsyncIOMotorClient for the app's lifetime and convenience
accessors for each collection used by the system, including the Knowledge
Agent's vector-search collection.
"""
from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

settings = get_settings()


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongo = MongoDB()


# Collection name constants — single source of truth used everywhere.
COLL_INVENTORY = "inventory"
COLL_SHIPMENTS = "shipments"
COLL_SUPPLIERS = "suppliers"
COLL_RISK_EVENTS = "risk_events"
COLL_KNOWLEDGE_DOCS = "knowledge_documents"
COLL_RECOMMENDATIONS = "recommendations"
COLL_REPORTS = "reports"
COLL_CHAT_SESSIONS = "chat_sessions"
COLL_AGENT_RUNS = "agent_runs"


async def connect_to_mongo() -> None:
    logger.info("mongo.connecting", uri_host=settings.mongodb_uri.split("@")[-1])
    mongo.client = AsyncIOMotorClient(settings.mongodb_uri, uuidRepresentation="standard")
    mongo.db = mongo.client[settings.mongodb_db_name]
    # Fail fast if the cluster is unreachable.
    await mongo.client.admin.command("ping")
    await ensure_indexes(mongo.db)
    logger.info("mongo.connected", db=settings.mongodb_db_name)


async def close_mongo_connection() -> None:
    if mongo.client:
        mongo.client.close()
        logger.info("mongo.connection_closed")


def get_db() -> AsyncIOMotorDatabase:
    if mongo.db is None:
        raise RuntimeError("MongoDB has not been initialized. Call connect_to_mongo() first.")
    return mongo.db


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create standard (non-vector) indexes. Vector search indexes must be
    created via Atlas Search (see scripts/create_vector_index.py) since the
    driver cannot create Atlas Search indexes directly on all tiers."""
    await db[COLL_INVENTORY].create_index("sku", unique=True)
    await db[COLL_INVENTORY].create_index("warehouse_id")
    await db[COLL_SHIPMENTS].create_index("shipment_id", unique=True)
    await db[COLL_SHIPMENTS].create_index("status")
    await db[COLL_SHIPMENTS].create_index("destination")
    await db[COLL_SUPPLIERS].create_index("supplier_id", unique=True)
    await db[COLL_RISK_EVENTS].create_index([("created_at", -1)])
    await db[COLL_RECOMMENDATIONS].create_index([("created_at", -1)])
    await db[COLL_REPORTS].create_index([("created_at", -1)])
    await db[COLL_CHAT_SESSIONS].create_index("session_id", unique=True)
    await db[COLL_AGENT_RUNS].create_index([("created_at", -1)])
    logger.info("mongo.indexes_ensured")
