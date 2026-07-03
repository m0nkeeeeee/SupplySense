"""Shipments router — direct CRUD and query access to shipment tracking data."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import COLL_SHIPMENTS, get_db
from app.models.schemas import Shipment, ShipmentStatus

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=List[Shipment])
async def list_shipments(
    status: Optional[ShipmentStatus] = Query(None),
    destination: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    db = get_db()
    query: dict = {}
    if status:
        query["status"] = status.value
    if destination:
        query["destination"] = destination

    cursor = db[COLL_SHIPMENTS].find(query, {"_id": 0}).limit(limit)
    return await cursor.to_list(length=limit)


@router.get("/{shipment_id}", response_model=Shipment)
async def get_shipment(shipment_id: str):
    db = get_db()
    shipment = await db[COLL_SHIPMENTS].find_one({"shipment_id": shipment_id}, {"_id": 0})
    if not shipment:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")
    return shipment


@router.post("", response_model=Shipment, status_code=201)
async def upsert_shipment(shipment: Shipment):
    db = get_db()
    shipment.last_updated = datetime.utcnow()
    await db[COLL_SHIPMENTS].update_one(
        {"shipment_id": shipment.shipment_id}, {"$set": shipment.model_dump()}, upsert=True
    )
    return shipment


@router.delete("/{shipment_id}", status_code=204)
async def delete_shipment(shipment_id: str):
    db = get_db()
    result = await db[COLL_SHIPMENTS].delete_one({"shipment_id": shipment_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Shipment {shipment_id} not found")
