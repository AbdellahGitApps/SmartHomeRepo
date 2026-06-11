import sqlite3

conn = sqlite3.connect("database/smart_home_edge.db")
cur = conn.cursor()

tables = cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

for t in tables:
    table = t[0]

    try:
        fks = cur.execute(
            f"PRAGMA foreign_key_list({table})"
        ).fetchall()

        for fk in fks:
            if fk[2] == "homes":
                print(table, "->", fk)

    except Exception:
        pass

conn.close()