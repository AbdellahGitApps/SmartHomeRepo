import re

def refactor_backend():
    # REFACTOR routers/dashboard.py
    with open('e:/SmartHomeMobileApp/edge/routers/dashboard.py', 'r', encoding='utf-8') as f:
        code = f.read()

    obsolete_paths = [
        "/final-devices/",
        "/final-devices-v3/",
        "/final-devices-v4/",
        "/final-devices-v6/",
        "/d7-final-device-action/",
        "/d7r2-device-action/",
        "/final-devices-v5/",
        "/final-devices/normalize-demo-status"
    ]

    # Split the file by router decorators
    # We will keep the preamble before the first @router
    blocks = re.split(r'(?=@router\.(?:get|post|put|delete)\()', code)
    
    new_blocks = [blocks[0]] # preamble
    
    for block in blocks[1:]:
        # extract the route path
        match = re.search(r'@router\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)', block)
        if match:
            path = match.group(1)
            is_obsolete = any(path.startswith(obs) for obs in obsolete_paths)
            if not is_obsolete:
                new_blocks.append(block)
        else:
            new_blocks.append(block)

    with open('e:/SmartHomeMobileApp/edge/routers/dashboard.py', 'w', encoding='utf-8') as f:
        f.write("".join(new_blocks))
        
    print("Cleaned routers/dashboard.py")

    # REFACTOR main.py
    with open('e:/SmartHomeMobileApp/edge/main.py', 'r', encoding='utf-8') as f:
        main_code = f.read()

    blocks_main = re.split(r'(?=@app\.(?:get|post|put|delete)\()', main_code)
    
    new_main_blocks = [blocks_main[0]]
    removed_count = 0
    
    for block in blocks_main[1:]:
        match = re.search(r'@app\.(?:get|post|put|delete)\([\'"]([^\'"]+)[\'"]\)', block)
        if match:
            path = match.group(1)
            # Remove any path ending with "-old" inside /api/dashboard
            if path.startswith("/api/dashboard") and path.endswith("-old"):
                removed_count += 1
                continue
        new_main_blocks.append(block)

    with open('e:/SmartHomeMobileApp/edge/main.py', 'w', encoding='utf-8') as f:
        f.write("".join(new_main_blocks))
        
    print(f"Cleaned main.py (Removed {removed_count} -old legacy routes)")

if __name__ == '__main__':
    refactor_backend()
