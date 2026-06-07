import re

def find_errors():
    with open('e:/SmartHomeMobileApp/edge/dashboard/templates/devices.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines):
        if '="<span' in line or "='<span" in line:
            print(f"{i+1}: {line.strip()}")

if __name__ == '__main__':
    find_errors()
