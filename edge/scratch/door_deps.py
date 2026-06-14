import ast
import json
import os

door_routes = [
    'd7m16_app_door_access_logs',
    'd7m16_app_door_manual_action',
    'd7real_app_door_access_logs_real',
    'd7real_delete_app_door_access_log',
    'd7real_delete_app_door_access_logs_bulk',
    'd7final_get_door_logs',
    'd7final_delete_door_log',
    'd7final_delete_door_logs_bulk',
    'd7m16_final_delete_app_door_access_log',
    'd7m16_final_bulk_delete_app_door_access_logs',
    'd7m16_post_app_door_access_logs_final_bulk'
]

calls_map = {}
functions = {}

files_to_parse = ['main.py', 'api/notifications.py']

for filepath in files_to_parse:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, getattr(ast, 'AsyncFunctionDef', type(None)))):
                functions[node.name] = node
                calls = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            calls.add(child.func.id)
                        elif isinstance(child.func, ast.Attribute):
                            for arg in child.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    calls.add(arg.value)
                        if getattr(child.func, 'id', '') in ('getattr', 'globals', 'locals'):
                            for arg in child.args:
                                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                    calls.add(arg.value)
                    elif isinstance(child, ast.Dict):
                        for val in child.values:
                            if isinstance(val, ast.Name): calls.add(val.id)
                            elif isinstance(val, ast.Constant) and isinstance(val.value, str): calls.add(val.value)
                    
                    # ALSO check for local imports: from edge.main import _d7real_conn
                    elif isinstance(child, ast.ImportFrom):
                        for name in child.names:
                            calls.add(name.name)
                            
                calls_map[node.name] = calls

def get_all_deps(func_name, visited=None):
    if visited is None: visited = set()
    if func_name in visited or func_name not in functions: return visited
    visited.add(func_name)
    for call in calls_map.get(func_name, set()):
        if call in functions:
            get_all_deps(call, visited)
    return visited

all_door_deps = set()
for r in door_routes:
    all_door_deps.update(get_all_deps(r))

for r in door_routes:
    all_door_deps.discard(r)

safe_to_move = set()
shared_deps = set()

for dep in all_door_deps:
    is_shared = False
    for name, calls in calls_map.items():
        if name not in door_routes and name not in all_door_deps:
            if dep in calls:
                is_shared = True
                break
    if is_shared:
        shared_deps.add(dep)
    else:
        safe_to_move.add(dep)

# Also exclude common local variables misidentified as functions
locals_guess = {'label_from', 'user_from', 'as_dict', 'result_from', 'method_from', 'pick', 'cols', 'lower', 'text', 'add_item'}
safe_to_move = [s for s in safe_to_move if s not in locals_guess]
shared_deps = [s for s in shared_deps if s not in locals_guess]

res = {
    'door_routes': door_routes,
    'safe_to_move': list(safe_to_move),
    'shared_deps': list(shared_deps)
}
with open('scratch/door_deps.json', 'w') as f:
    json.dump(res, f, indent=2)

print('Deps calculated.')
