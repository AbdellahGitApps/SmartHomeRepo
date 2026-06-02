import re
from pathlib import Path

edge_dir = Path("d:/GitHubRepoes/SmartHomeRepo-1/edge")
main_py = edge_dir / "main.py"

print("--- AUDITING MAIN.PY ROUTES ---")
content = main_py.read_text(encoding="utf-8")

# Find all lines starting with @app
routes = []
for i, line in enumerate(content.splitlines(), 1):
    if "@app." in line:
        routes.append((i, line))

for line_num, route in routes:
    print(f"Line {line_num}: {route}")

print("\n--- AUDITING API/ ROUTERS ---")
for p in (edge_dir / "api").glob("*.py"):
    if p.name == "__init__.py":
        continue
    api_content = p.read_text(encoding="utf-8")
    api_routes = []
    for i, line in enumerate(api_content.splitlines(), 1):
        if "@router." in line:
            api_routes.append((i, line))
    if api_routes:
        print(f"File {p.name}:")
        for line_num, route in api_routes:
            print(f"  Line {line_num}: {route}")
