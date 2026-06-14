import ast
from collections import defaultdict
import json

with open('main.py', 'r', encoding='utf-8') as f:
    source_lines = f.readlines()

with open('main.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

functions = defaultdict(list)
callers_map = defaultdict(set)

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        end = node.end_lineno
        
        source = ''.join(source_lines[start:end])
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                decorators.append(f'@{dec.func.value.id}.{dec.func.attr}')
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(f'@{dec.func.id}')
            elif isinstance(dec, ast.Attribute):
                decorators.append(f'@{dec.value.id}.{dec.attr}')
            elif isinstance(dec, ast.Name):
                decorators.append(f'@{dec.id}')
                
        functions[node.name].append({
            'start': start + 1,
            'end': end,
            'source': source,
            'decorators': decorators,
            'ast_dump': ast.dump(node, annotate_fields=False)
        })
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                callers_map[child.func.id].add(node.name)

duplicates = {}
for name, defs in functions.items():
    if len(defs) > 1:
        duplicates[name] = defs

res = {}
for name, defs in duplicates.items():
    res[name] = {
        'definitions': [
            {
                'lines': f"{d['start']}-{d['end']}",
                'decorators': d['decorators']
            }
            for d in defs
        ],
        'callers': list(callers_map.get(name, set())),
        'active_definition': f"{defs[-1]['start']}-{defs[-1]['end']}",
        'identical_impls': len(set(d['source'] for d in defs)) == 1,
        'identical_asts': len(set(d['ast_dump'] for d in defs)) == 1,
        'shadowed': True,
    }

with open('scratch/dupes.json', 'w', encoding='utf-8') as f:
    json.dump(res, f, indent=2)

print('Dumped successfully.')
