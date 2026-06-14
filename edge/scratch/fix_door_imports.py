import re
import sys
sys.path.append('e:/SmartHomeMobileApp/edge')
import main

file_path = 'e:/SmartHomeMobileApp/edge/api/door.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if 'from edge.main import ' in line or 'from main import ' in line:
        match = re.search(r'from (edge\.)?main import (.*)', line)
        if match:
            symbols_str = match.group(2)
            symbols = [s.strip() for s in symbols_str.split(',')]
            valid_symbols = []
            for s in symbols:
                if hasattr(main, s):
                    valid_symbols.append(s)
                else:
                    print(f'Line {i+1}: Removing invalid symbol {s}')
            
            if valid_symbols:
                indent = line[:len(line) - len(line.lstrip())]
                new_line = f'{indent}from main import {", ".join(valid_symbols)}\n'
                new_lines.append(new_line)
            else:
                print(f'Line {i+1}: Removing entire import line (no valid symbols)')
            continue
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done fixing api/door.py')
