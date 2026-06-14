import glob
import os
import re
import json

patterns = [
    'scratch/**/*',
    '**/*.bak',
    '**/*.bak2',
    '**/*.bak3',
    '**/*.bak4',
    '**/phase*.py',
    '**/audit*.py',
    '**/check*.py',
    '**/execute*.py',
    '**/analyze*.py',
    '**/temp*.py',
    '**/cleanup*.py',
    '**/migration*.py'
]

files = set()
for pattern in patterns:
    for f in glob.glob(pattern, recursive=True):
        if os.path.isfile(f):
            files.add(f)

result = {}
for f in sorted(list(files)):
    result[f] = os.path.getsize(f)

with open('scratch/artifacts.json', 'w') as out:
    json.dump(result, out, indent=2)

print(f"Found {len(result)} files")
