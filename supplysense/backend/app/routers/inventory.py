"""Inventory router — direct CRUD and query access to inventory data,
independent of the agent graph (used by the dashboard for fast table loads)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.database import COLL_INVENTORY, get_db
from app.models.schemas import InventoryItem

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=List[InventoryItem])
async def list_inventory(
    warehouse_id: Optional[str] = Query(None),
    below_reorder_only: bool = Query(False),
    limit: int = Query(100, le=500),
):
    db = get_db()
    query: dict = {}
    if warehouse_id:
        query["warehouse_id"] = warehouse_id

    cursor = db[COLL_INVENTORY].find(query, {"_id": 0}).limit(limit)
    items = await cursor.to_list(length=limit)

    if below_reorder_only:
        items = [i for i in items if i.get("quantity_on_hand", 0) <= i.get("reorder_point", 0)]

    return items


@router.get("/{sku}", response_model=InventoryItem)
async def get_item(sku: str):
    db = get_db()
    item = await db[COLL_INVENTORY].find_one({"sku": sku}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found")
    return item


@router.post("", response_model=InventoryItem, status_code=201)
async def upsert_item(item: InventoryItem):
    db = get_db()
    item.last_updated = datetime.utcnow()
    await db[COLL_INVENTORY].update_one(
        {"sku": item.sku}, {"$set": item.model_dump()}, upsert=True
    )
    return item


@router.delete("/{sku}", status_code=204)
async def delete_item(sku: str):
    db = get_db()
    result = await db[COLL_INVENTORY].delete_one({"sku": sku})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"SKU {sku} not found")
