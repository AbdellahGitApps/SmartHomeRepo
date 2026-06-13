import ast

with open('e:/SmartHomeMobileApp/edge/main.py', encoding='utf-8') as f:
    code = f.read()

tree = ast.parse(code)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if dec.func.attr in ['get', 'post', 'put', 'delete', 'patch']:
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        path = dec.args[0].value
                        if path.endswith('-old'):
                            print(f"{path} | {node.name} | {node.lineno}")
