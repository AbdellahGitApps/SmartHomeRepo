import re

def audit_backend():
    print('=== routers/dashboard.py Endpoints ===')
    with open('e:/SmartHomeMobileApp/edge/routers/dashboard.py', 'r', encoding='utf-8') as f:
        backend = f.read()
    routes = re.findall(r'@router\.(get|post|put|delete)\([\'"]([^\'"]+)[\'"]', backend)
    for m, r in routes:
        print(f'{m.upper()} {r}')
        
    print('\n=== main.py API Endpoints ===')
    with open('e:/SmartHomeMobileApp/edge/main.py', 'r', encoding='utf-8') as f:
        main_py = f.read()
    routes2 = re.findall(r'@app\.(get|post|put|delete)\([\'"](/api/dashboard[^\'"]+)[\'"]', main_py)
    for m, r in routes2:
        print(f'{m.upper()} {r}')

if __name__ == '__main__':
    audit_backend()
