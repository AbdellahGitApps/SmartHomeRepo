
from datetime import datetime
from pathlib import Path
from typing import Optional
import sqlite3

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


class FamilyMemberUpdate(BaseModel):
    home_id: Optional[int] = None
    name: Optional[str] = None
    role: Optional[str] = "Family"
    face_enrolled: Optional[bool] = None
    enabled: Optional[bool] = None
    notes: Optional[str] = None


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


def _ensure_family_table(conn):
    conn.execute("""
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
    """)

    needed = {
        "home_id": "INTEGER DEFAULT 1",
        "name": "TEXT",
        "role": "TEXT DEFAULT 'Family'",
        "face_enrolled": "INTEGER DEFAULT 0",
        "enabled": "INTEGER DEFAULT 1",
        "person_id": "INTEGER",
        "notes": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    cols = _cols(conn, "family_members")
    for col, col_type in needed.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE family_members ADD COLUMN {col} {col_type}")

    conn.commit()


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


def _member_dict(row):
    data = dict(row)
    return {
        **data,
        "id": str(data.get("id") or ""),
        "raw_id": data.get("id"),
        "name": str(data.get("name") or "Unknown"),
        "role": "Family",
        "face_enrolled": _bool(data.get("face_enrolled")),
        "faceEnrolled": _bool(data.get("face_enrolled")),
        "enabled": _bool(data.get("enabled"), True),
        "isEnabled": _bool(data.get("enabled"), True),
        "created_at": data.get("created_at") or "",
        "createdAt": data.get("created_at") or "",
        "updated_at": data.get("updated_at") or "",
        "updatedAt": data.get("updated_at") or "",
    }


def _get_member(conn, member_id):
    row = conn.execute(
        "SELECT * FROM family_members WHERE CAST(id AS TEXT) = CAST(? AS TEXT) LIMIT 1",
        (str(member_id),),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Family member not found: {member_id}")

    return row


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
        }


@router.get("/api/family/members")
def list_family_members(home_id: Optional[int] = None, include_disabled: bool = True):
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

        return {
            "success": True,
            "members": [_member_dict(row) for row in rows],
        }


@router.post("/api/family/members")
def create_family_member(payload: FamilyMemberCreate, request: Request):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Member name is required.")

    role = _family_role(payload.role)
    now = _now()
    home_id = payload.home_id or 1
    face_enrolled = 1 if payload.face_enrolled else 0
    enabled = 1 if payload.enabled else 0

    with _conn() as conn:
        _ensure_family_table(conn)

        conn.execute("""
            INSERT INTO family_members (
                home_id,
                name,
                role,
                face_enrolled,
                enabled,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            home_id,
            name,
            role,
            face_enrolled,
            enabled,
            payload.notes or "",
            now,
            now,
        ))

        member_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
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
            "member": _member_dict(row),
        }


@router.patch("/api/family/members/{member_id}")
def update_family_member(member_id: int, payload: FamilyMemberUpdate):
    with _conn() as conn:
        _ensure_family_table(conn)
        old = _get_member(conn, member_id)

        name = (payload.name if payload.name is not None else old["name"]).strip()
        if not name:
            raise HTTPException(status_code=400, detail="Member name is required.")

        role = "Family"
        face_enrolled = old["face_enrolled"] if payload.face_enrolled is None else (1 if payload.face_enrolled else 0)
        enabled = old["enabled"] if payload.enabled is None else (1 if payload.enabled else 0)
        home_id = payload.home_id if payload.home_id is not None else old["home_id"]
        notes = payload.notes if payload.notes is not None else old["notes"]

        conn.execute("""
            UPDATE family_members
            SET home_id = ?,
                name = ?,
                role = ?,
                face_enrolled = ?,
                enabled = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            home_id,
            name,
            role,
            face_enrolled,
            enabled,
            notes or "",
            _now(),
            member_id,
        ))

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

        return {
            "success": True,
            "message": "Family member updated successfully",
            "member": _member_dict(row),
        }


@router.patch("/api/family/members/{member_id}/enable")
def enable_family_member(member_id: int):
    with _conn() as conn:
        _ensure_family_table(conn)
        row = _get_member(conn, member_id)

        conn.execute(
            "UPDATE family_members SET enabled = 1, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )

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
        _ensure_family_table(conn)
        row = _get_member(conn, member_id)

        conn.execute(
            "UPDATE family_members SET enabled = 0, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )

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
        _ensure_family_table(conn)

        rows = conn.execute(
            "SELECT * FROM family_members WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)",
            (str(home_id),),
        ).fetchall()

        count = len(rows)

        conn.execute(
            "DELETE FROM family_members WHERE CAST(home_id AS TEXT) = CAST(? AS TEXT)",
            (str(home_id),),
        )

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
        _ensure_family_table(conn)
        row = _get_member(conn, member_id)

        conn.execute("DELETE FROM family_members WHERE id = ?", (member_id,))

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
