"""
FastAPI application entrypoint.

Wires together configuration, MongoDB lifecycle, CORS, and all API routers.
Run with: uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo, mongo
from app.models.schemas import HealthResponse
from app.routers import chat, inventory, knowledge, reports, shipments
from app.utils.logger import configure_logging, get_logger

settings = get_settings()
configure_logging(debug=settings.app_debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.app_env)
    try:
        await connect_to_mongo()
    except Exception as exc:  # noqa: BLE001
        logger.error("app.mongo_connect_failed", error=str(exc))
    yield
    await close_mongo_connection()
    logger.info("app.shutdown")


app = FastAPI(
    title=settings.app_name,
    description="Multi-agent AI copilot for supply chain operations — inventory, "
    "shipments, risk, and recommendations, powered by LangGraph, Amazon Bedrock, "
    "Voyage AI, and MongoDB Atlas Vector Search.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(inventory.router, prefix=settings.api_prefix)
app.include_router(shipments.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(knowledge.router, prefix=settings.api_prefix)


@app.get("/", tags=["meta"])
async def root():
    return {
        "service": settings.app_name,
        "status": "running",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    mongo_ok = False
    if mongo.client is not None:
        try:
            await mongo.client.admin.command("ping")
            mongo_ok = True
        except Exception:  # noqa: BLE001
            mongo_ok = False

    return HealthResponse(
        status="ok" if mongo_ok else "degraded",
        mongodb=mongo_ok,
        bedrock_configured=bool(settings.aws_access_key_id and settings.aws_secret_access_key),
        voyage_configured=bool(settings.voyage_api_key),
    )
