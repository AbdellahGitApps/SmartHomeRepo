import re
import subprocess
import tempfile
import os

def check_js_syntax():
    with open('e:/SmartHomeMobileApp/edge/dashboard/templates/devices.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, flags=re.DOTALL | re.IGNORECASE)
    
    has_errors = False
    for i, script in enumerate(script_blocks):
        # We can write the script to a temp file and check it
        fd, temp_path = tempfile.mkstemp(suffix='.js')
        with os.fdopen(fd, 'w', encoding='utf-8') as tf:
            tf.write(script)
            
        result = subprocess.run(['node', '-c', temp_path], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error in script block {i+1}:")
            print(result.stderr)
            has_errors = True
            
        os.remove(temp_path)
        
    if not has_errors:
        print("No syntax errors found in any script block.")

if __name__ == '__main__':
    check_js_syntax()
