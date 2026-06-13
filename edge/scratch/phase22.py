import os

filepath = 'e:/SmartHomeMobileApp/edge/api/family_management_flow.py'

with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

# Refactor enable_family_member
old_enable = """        conn.execute(
            "UPDATE family_members SET enabled = 1, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )"""

new_enable = """        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                member.enabled = True
                from datetime import datetime
                member.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()"""
code = code.replace(old_enable, new_enable)

# Refactor disable_family_member
old_disable = """        conn.execute(
            "UPDATE family_members SET enabled = 0, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )"""

new_disable = """        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                member.enabled = False
                from datetime import datetime
                member.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()"""
code = code.replace(old_disable, new_disable)

# Refactor update_family_member
old_update = """        conn.execute(\"\"\"
            UPDATE family_members
            SET home_id = ?,
                name = ?,
                role = ?,
                face_enrolled = ?,
                enabled = ?,
                person_id = ?,
                notes = ?,
                access_type = ?,
                valid_from = ?,
                valid_to = ?,
                time_start = ?,
                time_end = ?,
                updated_at = ?
            WHERE id = ?
        \"\"\", (
            home_id,
            name,
            role,
            face_enrolled,
            enabled,
            person_id,
            notes or "",
            payload.access_type if payload.access_type is not None else old["access_type"],
            payload.valid_from if payload.valid_from is not None else dict(old).get("valid_from"),
            payload.valid_to if payload.valid_to is not None else dict(old).get("valid_to"),
            payload.time_start if payload.time_start is not None else dict(old).get("time_start"),
            payload.time_end if payload.time_end is not None else dict(old).get("time_end"),
            _now(),
            member_id,
        ))"""

new_update = """        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                member.home_id = home_id
                member.name = name
                member.role = role
                member.face_enrolled = bool(face_enrolled)
                member.enabled = bool(enabled)
                member.person_id = person_id
                member.notes = notes or ""
                member.access_type = payload.access_type if payload.access_type is not None else old["access_type"]
                member.valid_from = payload.valid_from if payload.valid_from is not None else dict(old).get("valid_from")
                member.valid_to = payload.valid_to if payload.valid_to is not None else dict(old).get("valid_to")
                member.time_start = payload.time_start if payload.time_start is not None else dict(old).get("time_start")
                member.time_end = payload.time_end if payload.time_end is not None else dict(old).get("time_end")
                from datetime import datetime
                member.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()"""
code = code.replace(old_update, new_update)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("Refactor script executed successfully.")
