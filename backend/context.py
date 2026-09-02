"""Assembles the context Kukdi reasons over. This is the seam between the DB and
the reasoning engine — routes call `build_context()` and hand the result to
`reasoning`. Keeping it here means the engine stays pure and the queries live in
one place.
"""
from __future__ import annotations

from datetime import datetime, timezone

from database import db
from models import INTERVIEW_COMPETENCIES


async def build_context() -> dict:
    memories = await db.memories.find(
        {"status": "active"}, {"_id": 0}
    ).sort("confidence", -1).to_list(60)

    now = datetime.now(timezone.utc).isoformat()
    events = await db.events.find(
        {"start": {"$gte": now}}, {"_id": 0}
    ).sort("start", 1).to_list(20)

    profile = next(
        (m["description"] for m in memories if m.get("type") == "Profile"),
        "Little Miss, MBA (PGP) student at ISB Mohali, aspiring Product Manager.",
    )
    return {"profile": profile, "memories": memories, "events": events}


async def build_prep_context() -> dict:
    """Read-only assembly for prep nudges: competency coverage (mirrors the Story
    Bank coverage computation), the prep circle, recent/unacted mock sessions, and
    upcoming interview-type events. The reasoning engine never touches Mongo — this
    is the only seam. Returns a plain dict.
    """
    # --- Competency coverage (same algorithm as routes/stories.py::coverage) ---
    stories = await db.stories.find({}, {"_id": 0}).to_list(500)
    lower_map = {c.lower(): c for c in INTERVIEW_COMPETENCIES}
    counts = {c: 0 for c in INTERVIEW_COMPETENCIES}
    for s in stories:
        seen = set()
        for t in (s.get("themes") or []):
            key = (t or "").strip().lower()
            if not key:
                continue
            comp = lower_map.get(key)
            if not comp:
                for lc, orig in lower_map.items():
                    if lc in key or key in lc:
                        comp = orig
                        break
            if comp and comp not in seen:
                counts[comp] += 1
                seen.add(comp)
    missing = [c for c in INTERVIEW_COMPETENCIES if counts[c] == 0]
    thin = [c for c in INTERVIEW_COMPETENCIES if counts[c] == 1]

    # --- Prep circle ---
    circle = await db.people.find(
        {"prep_group": True}, {"_id": 0}
    ).sort("name", 1).to_list(100)
    circle_people = [
        {
            "id": p["id"],
            "name": p.get("name", ""),
            "strengths": p.get("strengths", []) or [],
            "strength_note": p.get("strength_note", "") or "",
        }
        for p in circle
    ]

    # --- Recent mock sessions (newest first); resolve who from person ids ---
    all_people = await db.people.find({}, {"_id": 0}).to_list(500)
    name_by_id = {p["id"]: p.get("name", "") for p in all_people}
    mocks = await db.mock_sessions.find({}, {"_id": 0}).sort("date", -1).to_list(50)
    recent_mocks = []
    for m in mocks[:20]:
        who = [name_by_id.get(pid, "") for pid in (m.get("person_ids") or []) if name_by_id.get(pid)]
        recent_mocks.append({
            "id": m["id"],
            "date": m.get("date", ""),
            "who": who,
            "competencies": m.get("competencies", []) or [],
            "company": m.get("company") or "",
            "feedback": m.get("feedback") or "",
            "what_went_well": m.get("what_went_well") or "",
            "to_act_on": m.get("to_act_on") or "",
            "acted": bool(m.get("acted")),
        })
    unacted_mocks = [m for m in recent_mocks if m["to_act_on"] and not m["acted"]]

    # --- Upcoming interview-type events, nearest first ---
    now = datetime.now(timezone.utc).isoformat()
    events = await db.events.find(
        {"type": {"$in": ["interview", "placement"]}, "start": {"$gte": now}},
        {"_id": 0},
    ).sort("start", 1).to_list(20)
    interview_events = [
        {"id": e["id"], "title": e.get("title", ""), "start": e.get("start", ""),
         "type": e.get("type", "")}
        for e in events
    ]

    return {
        "coverage": {"missing": missing, "thin": thin, "counts": counts},
        "circle_people": circle_people,
        "recent_mocks": recent_mocks,
        "unacted_mocks": unacted_mocks,
        "interview_events": interview_events,
    }
