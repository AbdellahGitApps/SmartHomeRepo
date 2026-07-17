import sqlite3
import json

db_path = "e:/SmartHomeMobileApp/edge/database/smart_home_edge.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

if ('system_logs',) in tables:
    cur.execute("SELECT id, timestamp, action_taken, details FROM system_logs ORDER BY id DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)
else:
    print("No system_logs table found")
