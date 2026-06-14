import ast

def verify_shared_deep():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
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

    target_helpers = ['_d7_device_db', '_d7_camera_db_path', '_d7_cam_final_db_path', '_d7_rows', '_d7_device_log', '_d7_get_device_row']
    
    results = {h: [] for h in target_helpers}
    
    for caller, calls in func_calls.items():
        for target in target_helpers:
            if target in calls:
                results[target].append(caller)
                
    for h in target_helpers:
        print(f"Callers of {h}: {results[h]}")

if __name__ == '__main__':
    verify_shared_deep()
