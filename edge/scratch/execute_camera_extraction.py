import ast

def execute_extraction():
    with open('main.py', 'r', encoding='utf-8') as f:
        main_content = f.read()

    tree = ast.parse(main_content)
    
    handlers = {
        'cameras': '/cameras',
        'd7m16_app_cameras_real': '/api/app/cameras-real',
        'd7m16_app_camera_face_events_real': '/api/app/camera-face-events-real',
        'd7m16_fake_camera_frame': '/api/app/fake-camera-frame/{camera_id}',
        'd7m16_app_cameras_real_v2': '/api/app/cameras-real-v2',
        'd7m16_app_camera_face_events_real_v2': '/api/app/camera-face-events-real-v2'
    }
    
    helpers = [
        '_d7_cam_final_bool', '_d7_cam_final_conn', '_d7_cam_final_db_path', '_d7_cam_final_device_home_match',
        '_d7_cam_final_device_name_for_home', '_d7_cam_final_extract_member', '_d7_cam_final_find_home',
        '_d7_cam_final_format_time', '_d7_cam_final_home_code_from_apt', '_d7_cam_final_is_camera_device',
        '_d7_cam_final_log_home_match', '_d7_cam_final_png', '_d7_cam_final_stream_value', '_d7_cam_final_tables',
        '_d7_cam_final_text', '_d7_camera_bool', '_d7_camera_conn', '_d7_camera_db_path', '_d7_camera_device_home_match',
        '_d7_camera_extract_member', '_d7_camera_face_title', '_d7_camera_find_home', '_d7_camera_format_time',
        '_d7_camera_home_code_from_apt', '_d7_camera_is_camera_device', '_d7_camera_log_home_match', '_d7_camera_lower',
        '_d7_camera_stream_value', '_d7_camera_tables', '_d7_camera_text'
    ]
    
    ranges_to_remove = []
    extracted_lines = []
    
    main_lines = main_content.split('\n')
    
    print("--- TEMPORARY EXECUTION REPORT ---")
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in handlers or node.name in helpers:
                start = node.lineno
                if node.decorator_list:
                    start = min(start, min(d.lineno for d in node.decorator_list))
                end = node.end_lineno
                
                # capture the lines
                block = main_lines[start-1:end]
                
                if node.name in handlers:
                    print(f"Route: {handlers[node.name]} | Handler: {node.name} | Lines: {start}-{end}")
                    # Replace @app.get with @router.get
                    for i, line in enumerate(block):
                        if line.strip().startswith('@app.'):
                            block[i] = line.replace('@app.', '@router.')
                
                ranges_to_remove.append((start, end))
                extracted_lines.extend(block)
                extracted_lines.append("") # blank line between functions
                
    # Sort ranges in reverse to delete without offsetting
    ranges_to_remove.sort(reverse=True)
    
    for start, end in ranges_to_remove:
        del main_lines[start-1:end]
        
    # Inject router import into main.py
    # We will find the existing family_management router or similar and place it there.
    # E.g. line 1135: app.include_router(devices_router)
    for i, line in enumerate(main_lines):
        if "app.include_router(devices_router)" in line:
            main_lines.insert(i+1, "    from api.cameras import router as camera_router\n    app.include_router(camera_router)")
            break

    # Also remove orphaned imports from main.py if they were entirely wrapped in D7M16_APP_CAMERA_REAL_BINDING_START etc.
    # To be safe, we just leave them or delete the exact blocks.
    # Actually, we can just delete lines containing _d7_camera_sqlite3, _d7_camera_re, etc.
    imports_to_remove = ["_d7_camera_sqlite3", "_d7_camera_re", "_D7CameraPath", "_D7CameraQuery",
                         "_d7_cam_final_datetime", "_d7_cam_final_sqlite3", "_D7CamFinalPath", "_D7CamFinalQuery", "_d7_cam_final_re"]
    
    final_main_lines = []
    for line in main_lines:
        if any(imp in line for imp in imports_to_remove):
            continue
        final_main_lines.append(line)
        
    camera_file_content = [
        "from fastapi import APIRouter, Request, Query",
        "from fastapi.responses import HTMLResponse",
        "import sqlite3",
        "import re",
        "from datetime import datetime",
        "from pathlib import Path",
        "from core_database import _d7_find_db",
        "",
        "router = APIRouter(tags=['cameras'])",
        ""
    ]
    
    # We need to replace the alias usages inside the extracted code
    alias_replacements = {
        "_d7_camera_sqlite3": "sqlite3",
        "_d7_camera_re": "re",
        "_D7CameraPath": "Path",
        "_D7CameraQuery": "Query",
        "_d7_cam_final_datetime": "datetime",
        "_d7_cam_final_sqlite3": "sqlite3",
        "_D7CamFinalPath": "Path",
        "_D7CamFinalQuery": "Query",
        "_d7_cam_final_re": "re"
    }
    
    for line in extracted_lines:
        for alias, real_name in alias_replacements.items():
            line = line.replace(alias, real_name)
        camera_file_content.append(line)
        
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_main_lines))
        
    with open('api/cameras.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(camera_file_content))
        
    print("\nExtraction completed.")

if __name__ == '__main__':
    execute_extraction()
