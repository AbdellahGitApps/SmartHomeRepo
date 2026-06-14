import ast
import builtins

def check_unresolved():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    # We want to collect all imported names, defined functions, defined classes, and global variables
    global_names = set(dir(builtins))
    
    class GlobalCollector(ast.NodeVisitor):
        def visit_Import(self, node):
            for alias in node.names:
                global_names.add(alias.asname or alias.name.split('.')[0])
        def visit_ImportFrom(self, node):
            for alias in node.names:
                global_names.add(alias.asname or alias.name)
        def visit_FunctionDef(self, node):
            global_names.add(node.name)
        def visit_AsyncFunctionDef(self, node):
            global_names.add(node.name)
        def visit_ClassDef(self, node):
            global_names.add(node.name)
        def visit_Assign(self, node):
            # Very simplistic global assignment tracking
            for target in node.targets:
                if isinstance(target, ast.Name):
                    global_names.add(target.id)

    GlobalCollector().visit(tree)
    
    # Very crude unresolved check: just check if Name(ctx=Load()) exists in locals/globals
    # Since doing a real scope analysis is hard, we just look for calls to non-existent functions.
    class CallChecker(ast.NodeVisitor):
        def __init__(self):
            self.unresolved = set()
            
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                if node.func.id not in global_names:
                    # check if it's a known exception or local
                    self.unresolved.add(node.func.id)
            self.generic_visit(node)

    checker = CallChecker()
    checker.visit(tree)
    
    # Filter out common locals or args that might trigger false positives since we don't do full scope analysis
    filtered = []
    for u in checker.unresolved:
        if u.startswith('_d7') or u.startswith('d7'):
            filtered.append(u)
            
    print("Potentially unresolved D7 helpers:")
    print(filtered)

if __name__ == '__main__':
    check_unresolved()
