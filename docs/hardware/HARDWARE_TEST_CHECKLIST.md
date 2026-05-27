# Hardware Test Checklist

## Before Testing

- [ ] FastAPI يعمل على 0.0.0.0
- [ ] Mosquitto يعمل على Port 1883
- [ ] ESP32 يستخدم IP اللابتوب وليس 127.0.0.1
- [ ] Claim Code مطابق للداشبورد
- [ ] Device ID مطابق للداشبورد
- [ ] MQTT Topics متطابقة

## ESP32-CAM

- [ ] Firmware يترفع
- [ ] Wi-Fi connected يظهر في Serial Monitor
- [ ] ESP32 IP يظهر
- [ ] /capture يعمل
- [ ] /stream يعمل
- [ ] Claim ينجح
- [ ] Heartbeat ينجح
- [ ] الجهاز يظهر Online في Dashboard

## MQTT

- [ ] ESP32 يتصل بالـ Broker
- [ ] ESP32 يعمل Subscribe للـ Topics
- [ ] Restart من Dashboard يظهر في Security Logs
- [ ] Enable / Disable تظهر في Security Logs
- [ ] ESP32 يستقبل الأوامر

## Door Servo

- [ ] Servo على 5V خارجي
- [ ] GND مشترك
- [ ] Servo Pin مطابق للـ Firmware
- [ ] Open من Flutter يصل Backend
- [ ] Backend ينشر MQTT
- [ ] ESP32 يستقبل Open
- [ ] Servo يتحرك

## Camera + Face Recognition

- [ ] Backend يطلب /capture
- [ ] الصورة تصل Backend
- [ ] اختبار Known Face
- [ ] اختبار Unknown Face
- [ ] Face Event يظهر

## Energy

- [ ] ESP32 يرسل Fake Energy Reading
- [ ] تظهر في Dashboard
- [ ] تظهر في Flutter
- [ ] Real Sensor مؤجل
