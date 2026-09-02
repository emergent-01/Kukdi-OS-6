"""One-off additive starter seed for the single user: 4 STAR story drafts and 2
tentative calendar events. Uses existing collection shapes only. Idempotent —
skips any record whose title already exists. Run: python seed_starter.py
"""
import os
from datetime import datetime, timezone, date

from dotenv import load_dotenv
from pymongo import MongoClient

from models import new_id, now_iso

load_dotenv()
client = MongoClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]

STORIES = [
    {
        "title": "Doubling the Toastmasters budget",
        "situation": "As a leader in Thapar Toastmasters, the club needed significantly more budget than the previous year to run a bigger slate of public-speaking events.",
        "task": "Convince the university authorities to approve a budget increase of over 100%.",
        "action": "Presented a clear vision of what public speaking at Thapar could look like that year and walked the authorities through the impact, winning their buy-in. [she'll refine with specifics]",
        "result": "Secured a budget increase of more than 100% over the prior year.",
        "themes": ["Influence", "Execution"],
        "tags": ["Toastmasters", "leadership"],
    },
    {
        "title": "Winning HACKOWASP with a contactless-shopping prototype",
        "situation": "During the COVID-19 pandemic, HACKOWASP 2.1 brought together 15+ teams to solve real problems.",
        "task": "Design and build a user-centric solution that stood out.",
        "action": "Built a contactless-shopping interface prototype focused on the user experience of shopping safely during the pandemic. [she'll refine with specifics]",
        "result": "Earned first position among 15+ teams.",
        "themes": ["Customer Focus", "Execution"],
        "tags": ["hackathon", "product"],
    },
    {
        "title": "Handling conflict in the OWASP chapter",
        "situation": "A miscommunication/conflict arose within the OWASP student chapter at Thapar.",
        "task": "Step in and resolve the situation while keeping the team functioning.",
        "action": "[she'll refine — took the lead, thought on her feet, and defused the situation]",
        "result": "Resolved the conflict and kept the chapter on track.",
        "themes": ["Conflict", "Leadership"],
        "tags": ["OWASP", "teamwork"],
    },
    {
        "title": "Teaching on mobile-only during COVID",
        "situation": "While volunteering as a math tutor for underprivileged Class 9-10 students during COVID-19, students had access to phones only, with severe resource constraints.",
        "task": "Keep learning interactive and effective despite the constraints.",
        "action": "Innovated a low-cost DIY stylus and adapted problem-solving sessions to work on phones, improving engagement. [she'll refine with specifics]",
        "result": "Sustained interactive learning over ~8 months for students who otherwise couldn't access it.",
        "themes": ["Ambiguity", "Customer Focus"],
        "tags": ["tutoring", "impact"],
    },
]


def _future(month: int, day: int) -> str:
    today = datetime.now(timezone.utc).date()
    year = today.year
    if date(year, month, day) < today:
        year += 1
    return datetime(year, month, day, 9, 0, tzinfo=timezone.utc).isoformat()


EVENTS = [
    {
        "type": "deadline",
        "title": "Company registrations — expected mid-September (tentative)",
        "start": _future(9, 15),
        "notes": "College hasn't officially announced yet — update when confirmed.",
    },
    {
        "type": "placement",
        "title": "Interviews — expected around November (tentative)",
        "start": _future(11, 5),
        "notes": "Tentative — the college hasn't announced final dates. Update when known.",
    },
]


def seed_stories():
    added = 0
    for s in STORIES:
        if db.stories.find_one({"title": s["title"]}):
            print(f"  skip (exists): {s['title']}")
            continue
        doc = {
            "id": new_id(),
            "title": s["title"],
            "situation": s["situation"],
            "task": s["task"],
            "action": s["action"],
            "result": s["result"],
            "themes": s["themes"],
            "tags": s["tags"],
            "companies_used": [],
            "status": "draft",
            "feedback": "",
            "created": now_iso(),
            "updated": now_iso(),
        }
        db.stories.insert_one(doc)
        added += 1
        print(f"  added story: {s['title']}")
    return added


def seed_events():
    added = 0
    for e in EVENTS:
        if db.events.find_one({"title": e["title"]}):
            print(f"  skip (exists): {e['title']}")
            continue
        doc = {
            "id": new_id(),
            "type": e["type"],
            "title": e["title"],
            "start": e["start"],
            "end": None,
            "location": "",
            "course": "",
            "notes": e["notes"],
            "done": False,
            "created": now_iso(),
        }
        db.events.insert_one(doc)
        added += 1
        print(f"  added event: {e['title']} @ {e['start'][:10]}")
    return added


if __name__ == "__main__":
    print("Seeding starter stories...")
    ns = seed_stories()
    print("Seeding starter events...")
    ne = seed_events()
    print(f"Done. Stories added: {ns}, Events added: {ne}")
    print("Totals -> stories:", db.stories.count_documents({}), "events:", db.events.count_documents({}))
