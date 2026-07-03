"""
Seeds MongoDB Atlas with realistic demo data: inventory, shipments,
suppliers, risk events, and a small knowledge base (auto-embedded via
Voyage AI). Run with: python -m scripts.seed_data (from backend/).
"""
from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.database import (
    COLL_INVENTORY,
    COLL_RISK_EVENTS,
    COLL_SHIPMENTS,
    COLL_SUPPLIERS,
    ensure_indexes,
)
from app.models.schemas import (
    InventoryItem,
    KnowledgeDocument,
    RiskEvent,
    RiskSeverity,
    Shipment,
    ShipmentStatus,
    Supplier,
)
from app.services.embeddings import KnowledgeService

settings = get_settings()

WAREHOUSES = ["WH-EAST", "WH-WEST", "WH-CENTRAL", "WH-EU"]
CATEGORIES = ["Electronics", "Packaging", "Raw Materials", "Apparel", "Industrial Parts"]
CARRIERS = ["Maersk", "DHL Global", "FedEx Freight", "DB Schenker", "CMA CGM"]
MODES = ["ocean", "air", "road", "rail"]
COUNTRIES = ["China", "Vietnam", "Germany", "Mexico", "India", "USA"]


def make_suppliers() -> list[Supplier]:
    return [
        Supplier(
            supplier_id=f"SUP-{i:03d}",
            name=name,
            country=country,
            reliability_score=round(random.uniform(0.6, 0.99), 2),
            avg_lead_time_days=random.randint(7, 45),
            categories=random.sample(CATEGORIES, k=random.randint(1, 3)),
        )
        for i, (name, country) in enumerate(
            [
                ("Pacific Components Ltd", "China"),
                ("NordTech Industrial", "Germany"),
                ("Saigon Textiles Co", "Vietnam"),
                ("Azteca Manufacturing", "Mexico"),
                ("Bharat Precision Parts", "India"),
                ("Liberty Domestic Supply", "USA"),
            ],
            start=1,
        )
    ]


def make_inventory(suppliers: list[Supplier]) -> list[InventoryItem]:
    items = []
    product_names = [
        "USB-C Connector", "Lithium Battery Cell", "Corrugated Box (M)", "Steel Bracket",
        "Cotton Fabric Roll", "Microcontroller Board", "Rubber Gasket", "Aluminum Housing",
        "LED Display Panel", "Shipping Pallet", "Wiring Harness", "Plastic Resin Pellets",
        "Industrial Bearing", "Safety Gloves (Box)", "Circuit Breaker", "Glass Vial",
        "Foam Padding Sheet", "Stainless Bolt Set", "Power Adapter", "Touchscreen Module",
    ]
    for i, name in enumerate(product_names, start=1):
        supplier = random.choice(suppliers)
        reorder = random.randint(50, 300)
        safety = int(reorder * 0.4)
        # Bias ~30% of items toward being below reorder point for a realistic demo
        qty = random.randint(0, int(reorder * 0.9)) if random.random() < 0.3 else random.randint(reorder, reorder * 5)
        items.append(
            InventoryItem(
                sku=f"SKU-{i:04d}",
                name=name,
                category=random.choice(CATEGORIES),
                warehouse_id=random.choice(WAREHOUSES),
                quantity_on_hand=qty,
                reorder_point=reorder,
                safety_stock=safety,
                unit_cost=round(random.uniform(0.5, 250.0), 2),
                lead_time_days=supplier.avg_lead_time_days,
                supplier_id=supplier.supplier_id,
            )
        )
    return items


def make_shipments(inventory: list[InventoryItem]) -> list[Shipment]:
    shipments = []
    destinations = ["Los Angeles, US", "Rotterdam, NL", "New York, US", "Hamburg, DE", "Chicago, US"]
    origins = ["Shenzhen, CN", "Ho Chi Minh City, VN", "Hamburg, DE", "Mumbai, IN", "Mexico City, MX"]

    for i in range(1, 26):
        status = random.choices(
            [s.value for s in ShipmentStatus],
            weights=[15, 35, 20, 10, 15, 5],
        )[0]
        delay = random.randint(1, 12) if status in ("delayed", "customs_hold") else 0
        etd = datetime.utcnow() - timedelta(days=random.randint(1, 20))
        eta = etd + timedelta(days=random.randint(5, 35)) + timedelta(days=delay)
        skus = random.sample([item.sku for item in inventory], k=random.randint(1, 4))
        shipments.append(
            Shipment(
                shipment_id=f"SHP-{i:04d}",
                origin=random.choice(origins),
                destination=random.choice(destinations),
                carrier=random.choice(CARRIERS),
                mode=random.choice(MODES),
                status=status,
                sku_list=skus,
                etd=etd,
                eta=eta,
                delay_days=delay,
                cost_usd=round(random.uniform(800, 45000), 2),
                risk_score=round(random.uniform(0.05, 0.95), 2),
            )
        )
    return shipments


def make_risk_events() -> list[RiskEvent]:
    return [
        RiskEvent(
            title="Red Sea shipping lane disruption",
            description="Ongoing rerouting around the Cape of Good Hope is adding 10-14 days "
            "to ocean freight transit times for Asia-Europe lanes.",
            category="geopolitical",
            severity=RiskSeverity.HIGH,
            region="Red Sea / Suez",
        ),
        RiskEvent(
            title="Typhoon season impacting Vietnam ports",
            description="Seasonal typhoon activity is forecast to disrupt port operations in "
            "Ho Chi Minh City for 3-5 days in the coming weeks.",
            category="weather",
            severity=RiskSeverity.MEDIUM,
            region="Vietnam",
        ),
        RiskEvent(
            title="Key connector supplier reliability decline",
            description="Pacific Components Ltd has missed its committed lead time on the last "
            "three purchase orders, trending toward a reliability downgrade.",
            category="supplier",
            severity=RiskSeverity.MEDIUM,
            region="China",
        ),
    ]


def make_knowledge_documents() -> list[KnowledgeDocument]:
    return [
        KnowledgeDocument(
            title="Standard Reorder Policy — Electronics Category",
            content=(
                "For SKUs in the Electronics category, initiate a reorder when quantity on hand "
                "reaches the reorder point. Standard reorder quantity is the greater of (a) 60 "
                "days of average demand, or (b) the supplier's minimum order quantity. Expedited "
                "air freight should only be used when projected stockout date is within the "
                "supplier's standard lead time, since air freight costs roughly 4-6x ocean freight "
                "for comparable volumes."
            ),
            source="internal_policy",
            tags=["inventory", "reorder", "electronics", "policy"],
        ),
        KnowledgeDocument(
            title="Customs Clearance SOP — US Imports",
            content=(
                "All shipments entering US ports must have a complete commercial invoice, packing "
                "list, and (where applicable) certificate of origin filed at least 48 hours before "
                "vessel arrival. Customs holds are most commonly triggered by HS code mismatches "
                "or missing certificates of origin for preferential tariff treatment. Average "
                "customs hold resolution time is 2-4 business days once documentation is corrected."
            ),
            source="internal_policy",
            tags=["customs", "compliance", "shipments", "imports"],
        ),
        KnowledgeDocument(
            title="Supplier Switching Protocol",
            content=(
                "Before switching primary suppliers for any SKU, Procurement must confirm: (1) "
                "the alternate supplier's reliability score is at or above 0.85, (2) sample "
                "quality approval has been documented within the last 12 months, and (3) the "
                "alternate supplier's lead time does not exceed the current supplier's by more "
                "than 20%. Emergency switches for single-source critical SKUs may bypass step 2 "
                "with VP Supply Chain sign-off."
            ),
            source="internal_policy",
            tags=["supplier", "procurement", "policy"],
        ),
        KnowledgeDocument(
            title="Historical Incident — Suez Canal Blockage (2021) Lessons Learned",
            content=(
                "During the 2021 Suez Canal blockage, shipments relying on single-route ocean "
                "freight from Asia to Europe experienced average delays of 18 days. Post-incident "
                "review recommended maintaining dual-route capability (Suez and Cape of Good Hope) "
                "for at least 30% of high-value ocean freight volume, and pre-negotiating air "
                "freight capacity options with at least two carriers per major trade lane."
            ),
            source="incident_report",
            tags=["risk", "geopolitical", "ocean freight", "history"],
        ),
        KnowledgeDocument(
            title="Safety Stock Calculation Methodology",
            content=(
                "Safety stock is calculated as: Z-score (service level) x standard deviation of "
                "lead time demand x sqrt(average lead time). The default target service level is "
                "95% (Z=1.65). Categories with single-source suppliers or lead times exceeding 30 "
                "days should use a 98% service level (Z=2.05) given limited ability to expedite."
            ),
            source="internal_policy",
            tags=["inventory", "safety stock", "policy", "methodology"],
        ),
    ]


async def seed() -> None:
    client = AsyncIOMotorClient(settings.mongodb_uri)
    db = client[settings.mongodb_db_name]

    print("Clearing existing demo collections...")
    for coll in [COLL_INVENTORY, COLL_SHIPMENTS, COLL_SUPPLIERS, COLL_RISK_EVENTS]:
        await db[coll].delete_many({})

    await ensure_indexes(db)

    print("Seeding suppliers...")
    suppliers = make_suppliers()
    await db[COLL_SUPPLIERS].insert_many([s.model_dump() for s in suppliers])

    print("Seeding inventory...")
    inventory = make_inventory(suppliers)
    await db[COLL_INVENTORY].insert_many([i.model_dump() for i in inventory])

    print("Seeding shipments...")
    shipments = make_shipments(inventory)
    await db[COLL_SHIPMENTS].insert_many([s.model_dump() for s in shipments])

    print("Seeding risk events...")
    risks = make_risk_events()
    await db[COLL_RISK_EVENTS].insert_many([r.model_dump() for r in risks])

    if settings.voyage_api_key:
        print("Embedding and seeding knowledge base via Voyage AI...")
        knowledge_service = KnowledgeService(db)
        docs = make_knowledge_documents()
        await knowledge_service.ingest_bulk(docs)
    else:
        print("VOYAGE_API_KEY not set — skipping knowledge base embedding. "
              "Set it in .env and rerun to enable the Knowledge Agent.")

    print(
        f"Done. Seeded {len(suppliers)} suppliers, {len(inventory)} SKUs, "
        f"{len(shipments)} shipments, {len(risks)} risk events."
    )
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
