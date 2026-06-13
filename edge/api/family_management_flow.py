
from datetime import datetime
from pathlib import Path
from typing import Optional
import sqlite3
from database.connection.database import SessionLocal
from database.models.family import FamilyMember
from sqlalchemy import desc, func

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel


router = APIRouter(tags=["Family Management"])


class FamilyMemberCreate(BaseModel):
    home_id: Optional[int] = None
    name: str
    role: str = "Family"
    face_enrolled: bool = False
    enabled: bool = True
    notes: Optional[str] = None
    access_type: str = "Always"
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None

    face_image_data: Optional[str] = None


class FamilyMemberUpdate(BaseModel):
    home_id: Optional[int] = None
    name: Optional[str] = None
    role: Optional[str] = "Family"
    face_enrolled: Optional[bool] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None
    access_type: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None

    face_image_data: Optional[str] = None


def _db_path() -> Path:
    try:
        from core_database import get_database_path
        return get_database_path()
    except Exception:
        base = Path(__file__).resolve().parents[1]
        return base / "database" / "smart_home_edge.db"


def _conn():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _tables(conn):
    return {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}


def _cols(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}





def _ensure_logs_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            created_at TEXT,
            severity TEXT,
            actor TEXT,
            source TEXT,
            home TEXT,
            home_id TEXT,
            apartment_number TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT,
            device_id TEXT,
            device_name TEXT
        )
    """)

    needed = {
        "timestamp": "TEXT",
        "created_at": "TEXT",
        "severity": "TEXT",
        "actor": "TEXT",
        "source": "TEXT",
        "home": "TEXT",
        "home_id": "TEXT",
        "apartment_number": "TEXT",
        "event_type": "TEXT",
        "details": "TEXT",
        "action_taken": "TEXT",
        "device_id": "TEXT",
        "device_name": "TEXT",
    }

    cols = _cols(conn, "system_logs")
    for col, col_type in needed.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE system_logs ADD COLUMN {col} {col_type}")

    conn.commit()


def _home_apartment(conn, home_id):
    if not home_id:
        return ""

    if "homes" not in _tables(conn):
        return ""

    row = conn.execute(
        "SELECT apartment_number FROM homes WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
        (str(home_id),),
    ).fetchone()

    return str(row["apartment_number"] or "") if row else ""


def _family_role(value):
    if not value:
        return "Family"
    
    valid_roles = {"Owner", "Family", "Guest", "Worker", "Child", "Blocked"}
    
    # Exact match
    if value in valid_roles:
        return value
        
    # Case-insensitive match
    for role in valid_roles:
        if str(value).lower() == role.lower():
            return role
            
    return "Family"


def _bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0

    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "enabled", "on"}:
        return True
    if text in {"0", "false", "no", "disabled", "off"}:
        return False

    return default


def _member_dict(row, face_count=0):
    data = dict(row)
    return {
        **data,
        "id": str(data.get("id") or ""),
        "raw_id": data.get("id"),
        "name": str(data.get("name") or "Unknown"),
        "role": data.get("role") or "Family",
        "face_enrolled": _bool(data.get("face_enrolled")),
        "faceEnrolled": _bool(data.get("face_enrolled")),
        "face_count": face_count,
        "faceCount": face_count,
        "enabled": _bool(data.get("enabled"), True),
        "isEnabled": _bool(data.get("enabled"), True),
        "access_type": data.get("access_type") or "Always",
        "valid_from": data.get("valid_from"),
        "valid_to": data.get("valid_to"),
        "time_start": data.get("time_start"),
        "time_end": data.get("time_end"),
        "created_at": data.get("created_at") or "",
        "createdAt": data.get("created_at") or "",
        "updated_at": data.get("updated_at") or "",
        "updatedAt": data.get("updated_at") or "",
    }


def _get_member(conn, member_id):
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
        db.close()


def _log_family_action(conn, *, home_id, member_name, severity, details, action_taken):
    _ensure_logs_table(conn)

    now = _now()
    apartment = _home_apartment(conn, home_id)

    conn.execute("""
        INSERT INTO system_logs (
            timestamp,
            created_at,
            severity,
            actor,
            source,
            home,
            home_id,
            apartment_number,
            event_type,
            details,
            action_taken,
            device_id,
            device_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now,
        now,
        severity.upper(),
        "Admin App",
        "Admin App",
        apartment,
        str(home_id or ""),
        apartment,
        "Family Management",
        details,
        action_taken,
        "family_members",
        member_name,
    ))


@router.get("/api/family/status")
def family_status():
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
        db.close()


@router.get("/api/family/members")
def list_family_members(home_id: Optional[int] = None, include_disabled: bool = True):
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
        db.close()


@router.post("/api/family/members")
def create_family_member(payload: FamilyMemberCreate, request: Request):

    name = (payload.name or "").strip()

    print("\n" + "=" * 80)
    print("CREATE FAMILY MEMBER REQUEST")
    print("=" * 80)
    print("NAME:", name)
    print("FACE ENROLLED:", payload.face_enrolled)

    if payload.face_image_data:
        print("FACE IMAGE RECEIVED: YES")
        print("IMAGE SIZE:", len(payload.face_image_data))
    else:
        print("FACE IMAGE RECEIVED: NO")

    print("=" * 80 + "\n")

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Member name is required."
        )

    role = _family_role(payload.role)
    now = _now()
    home_id = payload.home_id or 1
    enabled = 1 if payload.enabled else 0

    person_id = None
    if payload.face_image_data:
        import base64
        import numpy as np
        import cv2
        import json
        from api.face_recognition_flow import (
            _ensure_face_tables,
            _connect_model_db,
            _preprocess_face,
            _extract_embedding,
            _now_iso
        )

        try:
            print("[FACE] Decoding base64 image...")
            b64_str = payload.face_image_data
            if b64_str.startswith("data:image"):
                b64_str = b64_str.split(",", 1)[1]
            image_bytes = base64.b64decode(b64_str)
            print("[FACE] Base64 decoded successfully.")
            
            data = np.frombuffer(image_bytes, dtype=np.uint8)
            frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
            
            if frame is None:
                raise ValueError("Could not decode image format.")
            
            print("[FACE] Detecting face using Haar cascades...")
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            detector = cv2.CascadeClassifier(cascade_path)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
            )
            
            num_faces = len(faces)
            print(f"[FACE] Number of faces detected: {num_faces}")
            
            if num_faces == 0:
                raise ValueError("No face detected in the image.")
            if num_faces > 1:
                raise ValueError(f"Multiple faces ({num_faces}) detected. Please provide an image with exactly one face.")
            
            print("[FACE] Preprocessing face and extracting embedding...")
            box = faces[0]
            face_img = _preprocess_face(frame, box)
            embedding = _extract_embedding(face_img)
            print(f"[FACE] Embedding extracted successfully (Dimension: {len(embedding)}).")
            
            model_conn = _connect_model_db()
            try:
                _ensure_face_tables(model_conn)
                cur = model_conn.cursor()
                
                print("[FACE] Creating person record...")
                cur.execute("INSERT INTO persons (name, role, created_at) VALUES (?, ?, ?)", 
                            (name, role, _now_iso())
                )

                person_id = cur.lastrowid
                print(f"[FACE] Person created with ID: {person_id}")
                
                print("[FACE] Saving embedding...")
                emb_json = json.dumps(embedding)
                cur.execute("INSERT INTO face_embeddings (person_id, embedding_json, created_at) VALUES (?, ?, ?)",
                            (person_id, emb_json, _now_iso())
                )
                
                model_conn.commit()
                print("[FACE] Registration completed successfully in face_embeddings.")

                # ==================================================
                # COPY TO MAIN DATABASE USED BY RECOGNITION
                # ==================================================
                try:
                    from database.models.ai_face import Person, FaceEmbedding

                
                    db = SessionLocal()

                    try:
                        print("[SYNC] Creating ORM person...")

                        orm_person = Person(
                            home_id=home_id,
                            name=name,
                            role=role,
                        )

                        db.add(orm_person)
                        db.commit()
                        db.refresh(orm_person)

                        print(
                            f"[SYNC] ORM person created: {orm_person.id}"
                        )

                        orm_embedding = FaceEmbedding(
                            person_id=orm_person.id,
                            embedding_json=emb_json,
                        )

                        db.add(orm_embedding)
                        db.commit()

                        print(
                            f"[SYNC] ORM embedding saved for person {orm_person.id}"
                        )

                    finally:
                        db.close()

                except Exception as sync_error:
                    print(
                        f"[SYNC ERROR] {sync_error}"
                    )
            except Exception as e:
                model_conn.rollback()
                raise ValueError(f"Database insertion failed: {str(e)}")
            finally:
                model_conn.close()
                
        except Exception as e:
            print(f"[FACE ERROR] {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )

    face_enrolled = 1 if person_id is not None else (1 if payload.face_enrolled else 0)

    with _conn() as conn:
        
        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            from datetime import datetime
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
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(new_member)
            db.flush()
            member_id = new_member.id
            db.commit()
        finally:
            db.close()

        row = _get_member(conn, member_id)

        if face_enrolled:
            details = f"Family member {name} added with role Family / Face enrolled."
            action = "FAMILY MEMBER ADDED / FACE ENROLLED"
        else:
            details = f"Family member {name} added with role Family."
            action = "FAMILY MEMBER ADDED"

        _log_family_action(
            conn,
            home_id=home_id,
            member_name=name,
            severity="INFO",
            details=details,
            action_taken=action,
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member created successfully",
            "member": _member_dict(row, 1 if person_id else 0),
        }


@router.patch("/api/family/members/{member_id}")
def update_family_member(member_id: int, payload: FamilyMemberUpdate):
    with _conn() as conn:
        old = _get_member(conn, member_id)

        name = (payload.name if payload.name is not None else old["name"]).strip()
        if not name:
            raise HTTPException(status_code=400, detail="Member name is required.")

        role = _family_role(payload.role) if payload.role is not None else old["role"]
        enabled = old["enabled"] if payload.enabled is None else (1 if payload.enabled else 0)
        home_id = payload.home_id if payload.home_id is not None else old["home_id"]
        notes = payload.notes if payload.notes is not None else old["notes"]
        
        person_id = dict(old).get("person_id")
        
        if payload.face_image_data:
            import base64
            import numpy as np
            import cv2
            import json
            from api.face_recognition_flow import (
                _ensure_face_tables,
                _connect_model_db,
                _preprocess_face,
                _extract_embedding,
                _now_iso
            )
            
            try:
                print("[FACE UPDATE] Decoding base64 image...")
                b64_str = payload.face_image_data
                if b64_str.startswith("data:image"):
                    b64_str = b64_str.split(",", 1)[1]
                image_bytes = base64.b64decode(b64_str)
                
                data = np.frombuffer(image_bytes, dtype=np.uint8)
                frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
                
                if frame is None:
                    raise ValueError("Could not decode image format.")
                
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                detector = cv2.CascadeClassifier(cascade_path)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(80, 80),
                )
                
                num_faces = len(faces)
                if num_faces == 0:
                    raise ValueError("No face detected in the image.")
                if num_faces > 1:
                    raise ValueError(f"Multiple faces ({num_faces}) detected. Please provide an image with exactly one face.")
                
                box = faces[0]
                face_img = _preprocess_face(frame, box)
                embedding = _extract_embedding(face_img)
                
                model_conn = _connect_model_db()
                try:
                    _ensure_face_tables(model_conn)
                    cur = model_conn.cursor()
                    
                    if person_id is None:
                        cur.execute("INSERT INTO persons (name, role, created_at) VALUES (?, ?, ?)", 
                                    (name, role, _now_iso()))
                        person_id = cur.lastrowid
                    
                    emb_json = json.dumps(embedding)
                    cur.execute("INSERT INTO face_embeddings (person_id, embedding_json, created_at) VALUES (?, ?, ?)",
                                (person_id, emb_json, _now_iso()))
                    
                    model_conn.commit()
                except Exception as e:
                    model_conn.rollback()
                    raise ValueError(f"Database insertion failed: {str(e)}")
                finally:
                    model_conn.close()
                    
            except Exception as e:
                print(f"[FACE ERROR] {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )
                
            face_enrolled = 1
        else:
            face_enrolled = old["face_enrolled"] if payload.face_enrolled is None else (1 if payload.face_enrolled else 0)

        db = SessionLocal()
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
            db.close()

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=home_id,
            member_name=name,
            severity="INFO",
            details=f"Family member {name} updated.",
            action_taken="FAMILY MEMBER UPDATED",
        )

        conn.commit()
        
        # Determine face count
        face_count = 1 if face_enrolled else 0
        if person_id:
            try:
                from api.face_recognition_flow import _connect_model_db
                model_conn = _connect_model_db()
                c = model_conn.execute("SELECT COUNT(*) as c FROM face_embeddings WHERE person_id = ?", (person_id,)).fetchone()
                if c:
                    face_count = c["c"]
                model_conn.close()
            except Exception:
                pass

        return {
            "success": True,
            "message": "Family member updated successfully",
            "member": _member_dict(row, face_count),
        }


@router.patch("/api/family/members/{member_id}/enable")
def enable_family_member(member_id: int):
    with _conn() as conn:
        row = _get_member(conn, member_id)

        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                member.enabled = True
                from datetime import datetime
                member.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=row["home_id"],
            member_name=row["name"],
            severity="INFO",
            details=f"Family member {row['name']} enabled.",
            action_taken="FAMILY MEMBER ENABLED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member enabled successfully",
            "member": _member_dict(row),
        }


@router.patch("/api/family/members/{member_id}/disable")
def disable_family_member(member_id: int):
    with _conn() as conn:
        row = _get_member(conn, member_id)

        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                member.enabled = False
                from datetime import datetime
                member.updated_at = datetime.now()
                db.commit()
        finally:
            db.close()

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=row["home_id"],
            member_name=row["name"],
            severity="WARNING",
            details=f"Family member {row['name']} disabled.",
            action_taken="FAMILY MEMBER DISABLED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member disabled successfully",
            "member": _member_dict(row),
        }




@router.delete("/api/family/members")
def clear_family_members(home_id: Optional[int] = None):
    if home_id is None:
        raise HTTPException(status_code=400, detail="home_id is required.")

    with _conn() as conn:

        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            rows = db.query(FamilyMember).filter(FamilyMember.home_id == home_id).all()
            count = len(rows)
            for member in rows:
                db.delete(member)
            db.commit()
        finally:
            db.close()

        _log_family_action(
            conn,
            home_id=home_id,
            member_name="All Family Members",
            severity="WARNING",
            details=f"All family members cleared for Apartment {_home_apartment(conn, home_id)}.",
            action_taken="FAMILY MEMBERS CLEARED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "All family members deleted successfully",
            "deleted_count": count,
        }


@router.delete("/api/family/members/{member_id}")
def delete_family_member(member_id: int):
    with _conn() as conn:
        row = _get_member(conn, member_id)

        db = SessionLocal()
        try:
            from database.models.family import FamilyMember
            member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
            if member:
                db.delete(member)
                db.commit()
        finally:
            db.close()

        _log_family_action(
            conn,
            home_id=row["home_id"],
            member_name=row["name"],
            severity="WARNING",
            details=f"Family member {row['name']} deleted.",
            action_taken="FAMILY MEMBER DELETED",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member deleted successfully",
            "deleted_id": str(member_id),
        }
