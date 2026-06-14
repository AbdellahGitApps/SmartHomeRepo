import ast
from collections import defaultdict
import json

def analyze_main():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    line_count = len(lines)
    
    tree = ast.parse(content)
    
    function_defs = []
    class_defs = []
    routes = []
    
    func_names = defaultdict(list)
    route_paths = defaultdict(list)
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_names[node.name].append(node.lineno)
            
            # Check for route decorators
            is_route = False
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.value.id == 'app' and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        is_route = True
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = f"{decorator.func.attr.upper()} {decorator.args[0].value}"
                            route_paths[path].append(node.name)
            
            if is_route:
                routes.append(node.name)
            else:
                function_defs.append(node.name)
                
        elif isinstance(node, ast.ClassDef):
            class_defs.append(node.name)
            
    duplicate_funcs = {name: lines for name, lines in func_names.items() if len(lines) > 1}
    duplicate_routes = {path: funcs for path, funcs in route_paths.items() if len(funcs) > 1}
    
    result = {
        'main.py': {
            'line_count': line_count,
            'route_count': len(routes),
            'function_count': len(function_defs) + len(routes),
            'class_count': len(class_defs),
            'duplicate_function_definitions': duplicate_funcs,
            'duplicate_route_definitions': duplicate_routes,
        }
    }
    
    with open('scratch/analysis_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

if __name__ == '__main__':
    analyze_main()
