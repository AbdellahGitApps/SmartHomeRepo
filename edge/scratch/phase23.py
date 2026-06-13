import re

def clean_family_management_flow():
    filepath = 'e:/SmartHomeMobileApp/edge/api/family_management_flow.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove _ensure_family_table definition
    pattern_ensure_def = re.compile(r'def _ensure_family_table\(conn\):.*?(?=\n\n\ndef |\n\n\n@router)', re.DOTALL)
    content = pattern_ensure_def.sub('', content)

    # 2. Remove all calls to _ensure_family_table(conn)
    content = content.replace('        _ensure_family_table(conn)\n', '')
    content = content.replace('    _ensure_family_table(conn)\n', '')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("api/family_management_flow.py cleaned")

def clean_main_py():
    filepath = 'e:/SmartHomeMobileApp/edge/main.py'
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove # 2. family_members from init_database_tables
    pattern_init = re.compile(r'        # 2\. family_members\n        cur\.execute\("""\n            CREATE TABLE IF NOT EXISTS family_members.*?print\("\[DB INIT\] family_members verified"\)\n\n', re.DOTALL)
    content = pattern_init.sub('', content)

    # 2. Remove table creation from d7m16_fake_known_family_face
    pattern_fake_known = re.compile(r'        conn\.execute\("""\n            CREATE TABLE IF NOT EXISTS family_members.*?if col not in family_cols:\n                conn\.execute\(f"ALTER TABLE family_members ADD COLUMN \{col\} \{col_type\}"\)\n', re.DOTALL)
    content = pattern_fake_known.sub('', content)

    # 3. Clean _d7m16_insert_family_member_from_unknown
    old_unknown = """def _d7m16_insert_family_member_from_unknown(conn, home_id, name, face_enrolled=False):
    try:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "family_members" not in tables:
            conn.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS family_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_id INTEGER DEFAULT 1,
                    name TEXT NOT NULL,
                    role TEXT DEFAULT 'Family',
                    face_enrolled INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    person_id INTEGER,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            \"\"\")

        cols = [r[1] for r in conn.execute("PRAGMA table_info(family_members)").fetchall()]
        now = _d7m16_now()
        clean_name = _d7m16_log_norm(name) or "Unknown person"

        data = {
            "home_id": int(str(home_id or "1")) if str(home_id or "1").isdigit() else 1,
            "name": clean_name,
            "role": "Family",
            "face_enrolled": 1 if face_enrolled else 0,
            "enabled": 1,
            "notes": "Added from Unknown Face alert.",
            "created_at": now,
            "updated_at": now,
        }

        keys = [k for k in data if k in cols]
        if "name" not in keys:
            return

        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            from datetime import datetime
            new_member = FamilyMember(
                home_id=data.get("home_id", 1),
                name=data.get("name"),
                role=data.get("role", "Family"),
                face_enrolled=bool(data.get("face_enrolled", 0)),
                enabled=bool(data.get("enabled", 1)),
                notes=data.get("notes", ""),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_member)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass"""

    new_unknown = """def _d7m16_insert_family_member_from_unknown(conn, home_id, name, face_enrolled=False):
    try:
        clean_name = _d7m16_log_norm(name) or "Unknown person"
        if not clean_name:
            return

        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            from datetime import datetime
            new_member = FamilyMember(
                home_id=int(str(home_id or "1")) if str(home_id or "1").isdigit() else 1,
                name=clean_name,
                role="Family",
                face_enrolled=bool(face_enrolled),
                enabled=True,
                notes="Added from Unknown Face alert.",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_member)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass"""
    
    if old_unknown in content:
        content = content.replace(old_unknown, new_unknown)
    else:
        print("WARNING: Could not find old _d7m16_insert_family_member_from_unknown exactly!")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("main.py cleaned")

if __name__ == '__main__':
    clean_family_management_flow()
    clean_main_py()
