import ast

MAIN_PY = 'e:/SmartHomeMobileApp/edge/main.py'
FUNCS_TO_DELETE = {
    '_d7_pairing_code', '_d7_members_count', '_d7_device_public', 
    '_d7_home_summary', '_d7_clean_log_details', '_d7_all_logs', 
    '_d7_door_status_from_logs', '_d7_home_name', '_d7_status_online', 
    '_d7_is_energy_device', '_d7_sort_oldest', '_d7_log_home_matches', 
    '_d7_is_door_device', '_d7_sort_newest', '_d7_timestamp', 
    '_d7_device_name', '_d7_registered_at', '_d7_recent_access_for_home', 
    '_d7_enabled', '_d7_latest_energy_for_home', 
    '_d7m16_dashboard_home_overview_data', '_d7m16_dashboard_home_details_data'
}

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    source_lines = f.readlines()
    source_code = "".join(source_lines)

tree = ast.parse(source_code)

lines_to_delete = set()
deleted_functions = set()

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name in FUNCS_TO_DELETE:
        deleted_functions.add(node.name)
        
        # Determine start line including decorators
        start_line = node.lineno
        if node.decorator_list:
            start_line = min(d.lineno for d in node.decorator_list)
            
        end_line = node.end_lineno
        
        for i in range(start_line - 1, end_line):
            lines_to_delete.add(i)

print(f"Identified {len(deleted_functions)} out of {len(FUNCS_TO_DELETE)} functions to delete.")

new_lines = []
lines_removed_count = 0
for i, line in enumerate(source_lines):
    if i not in lines_to_delete:
        new_lines.append(line)
    else:
        lines_removed_count += 1

with open(MAIN_PY, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Successfully deleted {lines_removed_count} lines.")
