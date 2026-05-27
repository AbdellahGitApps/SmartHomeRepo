# ESP32-CAM Firmware

Phase 12 firmware for SmartHomeRepo.

## Purpose

This firmware prepares an ESP32-CAM device to work with the local Smart Home backend.

## Current features

- Connects to local Wi-Fi
- Starts ESP32-CAM camera
- Provides /capture endpoint
- Provides /stream endpoint
- Sends claim request to FastAPI backend
- Sends heartbeat request to FastAPI backend
- Connects to MQTT broker
- Listens for MQTT commands:
  - status
  - restart
  - enable
  - disable
  - open
  - unlock
  - lock
- Controls a door servo through MQTT open/lock commands

## Required Arduino libraries

Install these from Arduino Library Manager:

- PubSubClient
- ArduinoJson
- ESP32Servo

ESP32 board package is also required.

## Before uploading

Edit these values inside esp32_cam.ino:

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
String SERVER_BASE_URL = "http://192.168.1.100:8000";
const char* MQTT_HOST = "192.168.1.100";
String CLAIM_CODE = "PUT_CLAIM_CODE_HERE";

Use the real server IP and the real claim code shown in the dashboard.

## Test URLs after upload

After uploading the firmware to the real ESP32-CAM, open Serial Monitor.
It will show the ESP32 IP address.

Example:

ESP32 IP: 192.168.1.55

Then open these URLs from a browser on the same Wi-Fi:

http://192.168.1.55/
http://192.168.1.55/capture
http://192.168.1.55/stream

## Notes

Door servo control is prepared in this firmware. Real testing still requires ESP32-CAM, external 5V servo power, shared GND, and matching MQTT topics.


## Servo wiring

Recommended demo wiring:

ESP32-CAM GPIO 13 -> Servo Signal
External 5V       -> Servo VCC
External GND      -> Servo GND
ESP32-CAM GND     -> External GND

Do not power the servo from ESP32-CAM 3.3V.

## MQTT door behavior

When the firmware receives command `open`, it moves the servo to the open angle, waits, then returns to lock angle.

Default values in firmware:

SERVO_PIN = 13
SERVO_LOCK_ANGLE = 0
SERVO_OPEN_ANGLE = 90
SERVO_OPEN_TIME_MS = 3000
