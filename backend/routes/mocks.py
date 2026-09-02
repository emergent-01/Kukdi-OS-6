"""Mock interview sessions — a quiet log of practice rounds within the prep
circle. Additive collection; DB access lives here only (no LLM logic). Every
document carries a uuid `id` and ISO datetimes; Mongo's `_id` is always projected
out and never returned.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException

from database import db
from models import MockSessionIn, MockSessionUpdate, new_id, now_iso

router = APIRouter()


@router.post("")
async def create_mock(body: MockSessionIn):
    doc = body.model_dump()
    if not (doc.get("date") or "").strip():
        doc["date"] = now_iso()
    doc.update({"id": new_id(), "created": now_iso(), "updated": now_iso()})
    await db.mock_sessions.insert_one({k: v for k, v in doc.items()})
    return {k: v for k, v in doc.items() if k != "_id"}


@router.get("")
async def list_mocks(person_id: Optional[str] = None):
    query = {"person_ids": person_id} if person_id else {}
    mocks = await db.mock_sessions.find(query, {"_id": 0}).sort("date", -1).to_list(500)
    return {"mocks": mocks}


@router.patch("/{mock_id}")
async def update_mock(mock_id: str, body: MockSessionUpdate):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        raise HTTPException(400, "No changes")
    changes["updated"] = now_iso()
    res = await db.mock_sessions.update_one({"id": mock_id}, {"$set": changes})
    if not res.matched_count:
        raise HTTPException(404, "Mock session not found")
    return await db.mock_sessions.find_one({"id": mock_id}, {"_id": 0})


@router.delete("/{mock_id}")
async def delete_mock(mock_id: str):
    await db.mock_sessions.delete_one({"id": mock_id})
    return {"ok": True}
