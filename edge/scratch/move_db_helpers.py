import ast

def execute_relocation():
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()
        
    with open('core_database.py', 'r', encoding='utf-8') as f:
        core_content = f.read()

    # The exact block to cut from main.py
    block_to_cut = """def _d7_db_candidates():
    base = _D7Path(__file__).resolve().parent
    candidates = [
        base / "database" / "smart_home_edge.db",
        base / "data" / "smart_home.db",
        base.parent / "data" / "smart_home.db",
        base / "ai" / "smart_home_models.db",
        base / "smart_home.db",
    ]
    for p in base.rglob("*.db"):
        if "__pycache__" not in str(p):
            candidates.append(p)

    clean = []
    for p in candidates:
        if p not in clean:
            clean.append(p)
    return clean

def _d7_table_names(conn):
    try:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    except Exception:
        return set()

def _d7_find_db():
    fallback = None
    for p in _d7_db_candidates():
        if not p.exists():
            continue
        fallback = p
        try:
            conn = _d7_sqlite3.connect(str(p))
            tables = _d7_table_names(conn)
            conn.close()
            if "homes" in tables and "devices" in tables:
                return p
        except Exception:
            pass
    return fallback"""

    if block_to_cut not in main_content:
        print("Error: Could not find exact block in main.py")
        return

    # Replace the block with an import statement
    import_stmt = "from core_database import _d7_db_candidates, _d7_find_db, _d7_table_names"
    new_main_content = main_content.replace(block_to_cut, import_stmt)
    
    # We must patch the cut block so it works in core_database.py
    # Change _D7Path to Path, and _d7_sqlite3 to sqlite3
    patched_block = block_to_cut.replace("_D7Path", "Path").replace("_d7_sqlite3", "sqlite3")
    
    # Append to core_database.py
    new_core_content = core_content + "\n\n# Relocated from main.py Phase 26A.2\n" + patched_block + "\n"
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_main_content)
        
    with open('core_database.py', 'w', encoding='utf-8') as f:
        f.write(new_core_content)
        
    print(f"Removed {len(block_to_cut.splitlines())} lines from main.py")
    print(f"Added {len(patched_block.splitlines()) + 3} lines to core_database.py")
    print("Relocation completed.")

if __name__ == '__main__':
    execute_relocation()
