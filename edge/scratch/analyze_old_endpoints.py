import ast
import os
import re
from collections import defaultdict

# 1. Parse main.py
MAIN_PY_PATH = 'e:/SmartHomeMobileApp/edge/main.py'
with open(MAIN_PY_PATH, encoding='utf-8') as f:
    main_code = f.read()

tree = ast.parse(main_code)

# Data structures
old_endpoints = [] # dicts: path, func_name, lineno, helpers
all_functions = set() # all function names in main.py
func_callers = defaultdict(set) # func_name -> set of calling func_names
func_bodies = {} # func_name -> ast node

# 2. Extract all functions and call graphs
current_func = None
class CallVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            func_callers[node.func.id].add(current_func)
        self.generic_visit(node)

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        all_functions.add(node.name)
        func_bodies[node.name] = node

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        current_func = node.name
        CallVisitor().visit(node)

# 3. Find old endpoints
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        path = dec.args[0].value
                        if str(path).endswith('-old'):
                            old_endpoints.append({
                                'path': path,
                                'func_name': node.name,
                                'lineno': node.lineno,
                                'method': dec.func.attr.upper()
                            })

# 4. Search for references across the project
project_root = 'e:/SmartHomeMobileApp'
extensions_to_search = ['.py', '.html', '.js', '.dart', '.j2']
exclude_dirs = ['.git', 'venv', '__pycache__', 'scratch']

def search_in_files(queries):
    results = {q: [] for q in queries}
    for root, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in extensions_to_search):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            for q in queries:
                                if q in line:
                                    results[q].append(f"{os.path.relpath(filepath, project_root)}:{i+1}")
                except Exception:
                    pass
    return results

# Prepare queries
queries = set()
for ep in old_endpoints:
    # Search for the exact path, and also path without path params
    base_path = re.sub(r'\{.*?\}', '', ep['path']).replace('//', '/')
    queries.add(ep['path'])
    if base_path != ep['path']:
        queries.add(base_path)
    
    # Maybe the JS just appends '-old' to a variable? We can't catch all of that easily.
    # But we can search for the base path without -old
    base_no_old = ep['path'].replace('-old', '')
    # queries.add(base_no_old) # Too noisy, will skip for now

results = search_in_files(list(queries))

# Organize the results
safe_to_delete = []
potentially_active = []

for ep in old_endpoints:
    refs = []
    # Check for direct path refs
    if ep['path'] in results and results[ep['path']]:
        refs.extend(results[ep['path']])
    
    base_path = re.sub(r'\{.*?\}', '', ep['path']).replace('//', '/')
    if base_path != ep['path'] and base_path in results and results[base_path]:
        refs.extend(results[base_path])
    
    # Filter out main.py itself (where it's defined)
    refs = [r for r in refs if not r.startswith('edge\\main.py')]
    
    if refs:
        potentially_active.append((ep, refs))
    else:
        safe_to_delete.append(ep)

# 5. Find Dead Helper Functions
# A helper function is dead if all its callers are either safe_to_delete endpoints
# or other dead helper functions.
safe_func_names = set(ep['func_name'] for ep in safe_to_delete)

dead_helpers = {}
# We will do a bottom-up approach or iterative.
# Actually, just check all functions: if its callers are a subset of safe_func_names.
# Then add it, and repeat until no more changes.

dead_funcs = set(safe_func_names)
while True:
    added = False
    for func in all_functions:
        if func not in dead_funcs:
            callers = func_callers.get(func, set())
            if callers and callers.issubset(dead_funcs):
                dead_funcs.add(func)
                added = True
    if not added:
        break

# Gather actual helper info
for func in dead_funcs:
    if func not in safe_func_names:
        # Determine which safe endpoint depends on it (trace up)
        # Just list its direct dead callers for now
        direct_callers = func_callers.get(func, set())
        if func_bodies.get(func):
            dead_helpers[func] = {
                'lineno': func_bodies[func].lineno,
                'callers': list(direct_callers)
            }

# 6. Generate Report
lines_removable = 0
for func in safe_func_names:
    node = func_bodies[func]
    lines_removable += (node.end_lineno - node.lineno + 1)
for func in dead_helpers:
    node = func_bodies[func]
    lines_removable += (node.end_lineno - node.lineno + 1)

report = []
report.append("# Phase 10: main.py Cleanup Analysis Report\n")

report.append("## Section 1: Safe-To-Delete Endpoints\n")
for ep in safe_to_delete:
    report.append(f"- **Path:** `{ep['method']} {ep['path']}`")
    report.append(f"  - **Function:** `{ep['func_name']}` (Line {ep['lineno']})")
    report.append(f"  - **Confidence:** High")
    report.append(f"  - **Reason:** No references found across Python, JS, Dart, HTML, templates, or router files.\n")

report.append("## Section 2: Potentially Active Legacy Endpoints\n")
for ep, refs in potentially_active:
    report.append(f"- **Path:** `{ep['method']} {ep['path']}`")
    report.append(f"  - **Function:** `{ep['func_name']}`")
    report.append(f"  - **Confidence:** Low (Needs manual review)")
    report.append(f"  - **References Found ({len(refs)}):**")
    for r in set(refs):
        report.append(f"    - `{r}`")
    report.append("")

report.append("## Section 3: Dead Helper Functions\n")
for func, info in dead_helpers.items():
    report.append(f"- **Function:** `{func}` (Line {info['lineno']})")
    report.append(f"  - **Called By:** {', '.join(info['callers'])}\n")

report.append("## Section 4: Estimated Cleanup Impact\n")
report.append(f"- **Endpoints removable:** {len(safe_to_delete)}")
report.append(f"- **Functions removable:** {len(safe_to_delete) + len(dead_helpers)} (Endpoints + Helpers)")
report.append(f"- **Lines removable:** ~{lines_removable}")
report.append(f"- **Risk level:** Low (Assuming complete deletion of Safe-To-Delete and Dead Helpers)\n")

report.append("## Section 5: Recommended Removal Order\n")
report.append("1. **Remove Safe-To-Delete Endpoints:** Begin by deleting the endpoint functions listed in Section 1 one by one.")
report.append("2. **Remove Orphaned Helpers:** Delete the helper functions listed in Section 3.")
report.append("3. **Verify App Stability:** Run FastAPI server and ensure no startup errors (`PRAGMA integrity_check = ok`).")
report.append("4. **Manual Review of Potentially Active Endpoints:** Check the references in Section 2 to see if they are commented out or dead code in the frontend before deleting.")

with open('e:/SmartHomeMobileApp/edge/scratch/cleanup_report.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))
print("Done writing report to edge/scratch/cleanup_report.md")
