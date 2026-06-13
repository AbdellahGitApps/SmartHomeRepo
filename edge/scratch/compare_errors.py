import ast
import builtins
import sys

def get_errors(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except FileNotFoundError:
        return []

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return [{"type": "SyntaxError", "lineno": e.lineno}]

    global_defs = set(dir(builtins))
    global_defs.update({'__name__', '__file__', '__doc__', '__package__'})
    
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            global_defs.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name): global_defs.add(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name): global_defs.add(elt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            global_defs.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names: global_defs.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names: global_defs.add(alias.asname or alias.name)

    errors = []

    class Scope:
        def __init__(self, parent=None):
            self.parent = parent
            self.locals = set()
        def add(self, name): self.locals.add(name)
        def resolve(self, name):
            if name in self.locals: return True
            if self.parent: return self.parent.resolve(name)
            return name in global_defs

    def analyze_scope(node, current_scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            new_scope = Scope(current_scope)
            for arg in getattr(node.args, 'posonlyargs', []) + node.args.args + getattr(node.args, 'kwonlyargs', []):
                new_scope.add(arg.arg)
            if node.args.vararg: new_scope.add(node.args.vararg.arg)
            if node.args.kwarg: new_scope.add(node.args.kwarg.arg)
                
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name): new_scope.add(target.id)
                elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                    new_scope.add(child.target.id)
                elif isinstance(child, ast.For):
                    if isinstance(child.target, ast.Name): new_scope.add(child.target.id)
                    elif isinstance(child.target, ast.Tuple):
                        for elt in child.target.elts:
                            if isinstance(elt, ast.Name): new_scope.add(elt.id)
                elif isinstance(child, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                    for gen in child.generators:
                        if isinstance(gen.target, ast.Name): new_scope.add(gen.target.id)
                        elif isinstance(gen.target, ast.Tuple):
                            for elt in gen.target.elts:
                                if isinstance(elt, ast.Name): new_scope.add(elt.id)
                elif isinstance(child, ast.ExceptHandler) and child.name:
                    new_scope.add(child.name)
                elif isinstance(child, ast.NamedExpr) and isinstance(child.target, ast.Name):
                    new_scope.add(child.target.id)
                elif isinstance(child, ast.withitem) and child.optional_vars and isinstance(child.optional_vars, ast.Name):
                    new_scope.add(child.optional_vars.id)
                        
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                    if not new_scope.resolve(child.id):
                        errors.append(f"{node.name}:{child.id}")
        
    base_scope = Scope()
    for n in tree.body:
        analyze_scope(n, base_scope)
        
    return errors

errors_new = get_errors('e:/SmartHomeMobileApp/edge/main.py')
errors_old = get_errors('e:/SmartHomeMobileApp/edge/main.py.bak')

new_set = set(errors_new)
old_set = set(errors_old)

diff = new_set - old_set
diff_removed = old_set - new_set

print("New Errors Introduced:")
for d in diff:
    print(" ", d)

print(f"\nTotal existing errors remaining: {len(new_set - diff)}")
print(f"Errors removed (due to deleted code): {len(diff_removed)}")
