import ast

def audit_camera_domain():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    # 1. Identify camera routes
    camera_routes = [
        "/cameras",
        "/api/app/cameras-real",
        "/api/app/camera-face-events-real",
        "/api/app/fake-camera-frame/{camera_id}",
        "/api/app/cameras-real-v2",
        "/api/app/camera-face-events-real-v2"
    ]
    
    handlers = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.value.id == 'app' and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            if path in camera_routes:
                                handlers[node.name] = {
                                    'path': path,
                                    'node': node,
                                    'start': node.lineno,
                                    'end': node.end_lineno
                                }
                                
    # Also find classes/schemas that are camera related
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if 'camera' in node.name.lower() or 'photo' in node.name.lower() or 'face' in node.name.lower():
                classes.append(node.name)
    
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

    # Calculate dependencies
    def get_deps(func_name, depth=0, max_depth=5):
        if depth > max_depth: return set()
        deps = set(func_calls.get(func_name, []))
        for d in list(deps):
            if d.startswith('_d7') or d.startswith('d7'):
                deps.update(get_deps(d, depth+1))
        return deps

    all_deps = set()
    for h in handlers:
        all_deps.update(get_deps(h))
        
    print(f"Handlers found: {list(handlers.keys())}")
    
    # Check what other endpoints call these deps to classify them
    shared = set()
    for other_func, calls in func_calls.items():
        if other_func not in handlers:
            for c in calls:
                if c in all_deps:
                    shared.add(c)
                    
    print("\nSAFE TO MOVE (Camera specific helpers):")
    for d in all_deps:
        if d not in shared and (d.startswith('_d7') or d.startswith('d7') or d == 'cameras'):
            print("-", d)
            
    print("\nSHARED (Keep in main or shared module):")
    for d in all_deps:
        if d in shared and (d.startswith('_d7') or d.startswith('d7')):
            print("-", d)
            
    print("\nPotential schemas/classes:")
    print(classes)
    
if __name__ == '__main__':
    audit_camera_domain()
