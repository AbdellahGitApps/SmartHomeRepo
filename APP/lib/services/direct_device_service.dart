import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import 'app_settings_service.dart';

class DirectDeviceService {
  final http.Client _client;
  final AppSettingsService _appSettingsService = AppSettingsService();

  DirectDeviceService({http.Client? client}) : _client = client ?? http.Client();

  Future<Uri> _buildUri(String path) async {
    final baseUrl = await _appSettingsService.getEsp32BaseUrl();
    return Uri.parse('$baseUrl$path');
  }

  Future<Map<String, dynamic>> directOpenDoor() async {
    final uri = await _buildUri('/open');
    final response = await _client
        .get(uri)
        .timeout(AppConfig.requestTimeout);

    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return {
          'success': true,
          'message': 'Direct open command sent to ESP32',
        };
      }

      try {
        final data = jsonDecode(response.body);

        if (data is Map<String, dynamic>) {
          return data;
        }

        return {
          'success': true,
          'message': data.toString(),
        };
      } catch (_) {
        return {
          'success': true,
          'message': response.body,
        };
      }
    }

    throw Exception(
      'ESP32 direct open failed: ${response.statusCode}\n${response.body}',
    );
  }
}