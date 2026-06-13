import ast
import builtins
import sys

MAIN_PY = 'e:/SmartHomeMobileApp/edge/main.py'

try:
    with open(MAIN_PY, 'r', encoding='utf-8') as f:
        source_code = f.read()
except FileNotFoundError:
    print("File not found.")
    sys.exit(1)

try:
    tree = ast.parse(source_code)
except SyntaxError as e:
    print(f"SyntaxError|{e.lineno}|{e.text.strip() if e.text else ''}|{e.msg}")
    sys.exit(0)

# Gather global definitions
global_defs = set(dir(builtins))
global_defs.update({'__name__', '__file__', '__doc__', '__package__'})

class_defs = set()
func_defs = set()
imports = set()

# Pre-defined known magic or globally injected things
# FastAPI and Pydantic inject some things, but let's just gather what is explicitly defined.
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        func_defs.add(node.name)
        global_defs.add(node.name)
    elif isinstance(node, ast.AsyncFunctionDef):
        func_defs.add(node.name)
        global_defs.add(node.name)
    elif isinstance(node, ast.ClassDef):
        class_defs.add(node.name)
        global_defs.add(node.name)
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                global_defs.add(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        global_defs.add(elt.id)
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            global_defs.add(node.target.id)
    elif isinstance(node, ast.Import):
        for alias in node.names:
            global_defs.add(alias.asname or alias.name.split('.')[0])
            imports.add(alias.asname or alias.name)
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            global_defs.add(alias.asname or alias.name)
            imports.add(alias.asname or alias.name)

# Now check for unresolved references in all functions and classes
errors = []

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.locals = set()
    
    def add(self, name):
        self.locals.add(name)
        
    def resolve(self, name):
        if name in self.locals:
            return True
        if self.parent:
            return self.parent.resolve(name)
        return name in global_defs

def analyze_scope(node, current_scope):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        new_scope = Scope(current_scope)
        # Add args
        for arg in node.args.args + node.args.kwonlyargs + getattr(node.args, 'posonlyargs', []):
            new_scope.add(arg.arg)
        if node.args.vararg:
            new_scope.add(node.args.vararg.arg)
        if node.args.kwarg:
            new_scope.add(node.args.kwarg.arg)
            
        # Add local assignments
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        new_scope.add(target.id)
            elif isinstance(child, ast.AnnAssign):
                if isinstance(child.target, ast.Name):
                    new_scope.add(child.target.id)
            elif isinstance(child, ast.For):
                if isinstance(child.target, ast.Name):
                    new_scope.add(child.target.id)
                elif isinstance(child.target, ast.Tuple):
                    for elt in child.target.elts:
                        if isinstance(elt, ast.Name):
                            new_scope.add(elt.id)
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                for gen in child.generators:
                    if isinstance(gen.target, ast.Name):
                        new_scope.add(gen.target.id)
                    elif isinstance(gen.target, ast.Tuple):
                        for elt in gen.target.elts:
                            if isinstance(elt, ast.Name):
                                new_scope.add(elt.id)
            elif isinstance(child, ast.ExceptHandler):
                if child.name:
                    new_scope.add(child.name)
            elif isinstance(child, ast.NamedExpr):
                if isinstance(child.target, ast.Name):
                    new_scope.add(child.target.id)
            elif isinstance(child, ast.withitem):
                if child.optional_vars and isinstance(child.optional_vars, ast.Name):
                    new_scope.add(child.optional_vars.id)
                    
        # Check all loads
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if not new_scope.resolve(child.id):
                    # Exclude some common false positives like 'request', 'Depends' if not explicitly found, but let's record all for now.
                    errors.append({
                        'type': 'UndefinedName',
                        'symbol': child.id,
                        'lineno': child.lineno,
                        'parent': node.name
                    })

    elif isinstance(node, ast.ClassDef):
        new_scope = Scope(current_scope)
        # Check loads in class body
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                # Ignore self references as they are not resolved in class scope
                pass
                
    else:
        # Global scope statements
        pass

base_scope = Scope()
for n in tree.body:
    analyze_scope(n, base_scope)

# We will also use pylint/flake8 if they exist, but AST is safe.
import json
print(json.dumps(errors))
