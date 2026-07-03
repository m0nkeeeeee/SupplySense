"""Risk, recommendations, and reports — read-mostly endpoints surfaced by the
dashboard, plus PDF export for reports."""
from __future__ import annotations

import io
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.database import COLL_RECOMMENDATIONS, COLL_REPORTS, COLL_RISK_EVENTS, get_db
from app.models.schemas import Recommendation, Report, RiskEvent

router = APIRouter(tags=["insights"])


@router.get("/risks", response_model=List[RiskEvent])
async def list_risks(limit: int = 50):
    db = get_db()
    cursor = db[COLL_RISK_EVENTS].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


@router.get("/recommendations", response_model=List[Recommendation])
async def list_recommendations(limit: int = 50):
    db = get_db()
    cursor = db[COLL_RECOMMENDATIONS].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


@router.get("/reports", response_model=List[Report])
async def list_reports(limit: int = 20):
    db = get_db()
    cursor = db[COLL_REPORTS].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)


@router.get("/reports/{report_id}", response_model=Report)
async def get_report(report_id: str):
    db = get_db()
    report = await db[COLL_REPORTS].find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@router.get("/reports/{report_id}/pdf")
async def export_report_pdf(report_id: str):
    db = get_db()
    report = await db[COLL_REPORTS].find_one({"report_id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(report["title"], styles["Title"]),
        Spacer(1, 12),
        Paragraph(report["summary"], styles["BodyText"]),
        Spacer(1, 18),
    ]
    for section in report.get("sections", []):
        story.append(Paragraph(section.get("heading", ""), styles["Heading2"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(section.get("body", "").replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 14))

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={report_id}.pdf"},
    )
