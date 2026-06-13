import os

# ---------------------------------------------------------
# 1. api/family_management_flow.py
# ---------------------------------------------------------
filepath = 'e:/SmartHomeMobileApp/edge/api/family_management_flow.py'

with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace register_family_member (actually named create_family_member)
old_insert = """    with _conn() as conn:
        _ensure_family_table(conn)

        conn.execute(\"\"\"
            INSERT INTO family_members (
                home_id,
                name,
                role,
                face_enrolled,
                enabled,
                person_id,
                notes,
                access_type,
                valid_from,
                valid_to,
                time_start,
                time_end,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \"\"\", (
            home_id,
            name,
            role,
            face_enrolled,
            enabled,
            person_id,
            payload.notes or "",
            payload.access_type or "Always",
            payload.valid_from,
            payload.valid_to,
            payload.time_start,
            payload.time_end,
            now,
            now,
        ))

        member_id = conn.execute(
            "SELECT last_insert_rowid() AS id"
        ).fetchone()["id"]"""

new_insert = """    with _conn() as conn:
        _ensure_family_table(conn)
        
        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            new_member = FamilyMember(
                home_id=home_id,
                name=name,
                role=role,
                face_enrolled=bool(face_enrolled),
                enabled=bool(enabled),
                person_id=person_id,
                notes=payload.notes or "",
                access_type=payload.access_type or "Always",
                valid_from=payload.valid_from,
                valid_to=payload.valid_to,
                time_start=payload.time_start,
                time_end=payload.time_end,
                created_at=now,
                updated_at=now
            )
            db.add(new_member)
            db.flush()
            member_id = new_member.id
            db.commit()
        finally:
            db.close()"""

code = code.replace(old_insert, new_insert)

# Replace delete_family_member
old_delete = """        conn.execute("DELETE FROM family_members WHERE id = ?", (member_id,))"""

new_delete = """        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                db.delete(member)
                db.commit()
        finally:
            db.close()"""

code = code.replace(old_delete, new_delete)

# Replace clear_family_members
old_clear = """        rows = conn.execute(
            "SELECT * FROM family_members WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)",
            (str(home_id),),
        ).fetchall()

        count = len(rows)

        conn.execute(
            "DELETE FROM family_members WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)",
            (str(home_id),),
        )"""

new_clear = """        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            rows = db.query(FamilyMember).filter(FamilyMember.home_id == home_id).all()
            count = len(rows)
            for member in rows:
                db.delete(member)
            db.commit()
        finally:
            db.close()"""

code = code.replace(old_clear, new_clear)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("api/family_management_flow.py updated")

# ---------------------------------------------------------
# 2. main.py
# ---------------------------------------------------------
filepath = 'e:/SmartHomeMobileApp/edge/main.py'
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

old_insert_unknown = """        conn.execute(
            f"INSERT INTO family_members ({', '.join(keys)}) VALUES ({', '.join(['?'] * len(keys))})",
            [data[k] for k in keys],
        )"""

new_insert_unknown = """        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            new_member = FamilyMember(
                home_id=data.get("home_id", 1),
                name=data.get("name"),
                role=data.get("role", "Family"),
                face_enrolled=bool(data.get("face_enrolled", 0)),
                enabled=bool(data.get("enabled", 1)),
                notes=data.get("notes", ""),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at")
            )
            db.add(new_member)
            db.commit()
        finally:
            db.close()"""

code = code.replace(old_insert_unknown, new_insert_unknown)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("main.py updated")

# ---------------------------------------------------------
# 3. routers/dashboard.py
# ---------------------------------------------------------
filepath = 'e:/SmartHomeMobileApp/edge/routers/dashboard.py'
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

old_dash_delete = """        cur.execute(
            "DELETE FROM family_members WHERE home_id = ?",
            (actual_home_id,)
        )"""

new_dash_delete = """        from database.connection.database import SessionLocal
        from database.models.family import FamilyMember
        db = SessionLocal()
        try:
            db.query(FamilyMember).filter(FamilyMember.home_id == actual_home_id).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()"""

code = code.replace(old_dash_delete, new_dash_delete)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("routers/dashboard.py updated")
