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
- Listens for basic MQTT commands:
  - status
  - restart

## Required Arduino libraries

Install these from Arduino Library Manager:

- PubSubClient
- ArduinoJson

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

Door servo control is not added in this phase.
It belongs to the later official door flow phase.
