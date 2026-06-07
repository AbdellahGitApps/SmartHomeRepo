import re
import sys

def audit_devices_html():
    try:
        with open('e:/SmartHomeMobileApp/edge/dashboard/templates/devices.html', 'r', encoding='utf-8') as f:
            html = f.read()
    except Exception as e:
        print("Error reading devices.html:", e)
        return

    print('=== A) Duplicate Function Definitions ===')
    targets = ['showToast', 'toast', 'showBlueToast', 'd7m16SendRestartCommand', 'd7m16ResolveDeviceId', 'mockRemoveDevice', 'mockToggleDeviceStatus', 'restartDevice', 'enableDevice', 'disableDevice']
    for t in targets:
        matches = list(re.finditer(r'function\s+' + t + r'\s*\(', html))
        print(f'{t}: {len(matches)} occurrences')
        for i, m in enumerate(matches):
            lineno = html[:m.start()].count('\n') + 1
            print(f'  - Definition at line {lineno}')

    print('\n=== B) API Endpoints ===')
    endpoints = re.findall(r'fetch\([\'"\`](.*?)[\'"\`]', html)
    for e in set(endpoints):
        print(f'Endpoint: {e}')
        
    print('\n=== D) Observers & Timers ===')
    print('MutationObserver:', html.count('MutationObserver'))
    print('setInterval:', html.count('setInterval'))
    print('setTimeout:', html.count('setTimeout'))
    print('DOMContentLoaded:', html.count('DOMContentLoaded'))
    print('window.addEventListener("load"', html.count('window.addEventListener("load"'))

    print('\n=== E) Device ID Parsing ===')
    regexes = re.findall(r'(\/[^\/\n]+\/[gimuy]*\.test\([^)]+\))', html)
    print('Found regexes (test/match):')
    for r in set(regexes):
        print(' -', r)

    print('\n=== F) Hardcoded Credentials ===')
    print('dev-system-owner-token:', html.count('dev-system-owner-token'))

if __name__ == '__main__':
    audit_devices_html()
