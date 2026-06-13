import ast
import shutil
import sys

MAIN_PY = 'e:/SmartHomeMobileApp/edge/main.py'
BACKUP_PY = 'e:/SmartHomeMobileApp/edge/main.py.bak3'

FUNCS_TO_DELETE = {
    'api_dashboard_security_logs_data', '_d7m16_normalize_demo_device_status',
    '_d7m16_final_device_action_v3', '_d7m16_delete_home_v3',
    '_d7m16_final_device_action_v4', '_d7m16_delete_home_v4',
    '_d7m16_delete_device_v5', '_d7m16_final_homes_lite',
    '_d7m16_r2_device_action', '_d7m16_energy_page_data_v2',
    'd7real_delete_dashboard_log', 'd7real_delete_dashboard_logs_bulk',
    'd7final_delete_dashboard_log', 'd7m16_final_delete_dashboard_security_log',
    '_d7_energy_sort_newest_v2', '_d7_r3_cols', '_d7r2_find_devices',
    '_d7_energy_find_main_db_v2', '_d7_r3_now', '_d7_r3_tables',
    '_d7_energy_power_v2', '_d7r2_event_type', '_d7_delete5_db_files',
    '_d7r2_log', '_d7_energy_db_files_v2', '_d7_energy_rows_v2',
    '_get_security_logs', '_d7_energy_device_name_v2', '_d7_energy_parse_dt_v2',
    '_d7m16_filter_dashboard_logs_list', '_d7_energy_kwh_v2', '_d7_fix4_cols',
    '_d7_energy_is_energy_device_v2', '_d7_energy_number_v2', '_d7_delete5_clean',
    '_d7_fix4_find_db', '_d7_fix4_find_device_rows', '_d7r2_clean',
    '_d7_r3_log', '_d7_energy_is_online_v2', '_d7_r3_conn',
    '_d7_energy_value_v2', '_d7_energy_collect_readings_v2', '_d7_energy_text_v2',
    '_d7_delete5_cols', '_d7_fix4_conn', '_d7_energy_forecast_v2',
    '_d7_energy_device_type_v2', '_d7r2_ensure_logs', '_d7r2_apartment',
    '_d7_energy_device_id_v2', '_d7_energy_enabled_v2', '_d7_energy_device_apartment_v2',
    '_d7_energy_timestamp_v2', '_d7_fix4_now', '_d7_r3_find_db',
    '_d7_fix4_log', '_d7_energy_time_label_v2', '_d7m16_dashboard_log_hidden',
    '_d7_r3_one_device', '_d7_delete5_tables', '_d7_r3_home_apartment',
    '_d7_fix4_clean', '_d7_fix4_apartment_for_device', '_d7_fix4_tables'
}

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    source_lines = f.readlines()
    source_code = "".join(source_lines)

try:
    tree = ast.parse(source_code)
except SyntaxError as e:
    print(f"FAILED: Initial source code has SyntaxError: {e}")
    sys.exit(1)

# VERIFICATION
global_names = set()
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        global_names.add(node.name)
    elif isinstance(node, ast.ClassDef):
        global_names.add(node.name)

# Find all active functions that are NOT in FUNCS_TO_DELETE
active_functions = set(global_names) - FUNCS_TO_DELETE
broken_deps = []

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in active_functions:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id in FUNCS_TO_DELETE:
                    broken_deps.append((node.name, child.id, child.lineno))

if broken_deps:
    print("FAILED: Verification failed! Active functions depend on functions scheduled for deletion:")
    for caller, callee, line in broken_deps:
        print(f"  {caller} calls {callee} at line {line}")
    sys.exit(1)

print("Verification passed: No active references to scheduled deletions.")

# BACKUP
shutil.copy(MAIN_PY, BACKUP_PY)
print("Backup created.")

# DELETION
lines_to_delete = set()
deleted_count = 0

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in FUNCS_TO_DELETE:
        deleted_count += 1
        start_line = node.lineno
        if node.decorator_list:
            start_line = min(d.lineno for d in node.decorator_list)
        
        for i in range(start_line - 1, node.end_lineno):
            lines_to_delete.add(i)

new_lines = []
lines_removed = 0
for i, line in enumerate(source_lines):
    if i not in lines_to_delete:
        new_lines.append(line)
    else:
        lines_removed += 1

with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# POST-DELETION VALIDATION
try:
    with open(MAIN_PY, 'r', encoding='utf-8') as f:
        new_code = f.read()
    new_tree = ast.parse(new_code)
    print("Syntax validation passed.")
except SyntaxError as e:
    print(f"FAILED: SyntaxError after deletion: {e}")
    shutil.copy(BACKUP_PY, MAIN_PY)
    sys.exit(1)

# Check for remaining functions and NameError risks
new_global_names = set()
for node in new_tree.body:
    if isinstance(node, ast.FunctionDef):
        new_global_names.add(node.name)
        
builtins = {'True', 'False', 'None', 'print', 'len', 'int', 'str', 'bool', 'float', 'list', 'dict', 'set', 'tuple', 'Exception', 'ValueError', 'TypeError', 'KeyError', 'getattr', 'hasattr', 'setattr', 'isinstance', 'enumerate', 'zip', 'sum', 'min', 'max', 'abs', 'round', 'any', 'all', 'open', 'range', 'type', 'id', 'dir', 'vars', 'super', 'issubclass', 'callable', 'sorted', 'reversed', 'BaseException', 'RuntimeError', 'bytes'}

name_errors = []
for node in ast.walk(new_tree):
    if isinstance(node, ast.FunctionDef):
        local_names = set()
        for arg in node.args.args:
            local_names.add(arg.arg)
        if node.args.vararg:
            local_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            local_names.add(node.args.kwarg.arg)
            
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        local_names.add(target.id)
            elif isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                local_names.add(child.id)
        
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                name = child.id
                if name in FUNCS_TO_DELETE:
                    name_errors.append((node.name, child.lineno, name))

if name_errors:
    print("FAILED: Post-deletion NameError risk found.")
    for caller, line, name in name_errors:
        print(f"  {caller} calls missing {name} at line {line}")
    shutil.copy(BACKUP_PY, MAIN_PY)
    sys.exit(1)
else:
    print("Reference validation passed. No NameError risks.")

print(f"Functions removed: {deleted_count}")
print(f"Lines removed: {lines_removed}")
print(f"Remaining endpoints: (Checked externally)")
print(f"Remaining function count: {len(new_global_names)}")
