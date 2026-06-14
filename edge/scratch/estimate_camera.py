import ast

def estimate_lines():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content)
    
    handlers = ['cameras', 'd7m16_app_cameras_real', 'd7m16_app_camera_face_events_real', 'd7m16_fake_camera_frame', 'd7m16_app_cameras_real_v2', 'd7m16_app_camera_face_events_real_v2']
    
    helpers = [
        '_d7_cam_final_conn', '_d7_camera_bool', '_d7_camera_stream_value', '_d7_cam_final_png',
        '_d7_cam_final_device_name_for_home', '_d7_camera_device_home_match', '_d7_cam_final_stream_value',
        '_d7_cam_final_extract_member', '_d7_cam_final_bool', '_d7_cam_final_format_time',
        '_d7_camera_is_camera_device', '_d7_camera_face_title', '_d7_camera_find_home',
        '_d7_camera_extract_member', '_d7_camera_lower', '_d7_camera_log_home_match',
        '_d7_camera_conn', '_d7_camera_format_time', '_d7_cam_final_find_home',
        '_d7_cam_final_log_home_match', '_d7_cam_final_home_code_from_apt', '_d7_camera_db_path',
        '_d7_camera_text', '_d7_camera_home_code_from_apt', '_d7_cam_final_tables',
        '_d7_camera_tables', '_d7_cam_final_device_home_match', '_d7_cam_final_db_path',
        '_d7_cam_final_text', '_d7_cam_final_is_camera_device'
    ]
    
    lines_to_remove = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in handlers or node.name in helpers:
                start = node.lineno
                if node.decorator_list:
                    start = min(start, min(d.lineno for d in node.decorator_list))
                lines_to_remove += (node.end_lineno - start + 1)

    print(f"Total lines removable: {lines_to_remove}")

if __name__ == '__main__':
    estimate_lines()
