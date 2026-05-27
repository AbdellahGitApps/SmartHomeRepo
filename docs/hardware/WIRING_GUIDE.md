# Wiring Guide

## ESP32-CAM + Servo

لا تشغل السيرفو من 3.3V حق ESP32-CAM.

استخدم Power خارجي 5V للسيرفو.

التوصيل:

Servo VCC     -> External 5V
Servo GND     -> External GND
Servo Signal  -> ESP32-CAM GPIO 13
ESP32-CAM GND -> External GND

مهم جدًا:
لازم GND حق السيرفو و GND حق ESP32 يكونوا مشتركين.

## Camera Test

بعد معرفة IP حق ESP32-CAM:

http://ESP32_IP/
http://ESP32_IP/capture
http://ESP32_IP/stream

## Energy

الطاقة الآن نختبرها بقراءات Fake من ESP32.
قياس AC الحقيقي مؤجل إلى أن يكون التوصيل آمن.
