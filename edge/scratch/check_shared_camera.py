import ast

def check_shared():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    handlers = ['cameras', 'd7m16_app_cameras_real', 'd7m16_app_camera_face_events_real', 'd7m16_fake_camera_frame', 'd7m16_app_cameras_real_v2', 'd7m16_app_camera_face_events_real_v2']
    
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

    shared_helpers = [
        '_d7_cam_final_home_code_from_apt',
        '_d7_camera_db_path',
        '_d7_camera_text',
        '_d7_camera_home_code_from_apt',
        '_d7_table_names',
        '_d7_db_candidates',
        '_d7_find_db',
        '_d7_cam_final_tables',
        '_d7_camera_tables',
        '_d7_cam_final_device_home_match',
        '_d7_cam_final_db_path',
        '_d7_cam_final_text',
        '_d7_cam_final_is_camera_device'
    ]

    for h in shared_helpers:
        callers = []
        for func, calls in func_calls.items():
            if h in calls and func not in handlers and not func.startswith('_d7_cam') and not func.startswith('_d7_camera'):
                callers.append(func)
        print(f"{h}: called outside by: {callers}")

if __name__ == '__main__':
    check_shared()
