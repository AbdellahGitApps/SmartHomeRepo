class AppConfig {
  // Change this later to the laptop/server IP on the local network.
  // Example: http://192.168.1.10:8000
  static const String baseUrl = 'http://127.0.0.1:8000';

  // ESP32-CAM live stream URL, to be changed later when the real camera IP is known.
  // Example: http://192.168.1.55:81/stream
  static const String cameraStreamUrl = 'http://192.168.1.55:81/stream';

  static const Duration requestTimeout = Duration(seconds: 10);
}
