import ast
import re
import os
import glob
from collections import defaultdict

def analyze_old_endpoints():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    old_endpoints = []
    # 1. Find the handlers and their routes
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                    if decorator.func.value.id == 'app' and decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                            if str(path).endswith('-old'):
                                old_endpoints.append({
                                    'route': f"{decorator.func.attr.upper()} {path}",
                                    'handler': node.name,
                                    'node': node
                                })
                                
    # 2. Extract direct function calls from handlers
    class CallVisitor(ast.NodeVisitor):
        def __init__(self):
            self.calls = set()
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                self.calls.add(node.func.id)
            self.generic_visit(node)
            
    handler_calls = {}
    for ep in old_endpoints:
        visitor = CallVisitor()
        visitor.visit(ep['node'])
        handler_calls[ep['handler']] = list(visitor.calls)

    # Output structure
    print("Old Endpoints and Direct Calls:")
    for ep in old_endpoints:
        print(f"Route: {ep['route']}")
        print(f"Handler: {ep['handler']}")
        print(f"Direct Calls: {handler_calls[ep['handler']]}")
        print("-" * 40)

if __name__ == '__main__':
    analyze_old_endpoints()
