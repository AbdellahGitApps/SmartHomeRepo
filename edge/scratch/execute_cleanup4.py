import ast

def do_cleanup():
    handlers_to_delete = {
        'api_dashboard_logs',
        'd7_phase10_dashboard_device_action',
        '_d7m16_dashboard_edit_home',
        '_d7m16_dashboard_add_device',
        '_d7m16_final_device_action',
        '_d7m16_final_device_action_v6',
        'd7final_delete_dashboard_logs_bulk',
        'd7m16_final_delete_dashboard_security_logs_filtered',
        'd7m16_post_dashboard_logs_final_bulk'
    }

    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    ranges_to_delete = []
    
    deleted_handlers = set()
    deleted_helpers = set()
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_handler = node.name in handlers_to_delete
            is_helper = node.name.startswith('_d7_phase10_')
            
            if is_handler or is_helper:
                start = node.lineno
                if node.decorator_list:
                    start = min(start, min(d.lineno for d in node.decorator_list))
                end = node.end_lineno
                
                # Expand end line if there are blank lines or simple comments directly after
                ranges_to_delete.append((start, end))
                
                if is_handler:
                    deleted_handlers.add(node.name)
                if is_helper:
                    deleted_helpers.add(node.name)

    lines = content.split('\n')
    
    lines_to_keep = []
    for i, line in enumerate(lines, start=1):
        should_delete = False
        for start, end in ranges_to_delete:
            if start <= i <= end:
                should_delete = True
                break
        if not should_delete:
            lines_to_keep.append(line)
            
    new_content = '\n'.join(lines_to_keep)
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Removed Handlers: {len(ranges_to_delete) - len(deleted_helpers)}")
    print(f"Removed Helpers: {len(deleted_helpers)}")
    print(f"Removed Lines: {len(lines) - len(lines_to_keep)}")

if __name__ == '__main__':
    do_cleanup()
