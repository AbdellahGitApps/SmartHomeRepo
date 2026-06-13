import ast
import os
from collections import defaultdict

filepath = 'e:/SmartHomeMobileApp/edge/main.py'

with open(filepath, 'r', encoding='utf-8') as f:
    source_code = f.read()

tree = ast.parse(source_code)
lines = source_code.split('\n')
total_lines = len(lines)

functions = []
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
        decorators = [ast.unparse(d) for d in node.decorator_list]
        is_endpoint = any(d.startswith('app.') or d.startswith('@app.') or '.get(' in d or '.post(' in d or '.put(' in d or '.delete(' in d for d in decorators)
        
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        length = end_line - start_line + 1
        
        functions.append({
            'name': node.name,
            'is_endpoint': is_endpoint,
            'decorators': decorators,
            'start': start_line,
            'end': end_line,
            'length': length
        })

# Domains
def classify_domain(name, decorators):
    name_lower = name.lower()
    decs_lower = " ".join(decorators).lower()
    full_text = name_lower + " " + decs_lower
    
    if any(k in full_text for k in ['door', 'unlock']): return 'Door'
    if any(k in full_text for k in ['family', 'member']): return 'Family'
    if any(k in full_text for k in ['camera', 'webrtc', 'stream', 'snapshot']): return 'Camera'
    if any(k in full_text for k in ['face', 'recognition']): return 'Face Recognition'
    if any(k in full_text for k in ['alert', 'notification']): return 'Alerts'
    if any(k in full_text for k in ['auth', 'login', 'token', 'admin', 'password']): return 'Authentication'
    if any(k in full_text for k in ['energy', 'battery', 'power', 'consumption']): return 'Energy'
    if any(k in full_text for k in ['dashboard', 'home_status', 'home']): return 'Dashboard'
    if any(k in full_text for k in ['mqtt', 'system', 'startup', 'shutdown', 'database', 'log']): return 'MQTT/System'
    
    return 'Unknown/Misc'

domains = defaultdict(lambda: {'endpoints': 0, 'helpers': 0, 'lines': 0, 'ranges': []})
long_functions = []
old_endpoints = []
all_endpoints = []

for func in functions:
    dom = classify_domain(func['name'], func['decorators'])
    if func['is_endpoint']:
        domains[dom]['endpoints'] += 1
        all_endpoints.append(func)
        if '-old' in " ".join(func['decorators']):
            old_endpoints.append(func)
    else:
        domains[dom]['helpers'] += 1
        
    domains[dom]['lines'] += func['length']
    domains[dom]['ranges'].append((func['start'], func['end']))
    
    if func['length'] > 100:
        long_functions.append(func)

print(f"Total Lines in main.py: {total_lines}")
print("\n--- Domain Classification ---")
for dom, stats in domains.items():
    ranges_str = ", ".join([f"{r[0]}-{r[1]}" for r in stats['ranges'][:3]]) + ("..." if len(stats['ranges'])>3 else "")
    print(f"{dom}:")
    print(f"  Endpoints: {stats['endpoints']}")
    print(f"  Helpers: {stats['helpers']}")
    print(f"  Total Lines: {stats['lines']}")
    print(f"  Ranges: {ranges_str}")

print("\n--- Long Functions (>100 lines) ---")
for func in sorted(long_functions, key=lambda x: x['length'], reverse=True)[:10]:
    print(f"{func['name']} ({func['length']} lines) - {classify_domain(func['name'], func['decorators'])}")

print("\n--- Remaining '-old' Endpoints ---")
for ep in old_endpoints:
    print(f"{ep['name']} ({ep['decorators']})")

# Let's count some potential safe deletes/moves
# Helpers with _d7 or _d7m16 that are duplicates or unreferenced are candidates.
print("\n--- Rough Estimations ---")
movable = sum(stats['lines'] for dom, stats in domains.items() if dom != 'MQTT/System' and dom != 'Unknown/Misc')
removable = sum(f['length'] for f in old_endpoints)
print(f"Movable Lines (to Routers): ~{movable}")
print(f"Removable Lines (old endpoints/dead code): ~{removable}")
print(f"Resulting main.py size: ~{total_lines - movable - removable}")
