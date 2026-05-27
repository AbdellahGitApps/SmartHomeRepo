# Arduino IDE Setup

## المطلوب

- Arduino IDE
- ESP32 Board Package
- FTDI Programmer للـ ESP32-CAM
- Mosquitto MQTT Broker

## Libraries

ثبت من Arduino Library Manager:

- PubSubClient
- ArduinoJson
- ESP32Servo

## ESP32 Board Package URL

https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

## Board

AI Thinker ESP32-CAM

## Upload Wiring

ESP32-CAM 5V  -> FTDI 5V
ESP32-CAM GND -> FTDI GND
ESP32-CAM U0R -> FTDI TX
ESP32-CAM U0T -> FTDI RX
ESP32-CAM IO0 -> GND وقت رفع الكود فقط

بعد الرفع:
- افصل IO0 عن GND
- اضغط Reset
- افتح Serial Monitor على 115200
