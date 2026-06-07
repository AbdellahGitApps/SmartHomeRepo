def find_line():
    with open('e:/SmartHomeMobileApp/edge/routers/dashboard.py', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if '@router.post("/devices/{device_id}/actions/{action}")' in line:
                print(f"Line number: {i+1}")
                return

if __name__ == '__main__':
    find_line()
