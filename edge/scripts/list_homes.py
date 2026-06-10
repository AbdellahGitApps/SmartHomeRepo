from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection.database import SessionLocal
from database.models.home import Home

db = SessionLocal()

homes = db.query(Home).all()

print(f"Homes Count = {len(homes)}")

for h in homes:
    print(
        f"ID={h.id} | CODE={h.home_code} | NAME={h.name}"
    )

db.close()