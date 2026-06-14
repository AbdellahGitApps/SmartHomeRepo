with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('    from api.cameras import router as camera_router\n    app.include_router(camera_router)\n', '')

target = """try:
    from api.devices import router as devices_router
    app.include_router(devices_router)
except Exception as exc:
    print(f"Devices router failed to load: {exc}")"""

new_block = """try:
    from api.devices import router as devices_router
    app.include_router(devices_router)
except Exception as exc:
    print(f"Devices router failed to load: {exc}")

try:
    from api.cameras import router as camera_router
    app.include_router(camera_router)
except Exception as exc:
    print(f"Camera router failed to load: {exc}")"""

if target in content:
    content = content.replace(target, new_block)
else:
    print("Could not find the target block")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
