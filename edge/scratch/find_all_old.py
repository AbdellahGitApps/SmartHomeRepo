import re

with open('e:/SmartHomeMobileApp/edge/main.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '-old"' in line or "-old'" in line:
        print(f"Line {i+1}: {line.strip()}")
