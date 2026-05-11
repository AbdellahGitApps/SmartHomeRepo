class AppConfig {
  // FastAPI server URL.
  static const String baseUrl = 'http://127.0.0.1:8000';

  // ESP32-CAM live stream URL.
  static const String cameraStreamUrl = 'http://192.168.1.55:81/stream';

  // ESP32 direct control URL.
  // غيّره لاحقًا إلى IP الحقيقي للـ ESP32.
  static const String esp32BaseUrl = 'http://192.168.1.55';

  static const Duration requestTimeout = Duration(seconds: 10);
}