import 'package:shared_preferences/shared_preferences.dart';

class AppSettingsService {
  static const String _apiBaseUrlKey = 'api_base_url';
  static const String _esp32BaseUrlKey = 'esp32_base_url';

  static const String _defaultApiBaseUrl = 'http://127.0.0.1:8000';
  static const String _defaultEsp32BaseUrl = 'http://192.168.1.55';

  Future<String> getApiBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_apiBaseUrlKey) ?? _defaultApiBaseUrl;
  }

  Future<String> getEsp32BaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_esp32BaseUrlKey) ?? _defaultEsp32BaseUrl;
  }

  Future<void> saveApiBaseUrl(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_apiBaseUrlKey, value);
  }

  Future<void> saveEsp32BaseUrl(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_esp32BaseUrlKey, value);
  }

  Future<void> resetToDefaults() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_apiBaseUrlKey);
    await prefs.remove(_esp32BaseUrlKey);
  }
}
