import ast

MAIN_PY = 'e:/SmartHomeMobileApp/edge/main.py'

with open(MAIN_PY, 'r', encoding='utf-8') as f:
    source_code = f.read()

tree = ast.parse(source_code)

# Get all defined names at global scope
global_names = set()
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        global_names.add(node.name)
    elif isinstance(node, ast.ClassDef):
        global_names.add(node.name)
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                global_names.add(target.id)
    elif isinstance(node, ast.Import):
        for alias in node.names:
            global_names.add(alias.asname or alias.name)
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            global_names.add(alias.asname or alias.name)

# Some builtins and globals not caught above
builtins = {'True', 'False', 'None', 'print', 'len', 'int', 'str', 'bool', 'float', 'list', 'dict', 'set', 'tuple', 'Exception', 'ValueError', 'TypeError', 'KeyError', 'getattr', 'hasattr', 'setattr', 'isinstance', 'enumerate', 'zip', 'sum', 'min', 'max', 'abs', 'round', 'any', 'all', 'open', 'range', 'type', 'id', 'dir', 'vars', 'super', 'issubclass', 'callable', 'sorted', 'reversed'}

broken_references = []

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        # We check names used inside the function
        # A simple check: if a Name is Load context, and not in builtins, and not in global_names, and not a local var/arg
        
        # Gather locals
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
        
        # Find broken
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                name = child.id
                if name not in builtins and name not in global_names and name not in local_names:
                    # check if it's an imported module member
                    broken_references.append((node.name, child.lineno, name))

# Filter for the specific functions we deleted
deleted_funcs = {
    '_d7_pairing_code', '_d7_members_count', '_d7_device_public', 
    '_d7_home_summary', '_d7_clean_log_details', '_d7_all_logs', 
    '_d7_door_status_from_logs', '_d7_home_name', '_d7_status_online', 
    '_d7_is_energy_device', '_d7_sort_oldest', '_d7_log_home_matches', 
    '_d7_is_door_device', '_d7_sort_newest', '_d7_timestamp', 
    '_d7_device_name', '_d7_registered_at', '_d7_recent_access_for_home', 
    '_d7_enabled', '_d7_latest_energy_for_home', 
    '_d7m16_dashboard_home_overview_data', '_d7m16_dashboard_home_details_data'
}

actual_broken = [b for b in broken_references if b[2] in deleted_funcs]

if actual_broken:
    print("Found Broken References:")
    for func, line, name in actual_broken:
        print(f"Function {func} at line {line} calls missing function: {name}")
else:
    print("No Broken References Found. NameError risk is 0.")
