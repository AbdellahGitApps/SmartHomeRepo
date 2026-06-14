import ast

def verify_deps():
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
    
    camera_handlers = set()
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.value.id == 'app' and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            if path in camera_routes:
                                camera_handlers.add(node.name)

    # 2. Extract all calls
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

    # All defined functions in main.py
    defined_funcs = set(func_calls.keys())

    # 3. Calculate recursive dependencies for camera handlers
    def get_all_deps(start_funcs):
        deps = set()
        visited = set()
        
        def visit(f):
            if f in visited or f not in defined_funcs: return
            visited.add(f)
            deps.add(f)
            for child in func_calls.get(f, []):
                visit(child)
                
        for sf in start_funcs:
            visit(sf)
        return deps

    camera_all_deps = get_all_deps(camera_handlers)
    
    # Remove the handlers themselves from the dependency list
    camera_helpers = camera_all_deps - camera_handlers

    # 4. Check exclusivity: Who else calls these helpers?
    # For every function NOT in camera_all_deps, what does it call?
    non_camera_funcs = defined_funcs - camera_all_deps
    
    # A helper is "shared" if any non_camera_func calls it, OR if it's called by a shared helper.
    # To be precise, let's find all reachable functions from non_camera_funcs.
    non_camera_all_deps = get_all_deps(non_camera_funcs)
    
    # If a helper is in non_camera_all_deps, it MUST remain in main.py!
    safe_to_move = camera_helpers - non_camera_all_deps
    keep_in_main = camera_helpers.intersection(non_camera_all_deps)
    
    print("HANDLERS:")
    for h in sorted(camera_handlers): print("-", h)
    
    print("\nSAFE_TO_MOVE:")
    for h in sorted(safe_to_move): print("-", h)
        
    print("\nKEEP_IN_MAIN:")
    for h in sorted(keep_in_main): print("-", h)

    # Check for circular imports:
    # If camera.py imports from main.py, that's fine.
    # But if main.py imports from camera.py (it will, to register the router),
    # and camera.py imports from main.py, that is a circular import in Python!
    # FastAPI can handle it if we do local imports or register at the bottom of main.py, 
    # but the instruction says: "Stop and report if any circular import risk is detected."
    # Wait: main.py needs to import `api.cameras.router`.
    # `api.cameras` needs to import shared helpers from `edge.main`.
    # `from edge.main import ...` at the top of `api/cameras.py`.
    # If `main.py` has `from api.cameras import router` at the bottom, it works.
    # Is it a circular import risk? Yes. We must note this.
    
    # Another issue: classes/schemas used by camera_handlers.
    # Are there any?
    class TypeHintVisitor(ast.NodeVisitor):
        def __init__(self):
            self.hints = set()
        def visit_arg(self, node):
            if node.annotation:
                if isinstance(node.annotation, ast.Name):
                    self.hints.add(node.annotation.id)
            self.generic_visit(node)
            
    hints = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in camera_handlers or node.name in safe_to_move:
                visitor = TypeHintVisitor()
                visitor.visit(node.args)
                hints.update(visitor.hints)
                
    print("\nTYPE_HINTS_USED:")
    for h in sorted(hints): print("-", h)

if __name__ == '__main__':
    verify_deps()
