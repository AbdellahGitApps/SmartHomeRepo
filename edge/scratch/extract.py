import ast
import os
import builtins

routes_to_move = [
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

helpers_to_move = [
    'normalize_time',
    '_d7final_log_item',
    '_d7final_is_door',
    '_d7final_result_label',
    '_d7_final_find_db',
    'is_door_related',
    '_d7real_log_to_app_item',
    '_d7final_text',
    '_d7final_is_energy',
    '_d7real_door_where',
    '_d7final_home_filter',
    '_d7_final_delete_by_id',
    '_d7m16_door_log_hidden',
    '_d7final_result_key',
    '_d7m16_role_text',
    '_d7final_actor',
    '_d7real_result_label'
]

targets = routes_to_move + helpers_to_move

with open('main.py', 'r', encoding='utf-8') as f:
    source_lines = f.readlines()

with open('main.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

main_globals = set(dir(builtins))
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, getattr(ast, 'AsyncFunctionDef', type(None)), ast.ClassDef)):
        main_globals.add(node.name)
    elif isinstance(node, ast.Import):
        for n in node.names: main_globals.add(n.asname or n.name)
    elif isinstance(node, ast.ImportFrom):
        for n in node.names: main_globals.add(n.asname or n.name)
    elif isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name): main_globals.add(t.id)

extracted_sources = {}
delete_ranges = []

for node in tree.body:
    if isinstance(node, (ast.FunctionDef, getattr(ast, 'AsyncFunctionDef', type(None)))) and node.name in targets:
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        end = node.end_lineno
        
        source = ''.join(source_lines[start:end])
        extracted_sources[node.name] = source
        delete_ranges.append((start, end))

for t in targets:
    if t not in extracted_sources:
        print(f"Warning: {t} not found in main.py")

delete_ranges.sort(key=lambda x: x[0], reverse=True)
new_main_lines = list(source_lines)
for start, end in delete_ranges:
    del new_main_lines[start:end]

extracted_code = []
for node in tree.body:
    if getattr(node, 'name', '') in extracted_sources:
        # Check what globals it uses that need local imports
        used_names = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                used_names.add(child.id)
                
        deps = []
        for name in used_names:
            if name in main_globals and name not in targets and name not in ['app', 'Request', 'Depends']:
                # Filter out standard libraries imported globally if they might be needed?
                # Actually, local imports of anything from edge.main is safest.
                # Only include functions/vars defined in main.py, let's just do everything not builtin
                if name not in dir(builtins) and name not in ['_D7M16_ALERT_SCOPE']:
                    deps.append(name)

        source = extracted_sources[node.name]
        
        # Rewrite @app to @router
        source = source.replace('@app.get', '@router.get')
        source = source.replace('@app.post', '@router.post')
        source = source.replace('@app.delete', '@router.delete')
        source = source.replace('@app.put', '@router.put')
        
        # Inject local imports
        if deps:
            parts = source.split(':\n', 1)
            if len(parts) == 2:
                import_stmt = f"    from edge.main import {', '.join(sorted(deps))}\n"
                source = parts[0] + ':\n' + import_stmt + parts[1]
                
        extracted_code.append(source)

door_py_content = """from fastapi import APIRouter, Request, Depends, HTTPException
import sqlite3
import json
import asyncio
from datetime import datetime

router = APIRouter()

""" + '\n'.join(extracted_code)

with open('api/door.py', 'w', encoding='utf-8') as f:
    f.write(door_py_content)

# Add router registration to main.py
registration_code = """
from api.door import router as door_router
app.include_router(door_router)
"""

# Insert before if __name__ == '__main__':
insert_idx = len(new_main_lines)
for i, line in enumerate(new_main_lines):
    if line.startswith("if __name__ =="):
        insert_idx = i
        break

new_main_lines.insert(insert_idx, registration_code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(''.join(new_main_lines))

print(f"Extracted {len(extracted_sources)} functions.")
