import sqlite3
import os
import glob

def main():
    db_path = "database/smart_home_edge.db"
    if not os.path.exists(db_path):
        db_path = "data/smart_home.db"
        if not os.path.exists(db_path):
            print("DB not found")
            return
            
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    
    print("Raw SQLite tables in DB:")
    for t in tables:
        print("-", t)
        
    model_files = glob.glob("database/models/*.py")
    print("\nSQLAlchemy Model Files:")
    for m in model_files:
        print("-", m)

if __name__ == '__main__':
    main()
