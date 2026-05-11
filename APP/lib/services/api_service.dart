import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';

class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  Uri _buildUri(String path) {
    return Uri.parse('${AppConfig.baseUrl}$path');
  }

  Future<dynamic> _get(String path) async {
    final response = await _client
        .get(_buildUri(path))
        .timeout(AppConfig.requestTimeout);

    return _handleResponse(response);
  }

  Future<dynamic> _post(String path, {Map<String, dynamic>? body}) async {
    final response = await _client
        .post(
          _buildUri(path),
          headers: {
            'Content-Type': 'application/json',
          },
          body: jsonEncode(body ?? {}),
        )
        .timeout(AppConfig.requestTimeout);

    return _handleResponse(response);
  }

  dynamic _handleResponse(http.Response response) {
    final statusCode = response.statusCode;
    final responseBody = response.body;

    if (statusCode >= 200 && statusCode < 300) {
      if (responseBody.isEmpty) {
        return {'success': true};
      }

      try {
        return jsonDecode(responseBody);
      } catch (_) {
        return responseBody;
      }
    }

    throw Exception('Request failed: $statusCode\n$responseBody');
  }

  Future<dynamic> healthCheck() {
    return _get('/health');
  }

  Future<dynamic> openDoor() {
    return _post(
      '/door/open',
      body: {
        'source': 'flutter_admin',
        'reason': 'manual_open_from_app',
      },
    );
  }

  Future<dynamic> getLatestDoorEvent() {
    return _get('/door/latest');
  }

  Future<dynamic> getDoorLogs() {
    return _get('/door/logs');
  }

  Future<dynamic> getLatestEnergyReading() {
    return _get('/energy/latest');
  }

  Future<dynamic> getLatestEnergyForecast() {
    return _get('/energy/forecast/latest');
  }
}