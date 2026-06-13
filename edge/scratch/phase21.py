import os

filepath = 'e:/SmartHomeMobileApp/edge/api/family_management_flow.py'

with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

import_statement = """from typing import Optional
import sqlite3
from database.connection.database import SessionLocal
from database.models.family import FamilyMember
from sqlalchemy import desc, func"""

code = code.replace("from typing import Optional\nimport sqlite3", import_statement)

# Replace _get_member
old_get_member = """def _get_member(conn, member_id):
    row = conn.execute(
        "SELECT * FROM family_members WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
        (str(member_id),),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Family member not found: {member_id}")

    return row"""

new_get_member = """def _get_member(conn, member_id):
    db = SessionLocal()
    try:
        member = db.query(FamilyMember).filter(FamilyMember.id == int(member_id)).first()
        if not member:
            raise HTTPException(status_code=404, detail=f"Family member not found: {member_id}")
        
        # Return a dict to preserve compatibility with existing write operations
        # that treat the return value as a sqlite3.Row
        from datetime import datetime
        return {
            "id": member.id,
            "home_id": member.home_id,
            "name": member.name,
            "role": member.role,
            "face_enrolled": 1 if member.face_enrolled else 0,
            "enabled": 1 if member.enabled else 0,
            "person_id": member.person_id,
            "notes": member.notes,
            "access_type": member.access_type,
            "valid_from": member.valid_from,
            "valid_to": member.valid_to,
            "time_start": member.time_start,
            "time_end": member.time_end,
            "created_at": member.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(member.created_at, datetime) else member.created_at,
            "updated_at": member.updated_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(member.updated_at, datetime) else member.updated_at,
        }
    finally:
        db.close()"""

code = code.replace(old_get_member, new_get_member)


# Replace family_status
old_family_status = """def family_status():
    with _conn() as conn:
        _ensure_family_table(conn)
        total = conn.execute("SELECT COUNT(*) AS c FROM family_members").fetchone()["c"]
        enabled = conn.execute("SELECT COUNT(*) AS c FROM family_members WHERE enabled = 1").fetchone()["c"]
        disabled = conn.execute("SELECT COUNT(*) AS c FROM family_members WHERE enabled = 0").fetchone()["c"]

        return {
            "success": True,
            "family_members": total,
            "enabled": enabled,
            "disabled": disabled,
        }"""

new_family_status = """def family_status():
    db = SessionLocal()
    try:
        total = db.query(FamilyMember).count()
        enabled = db.query(FamilyMember).filter(FamilyMember.enabled == True).count()
        disabled = db.query(FamilyMember).filter(FamilyMember.enabled == False).count()

        return {
            "success": True,
            "family_members": total,
            "enabled": enabled,
            "disabled": disabled,
        }
    finally:
        db.close()"""

code = code.replace(old_family_status, new_family_status)


# Replace list_family_members
old_list_family_members = """def list_family_members(home_id: Optional[int] = None, include_disabled: bool = True):
    with _conn() as conn:
        _ensure_family_table(conn)

        params = []
        query = "SELECT * FROM family_members WHERE 1=1"

        if home_id is not None:
            query += " AND CAST(home_id AS TEXT) = CAST(? AS TEXT)"
            params.append(str(home_id))

        if not include_disabled:
            query += " AND enabled = 1"

        query += " ORDER BY COALESCE(created_at, updated_at, '') DESC, id DESC"

        rows = conn.execute(query, params).fetchall()
        
        # Get face counts for enrolled members
        person_ids = [r["person_id"] for r in rows if r["person_id"]]
        face_counts = {}
        if person_ids:
            try:
                from api.face_recognition_flow import _connect_model_db
                model_conn = _connect_model_db()
                placeholders = ",".join("?" * len(person_ids))
                count_rows = model_conn.execute(f"SELECT person_id, COUNT(*) as c FROM face_embeddings WHERE person_id IN ({placeholders}) GROUP BY person_id", person_ids).fetchall()
                face_counts = {r["person_id"]: r["c"] for r in count_rows}
                model_conn.close()
            except Exception:
                pass

        members = []
        for row in rows:
            data = dict(row)
            count = face_counts.get(data.get("person_id"), 1 if _bool(data.get("face_enrolled")) else 0)
            members.append(_member_dict(row, count))

        return {
            "success": True,
            "members": members,
        }"""

new_list_family_members = """def list_family_members(home_id: Optional[int] = None, include_disabled: bool = True):
    db = SessionLocal()
    try:
        query = db.query(FamilyMember)

        if home_id is not None:
            query = query.filter(FamilyMember.home_id == home_id)

        if not include_disabled:
            query = query.filter(FamilyMember.enabled == True)

        query = query.order_by(desc(func.coalesce(FamilyMember.created_at, FamilyMember.updated_at, '')), desc(FamilyMember.id))

        orm_rows = query.all()
        
        from datetime import datetime
        rows = []
        for member in orm_rows:
            rows.append({
                "id": member.id,
                "home_id": member.home_id,
                "name": member.name,
                "role": member.role,
                "face_enrolled": 1 if member.face_enrolled else 0,
                "enabled": 1 if member.enabled else 0,
                "person_id": member.person_id,
                "notes": member.notes,
                "access_type": member.access_type,
                "valid_from": member.valid_from,
                "valid_to": member.valid_to,
                "time_start": member.time_start,
                "time_end": member.time_end,
                "created_at": member.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(member.created_at, datetime) else member.created_at,
                "updated_at": member.updated_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(member.updated_at, datetime) else member.updated_at,
            })
        
        # Get face counts for enrolled members
        person_ids = [r["person_id"] for r in rows if r["person_id"]]
        face_counts = {}
        if person_ids:
            try:
                from api.face_recognition_flow import _connect_model_db
                model_conn = _connect_model_db()
                placeholders = ",".join("?" * len(person_ids))
                count_rows = model_conn.execute(f"SELECT person_id, COUNT(*) as c FROM face_embeddings WHERE person_id IN ({placeholders}) GROUP BY person_id", person_ids).fetchall()
                face_counts = {r["person_id"]: r["c"] for r in count_rows}
                model_conn.close()
            except Exception:
                pass

        members = []
        for row in rows:
            data = dict(row)
            count = face_counts.get(data.get("person_id"), 1 if _bool(data.get("face_enrolled")) else 0)
            members.append(_member_dict(row, count))

        return {
            "success": True,
            "members": members,
        }
    finally:
        db.close()"""

code = code.replace(old_list_family_members, new_list_family_members)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("Refactor completed.")
