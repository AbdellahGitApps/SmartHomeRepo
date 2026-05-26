
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["Family Management"])


class FamilyMemberCreate(BaseModel):
    name: str = Field(..., min_length=1)
    role: str = "Family"
    home_id: int = 1
    face_enrolled: bool = False
    enabled: bool = True
    person_id: Optional[int] = None
    notes: Optional[str] = None


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    home_id: Optional[int] = None
    face_enrolled: Optional[bool] = None
    enabled: Optional[bool] = None
    person_id: Optional[int] = None
    notes: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_path() -> Path:
    edge_dir = Path(__file__).resolve().parents[1]
    return edge_dir / "database" / "smart_home_edge.db"


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
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
        """
    )

    existing = {row[1] for row in conn.execute("PRAGMA table_info(family_members)").fetchall()}
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

    for col, col_type in needed.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE family_members ADD COLUMN {col} {col_type}")

    conn.commit()


def _normalize_role(role: str | None) -> str:
    value = (role or "Family").strip().lower()

    if value in {"admin", "administrator"}:
        return "Admin"

    if value in {"guest", "visitor"}:
        return "Guest"

    return "Family"


def _member_to_dict(row: sqlite3.Row) -> dict:
    enabled = bool(row["enabled"])
    face_enrolled = bool(row["face_enrolled"])

    return {
        "id": str(row["id"]),
        "raw_id": row["id"],
        "home_id": row["home_id"],
        "name": row["name"],
        "role": row["role"],
        "face_enrolled": face_enrolled,
        "faceEnrolled": face_enrolled,
        "enabled": enabled,
        "isEnabled": enabled,
        "person_id": row["person_id"],
        "notes": row["notes"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_member(conn: sqlite3.Connection, member_id: int) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM family_members WHERE id = ?",
        (member_id,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Family member not found: {member_id}")

    return row


def _ensure_logs_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            timestamp TEXT,
            severity TEXT,
            home TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT
        )
        """
    )
    conn.commit()


def _log_family_action(
    conn: sqlite3.Connection,
    *,
    home_id: int,
    severity: str,
    details: str,
    action_taken: str,
) -> None:
    _ensure_logs_table(conn)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute(
        """
        INSERT INTO system_logs (
            created_at,
            timestamp,
            severity,
            home,
            event_type,
            details,
            action_taken
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now,
            now,
            severity,
            f"Apartment {home_id}",
            "Family Management",
            details,
            action_taken,
        ),
    )


@router.get("/api/family/status")
def family_status():
    with _connect() as conn:
        _ensure_table(conn)

        count = conn.execute("SELECT COUNT(*) AS c FROM family_members").fetchone()["c"]
        active = conn.execute(
            "SELECT COUNT(*) AS c FROM family_members WHERE enabled = 1"
        ).fetchone()["c"]
        disabled = conn.execute(
            "SELECT COUNT(*) AS c FROM family_members WHERE enabled = 0"
        ).fetchone()["c"]

        return {
            "success": True,
            "database": str(_db_path()),
            "family_members": count,
            "active_members": active,
            "disabled_members": disabled,
        }


@router.get("/api/family/members")
def list_family_members(home_id: Optional[int] = None, include_disabled: bool = True):
    with _connect() as conn:
        _ensure_table(conn)

        query = "SELECT * FROM family_members"
        params = []

        conditions = []

        if home_id is not None:
            conditions.append("home_id = ?")
            params.append(home_id)

        if not include_disabled:
            conditions.append("enabled = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC"

        rows = conn.execute(query, params).fetchall()

        return {
            "success": True,
            "count": len(rows),
            "members": [_member_to_dict(row) for row in rows],
        }


@router.post("/api/family/members")
def create_family_member(payload: FamilyMemberCreate, request: Request):
    name = payload.name.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Member name is required")

    now = _now()
    role = _normalize_role(payload.role)

    with _connect() as conn:
        _ensure_table(conn)

        cursor = conn.execute(
            """
            INSERT INTO family_members (
                home_id,
                name,
                role,
                face_enrolled,
                enabled,
                person_id,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.home_id,
                name,
                role,
                1 if payload.face_enrolled else 0,
                1 if payload.enabled else 0,
                payload.person_id,
                payload.notes,
                now,
                now,
            ),
        )

        member_id = cursor.lastrowid
        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=payload.home_id,
            severity="info",
            details=f"Family member {name} added with role {role}.",
            action_taken="Family Member Added",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member created successfully",
            "member": _member_to_dict(row),
        }


@router.patch("/api/family/members/{member_id}")
def update_family_member(member_id: int, payload: FamilyMemberUpdate):
    with _connect() as conn:
        _ensure_table(conn)
        old = _get_member(conn, member_id)

        updates = {}
        if payload.name is not None:
            name = payload.name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Member name cannot be empty")
            updates["name"] = name

        if payload.role is not None:
            updates["role"] = _normalize_role(payload.role)

        if payload.home_id is not None:
            updates["home_id"] = payload.home_id

        if payload.face_enrolled is not None:
            updates["face_enrolled"] = 1 if payload.face_enrolled else 0

        if payload.enabled is not None:
            updates["enabled"] = 1 if payload.enabled else 0

        if payload.person_id is not None:
            updates["person_id"] = payload.person_id

        if payload.notes is not None:
            updates["notes"] = payload.notes

        updates["updated_at"] = _now()

        set_sql = ", ".join([f"{key} = ?" for key in updates])
        values = list(updates.values())
        values.append(member_id)

        conn.execute(
            f"UPDATE family_members SET {set_sql} WHERE id = ?",
            values,
        )

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=row["home_id"],
            severity="info",
            details=f"Family member {row['name']} updated.",
            action_taken="Family Member Updated",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member updated successfully",
            "member": _member_to_dict(row),
        }


@router.patch("/api/family/members/{member_id}/enable")
def enable_family_member(member_id: int):
    with _connect() as conn:
        _ensure_table(conn)
        old = _get_member(conn, member_id)

        conn.execute(
            "UPDATE family_members SET enabled = 1, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=row["home_id"],
            severity="info",
            details=f"Family member {row['name']} enabled.",
            action_taken="Family Member Enabled",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member enabled successfully",
            "member": _member_to_dict(row),
        }


@router.patch("/api/family/members/{member_id}/disable")
def disable_family_member(member_id: int):
    with _connect() as conn:
        _ensure_table(conn)
        old = _get_member(conn, member_id)

        conn.execute(
            "UPDATE family_members SET enabled = 0, updated_at = ? WHERE id = ?",
            (_now(), member_id),
        )

        row = _get_member(conn, member_id)

        _log_family_action(
            conn,
            home_id=row["home_id"],
            severity="warning",
            details=f"Family member {row['name']} disabled.",
            action_taken="Family Member Disabled",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member disabled successfully",
            "member": _member_to_dict(row),
        }


@router.delete("/api/family/members/{member_id}")
def delete_family_member(member_id: int):
    with _connect() as conn:
        _ensure_table(conn)
        row = _get_member(conn, member_id)

        conn.execute("DELETE FROM family_members WHERE id = ?", (member_id,))

        _log_family_action(
            conn,
            home_id=row["home_id"],
            severity="warning",
            details=f"Family member {row['name']} deleted.",
            action_taken="Family Member Deleted",
        )

        conn.commit()

        return {
            "success": True,
            "message": "Family member deleted successfully",
            "deleted_id": member_id,
        }
