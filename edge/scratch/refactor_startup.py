import ast
import shutil

MAIN_PY = 'e:/SmartHomeMobileApp/edge/main.py'
BACKUP_PY = 'e:/SmartHomeMobileApp/edge/main.py.bak4'

shutil.copy2(MAIN_PY, BACKUP_PY)

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    code = f.read()

tree = ast.parse(code)
lines_to_remove = set()

# We need to find `run_startup_migrations` specifically under the `try` block that wraps it.
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        func = node.value.func
        if isinstance(func, ast.Name):
            name = func.id
            if name in ['run_startup_migrations', 'init_database_tables', '_d7m16_normalize_bad_datetime_values_once', '_ensure_system_logs_table', '_d7_cleanup_duplicate_app_security_logs_once']:
                for i in range(node.lineno, node.end_lineno + 1):
                    lines_to_remove.add(i)
        elif isinstance(func, ast.Attribute):
            if func.attr == 'create_all' and getattr(func.value, 'attr', '') == 'metadata':
                for i in range(node.lineno, node.end_lineno + 1):
                    lines_to_remove.add(i)
    elif isinstance(node, ast.Try):
        # check if it wraps run_startup_migrations
        for stmt in node.body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                func = stmt.value.func
                if getattr(func, 'id', '') == 'run_startup_migrations':
                    # remove the entire try block!
                    for i in range(node.lineno, node.end_lineno + 1):
                        lines_to_remove.add(i)

startup_event_lineno = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'startup_event':
        startup_event_lineno = node.lineno
        break

if not startup_event_lineno:
    print("FAILED: Could not find startup_event")
    exit(1)

lines = code.splitlines()

insertion = """    # --- RELOCATED DATABASE BOOTSTRAP START ---
    try:
        run_startup_migrations()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] run_startup_migrations failed: {e}")

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] create_all failed: {e}")

    try:
        init_database_tables()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] init_database_tables failed: {e}")

    try:
        _d7m16_normalize_bad_datetime_values_once()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] datetime normalization failed: {e}")

    try:
        _ensure_system_logs_table()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] ensure_system_logs_table failed: {e}")

    try:
        _d7_cleanup_duplicate_app_security_logs_once()
    except Exception as e:
        print(f"[BOOTSTRAP ERROR] cleanup_duplicate_logs failed: {e}")
    # --- RELOCATED DATABASE BOOTSTRAP END ---
"""

final_lines = []
for i, line in enumerate(lines):
    if (i + 1) in lines_to_remove:
        continue
    
    final_lines.append(line)
    
    if (i + 1) == startup_event_lineno:
        final_lines.append(insertion)

final_code = "\n".join(final_lines) + "\n"

try:
    ast.parse(final_code)
except SyntaxError as e:
    print(f"FAILED: Syntax error after refactoring: {e}")
    shutil.copy2(BACKUP_PY, MAIN_PY)
    exit(1)

with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.write(final_code)

print("SUCCESS: Lines removed:", len(lines_to_remove))
