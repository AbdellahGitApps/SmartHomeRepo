import ast
import re

def main():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    # Get all functions and their direct calls
    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.calls = set()
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                self.calls.add(node.func.id)
            self.generic_visit(node)

    func_calls = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor = CallVisitor()
            visitor.visit(node)
            func_calls[node.name] = list(visitor.calls)
            
    # Which functions call our helpers?
    def who_calls(target_func):
        callers = []
        for f_name, calls in func_calls.items():
            if target_func in calls:
                callers.append(f_name)
        return callers

    handlers = [
        'api_dashboard_logs',
        'd7_phase10_dashboard_device_action',
        '_d7m16_dashboard_edit_home',
        '_d7m16_dashboard_add_device',
        '_d7m16_final_device_action',
        '_d7m16_final_device_action_v6',
        'd7final_delete_dashboard_logs_bulk',
        'd7m16_final_delete_dashboard_security_logs_filtered',
        'd7m16_post_dashboard_logs_final_bulk'
    ]
    
    for h in handlers:
        print(f"Handler: {h}")
        print(f"Is handler called by anyone? {who_calls(h)}")
        helpers = func_calls.get(h, [])
        for helper in helpers:
            if helper.startswith('_') or helper.startswith('d7'):
                callers = who_calls(helper)
                callers_excluding_handlers = [c for c in callers if not c.endswith('-old') and c not in handlers and not c.endswith('_old')]
                print(f"  Helper: {helper} -> Callers: {callers}")
                
if __name__ == '__main__':
    main()
