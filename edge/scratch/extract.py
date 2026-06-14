import ast

routes = [
    'd7real_get_app_alerts',
    'd7real_resolve_alert',
    'd7real_hide_alert',
    'd7real_clear_alerts',
    'd7final_get_alerts',
    'd7final_clear_alerts',
    'd7final_resolve_alert',
    'd7final_hide_alert'
]

helpers_to_move = [
    '_d7real_ensure_alert_table',
    '_d7real_cols',
    '_d7final_alerts_for_home',
    '_d7real_state',
    '_d7m16_role_text',
    '_d7real_tables',
    '_d7real_alert_item'
]

with open('main.py', 'r', encoding='utf-8') as f:
    tree = ast.parse(f.read())

to_extract = []
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in routes + helpers_to_move:
        start = node.lineno - 1
        if node.decorator_list:
            start = node.decorator_list[0].lineno - 1
        to_extract.append({
            'name': node.name,
            'start': start,
            'end': node.end_lineno
        })

for item in to_extract:
    print(f"{item['name']}: {item['start']+1}-{item['end']}")
