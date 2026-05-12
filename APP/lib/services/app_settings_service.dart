import 'package:shared_preferences/shared_preferences.dart';

class AppSettingsService {
  static const String _apiBaseUrlKey = 'apiBaseUrl';
  static const String _esp32BaseUrlKey = 'esp32BaseUrl';
  static const String _cameraStreamUrlKey = 'cameraStreamUrl';

  static const String defaultApiBaseUrl = 'http://127.0.0.1:8000';
  static const String defaultEsp32BaseUrl = 'http://192.168.1.55';
  static const String defaultCameraStreamUrl = 'http://192.168.1.55:81/stream';

  Future<String> getApiBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_apiBaseUrlKey) ?? defaultApiBaseUrl;
  }

  Future<String> getEsp32BaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_esp32BaseUrlKey) ?? defaultEsp32BaseUrl;
  }

  Future<String> getCameraStreamUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_cameraStreamUrlKey) ?? defaultCameraStreamUrl;
  }

  Future<void> saveApiBaseUrl(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_apiBaseUrlKey, value.trim());
  }

  Future<void> saveEsp32BaseUrl(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_esp32BaseUrlKey, value.trim());
  }

  Future<void> saveCameraStreamUrl(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_cameraStreamUrlKey, value.trim());
  }

  Future<void> resetToDefaults() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString(_apiBaseUrlKey, defaultApiBaseUrl);
    await prefs.setString(_esp32BaseUrlKey, defaultEsp32BaseUrl);
    await prefs.setString(_cameraStreamUrlKey, defaultCameraStreamUrl);
  }
}