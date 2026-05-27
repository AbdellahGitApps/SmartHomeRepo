# MQTT Topics and JSON Formats

## Device Command Topics

Backend يرسل أوامر الجهاز إلى:

{device.mqtt_topic}/cmd
{device.mqtt_topic}/control
device/{device_id}/cmd
device/{device_id}/control

للباب الذكي:

{device.mqtt_topic}/door/control

## Door Command JSON

{
  "request_id": "abc123",
  "command": "open",
  "action": "open",
  "device_id": "DOOR-HOME008-001",
  "device_token": "DEVICE_TOKEN",
  "source": "flutter_app",
  "reason": "manual_open_from_flutter",
  "opened_by": "1"
}

الأوامر:
open
lock
unlock
restart
enable
disable
status

## Claim JSON

{
  "claim_code": "HOME008-NJZP",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_ip": "192.168.1.88",
  "device_type": "esp32_cam"
}

## Heartbeat JSON

{
  "device_id": "DOOR-HOME008-001",
  "device_token": "DEVICE_TOKEN",
  "device_ip": "192.168.1.88",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "status": "online"
}

## Energy Reading JSON

{
  "device_id": "METER-HOME008-001",
  "voltage": 220.0,
  "current": 5.7,
  "watts": 1261,
  "kwh_today": 6.2
}
