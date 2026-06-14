import json
with open('scratch/dupes.json', 'r') as f:
    dupes = json.load(f)

print(f'Total duplicates found: {len(dupes)}')
for k, v in dupes.items():
    print(f'\n--- {k} ---')
    print(f'Definitions: {[d["lines"] for d in v["definitions"]]}')
    print(f'Decorators: {[d["decorators"] for d in v["definitions"]]}')
    print(f'Identical Impls: {v["identical_impls"]}')
    print(f'Identical ASTs: {v["identical_asts"]}')
    print(f'Callers: {v["callers"]}')
    print(f'Active Definition: {v["active_definition"]}')
