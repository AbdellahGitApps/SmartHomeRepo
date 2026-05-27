# Phase 18 Hardware Preparation

هذه المرحلة تجهيز للهاردوير قبل التركيب الحقيقي.

ليست تشغيل أجهزة، وليست رفع Firmware. الهدف منها توثيق:
- MQTT Topics
- JSON Formats
- Arduino IDE Setup
- Wiring
- Hardware Checklist

## الوضع الحالي

Backend جاهز:
- Device Claim
- Heartbeat
- MQTT Device Commands
- Door Open Command
- Energy APIs
- Camera / Face APIs

Firmware موجود:
- firmware/esp32_cam/esp32_cam.ino

المطلوب لاحقًا:
- رفع Firmware على ESP32-CAM
- اختبار الكاميرا
- اختبار السيرفو
- اختبار MQTT الحقيقي
- اختبار الطاقة لاحقًا

## قاعدة مهمة

لا تستخدم 127.0.0.1 داخل ESP32.

استخدم IP اللابتوب أو Raspberry Pi داخل الشبكة، مثال:
FastAPI = http://192.168.1.100:8000
MQTT Host = 192.168.1.100
MQTT Port = 1883

تشغيل السيرفر للهاردوير:
cd edge
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
