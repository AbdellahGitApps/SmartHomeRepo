import ast
import os
import re

filepath = 'e:/SmartHomeMobileApp/edge/main.py'
with open(filepath, 'r', encoding='utf-8') as f:
    source_code = f.read()

tree = ast.parse(source_code)
lines = source_code.split('\n')

target_handlers = [
    'api_dashboard_logs',
    'd7_phase10_dashboard_device_action',
    '_d7m16_dashboard_edit_home',
    '_d7m16_dashboard_add_device',
    '_d7m16_final_device_action',
    '_d7m16_final_device_action_v6',
    'd7final_delete_dashboard_logs_bulk',
    'd7m16_final_delete_dashboard_security_logs_filtered',
    'd7m16_post_dashboard_logs_final_bulk'
]

endpoints = {}

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        if node.name in target_handlers:
            routes = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and hasattr(dec.func, 'attr'):
                    if dec.func.attr in ['get', 'post', 'put', 'delete']:
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            routes.append(dec.args[0].value)
            
            # Find dependencies (called functions within this file)
            calls = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                    calls.add(child.func.id)
            
            start_line = node.lineno
            end_line = getattr(node, 'end_lineno', start_line)
            length = end_line - start_line + 1
            
            if node.name not in endpoints:
                endpoints[node.name] = []
            
            endpoints[node.name].append({
                'routes': routes,
                'calls': list(calls),
                'length': length,
                'start': start_line,
                'end': end_line
            })

# Scan project for route and handler usages
project_dir = 'e:/SmartHomeMobileApp'
exts_to_check = ('.py', '.dart', '.html', '.js')

def search_project(queries):
    results = {q: [] for q in queries}
    for root, dirs, files in os.walk(project_dir):
        if 'scratch' in root or '.git' in root or 'venv' in root or '.dart_tool' in root or 'build' in root:
            continue
        for f in files:
            if f.endswith(exts_to_check):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        content = file.read()
                        for q in queries:
                            # Skip self reference in main.py
                            if path.replace('\\', '/') == filepath:
                                # We only care if it's referenced outside of its definition
                                # Simple check: count occurrences > 1 for functions, or check for exact strings
                                if q.startswith('/api/'):
                                    if content.count(q) > 0: # Wait, in main.py it's defined
                                        pass
                            else:
                                if q in content:
                                    results[q].append(path)
                except Exception:
                    pass
    return results

search_queries = []
for name, data_list in endpoints.items():
    search_queries.append(name)
    for data in data_list:
        for r in data['routes']:
            # Strip path parameters to search
            base_route = re.sub(r'\{.*?\}', '', r)
            if base_route.endswith('//'): base_route = base_route[:-1]
            if base_route:
                search_queries.append(base_route)

# Add specific queries
search_results = search_project(search_queries)

print("--- Endpoint Audit Results ---")
for name, data_list in endpoints.items():
    for data in data_list:
        print(f"Endpoint: {name}")
        print(f"Routes: {data['routes']}")
        print(f"Lines: {data['length']} ({data['start']}-{data['end']})")
        print(f"Direct Helper Calls: {data['calls']}")
        
        # Check usages
        is_used = False
        usages = []
        if search_results.get(name):
            usages.extend(search_results[name])
        for r in data['routes']:
            base_route = re.sub(r'\{.*?\}', '', r)
            if base_route.endswith('//'): base_route = base_route[:-1]
            if base_route and search_results.get(base_route):
                usages.extend(search_results[base_route])
        
        if usages:
            print(f"References Found In: {list(set(usages))}")
        else:
            print("References: NONE")
        print("-" * 40)
