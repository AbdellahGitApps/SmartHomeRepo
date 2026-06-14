import ast
import glob
import os
import collections
import json

files_to_check = ['main.py'] + glob.glob('api/*.py') + glob.glob('routers/*.py') + glob.glob('database/models/*.py') + ['core_database.py']
files_to_check = [f for f in files_to_check if os.path.exists(f)]

metrics = {
    'main_lines': 0,
    'main_routes': 0,
    'total_routes': 0,
    'main_funcs': 0,
    'total_funcs': 0,
    'dup_funcs': 0,
    'dup_routes': 0,
    'files': {}
}

route_paths = []

for fpath in files_to_check:
    with open(fpath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        lines = len(content.splitlines())
        
    metrics['files'][fpath] = {'lines': lines, 'routes': 0, 'funcs': 0, 'tables': [], 'is_raw': 'sqlite3' in content, 'is_orm': 'sqlalchemy' in content}
    
    if fpath == 'main.py':
        metrics['main_lines'] = lines
        
    try:
        tree = ast.parse(content)
        func_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, getattr(ast, 'AsyncFunctionDef', type(None)))):
                func_names.append(node.name)
                metrics['files'][fpath]['funcs'] += 1
                metrics['total_funcs'] += 1
                if fpath == 'main.py':
                    metrics['main_funcs'] += 1
                    
                is_route = False
                path = ''
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        is_route = True
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            path = dec.args[0].value
                
                if is_route:
                    metrics['files'][fpath]['routes'] += 1
                    metrics['total_routes'] += 1
                    if fpath == 'main.py':
                        metrics['main_routes'] += 1
                    route_paths.append(f"{node.name}:{path}")

            elif isinstance(node, ast.Call) and getattr(node.func, 'attr', '') == 'execute':
                if node.args and isinstance(node.args[0], ast.Constant):
                    sql = node.args[0].value.lower()
                    if 'from ' in sql or 'into ' in sql or 'table ' in sql or 'update ' in sql:
                        words = sql.split()
                        for i, w in enumerate(words):
                            if w in ('from', 'into', 'table', 'update') and i + 1 < len(words):
                                t = words[i+1].strip('()",;')
                                if t and t not in ('if', 'exists', 'door_events', 'face_events'):
                                    metrics['files'][fpath]['tables'].append(t)
                                    
        if fpath == 'main.py':
            c = collections.Counter(func_names)
            metrics['dup_funcs'] = sum(1 for v in c.values() if v > 1)
            
    except Exception as e:
        print(f"Error parsing {fpath}: {e}")

metrics['dup_routes'] = sum(1 for v in collections.Counter(route_paths).values() if v > 1)

with open('scratch/metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

print('Metrics calculated.')
