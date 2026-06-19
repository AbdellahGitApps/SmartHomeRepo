import urllib.request
import json
import urllib.error

req = urllib.request.Request('http://127.0.0.1:8000/api/dashboard/final-devices/DOOR-HOME001-002/actions/remove', method='POST', headers={'X-Actor-Role': 'system_owner', 'X-System-Owner-Token': 'dev-system-owner-token'})
try:
    res = urllib.request.urlopen(req).read().decode('utf-8')
    print("SUCCESS:")
    print(res)
except urllib.error.HTTPError as e:
    print("HTTP ERROR:")
    print(e.read().decode('utf-8'))
except Exception as e:
    print("OTHER ERROR:", str(e))
