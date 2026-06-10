from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection.database import SessionLocal
from database.models.ai_face import FaceEvent

db = SessionLocal()

events = (
    db.query(FaceEvent)
    .order_by(FaceEvent.id.desc())
    .all()
)

print(f"Events Count = {len(events)}")

for e in events:
    print(
        f"ID={e.id} | "
        f"TYPE={e.event_type} | "
        f"PERSON={e.person_id} | "
        f"SCORE={e.score} | "
        f"IMAGE={e.snapshot_path}"
    )

db.close()