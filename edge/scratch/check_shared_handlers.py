import ast

def check_handlers():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    # Map function names to their decorators' paths
    handler_routes = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            paths = []
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.value.id == 'app' and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            paths.append(decorator.args[0].value)
            if paths:
                if node.name not in handler_routes:
                    handler_routes[node.name] = []
                handler_routes[node.name].append({
                    'paths': paths,
                    'start': node.lineno,
                    'end': node.end_lineno
                })

    for name, definitions in handler_routes.items():
        for i, def_info in enumerate(definitions):
            has_old = any(str(p).endswith('-old') for p in def_info['paths'])
            has_active = any(not str(p).endswith('-old') for p in def_info['paths'])
            if has_old:
                print(f"Function {name} (Def {i}, lines {def_info['start']}-{def_info['end']}):")
                print(f"  Old routes: {[p for p in def_info['paths'] if str(p).endswith('-old')]}")
                print(f"  Active routes: {[p for p in def_info['paths'] if not str(p).endswith('-old')]}")

if __name__ == '__main__':
    check_handlers()
