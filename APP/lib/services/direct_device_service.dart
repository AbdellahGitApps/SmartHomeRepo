import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';

class DirectDeviceService {
  final http.Client _client;

  DirectDeviceService({http.Client? client}) : _client = client ?? http.Client();

  Uri _buildUri(String path) {
    return Uri.parse('${AppConfig.esp32BaseUrl}$path');
  }

  Future<Map<String, dynamic>> directOpenDoor() async {
    final response = await _client
        .get(_buildUri('/open'))
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