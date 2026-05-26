import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/backend_config.dart';

class BackendApiException implements Exception {
  final String message;
  final int? statusCode;

  const BackendApiException(this.message, {this.statusCode});

  @override
  String toString() {
    if (statusCode == null) {
      return 'BackendApiException: $message';
    }

    return 'BackendApiException($statusCode): $message';
  }
}

class BackendApiService {
  BackendApiService({String? baseUrl, http.Client? client})
    : baseUrl = (baseUrl ?? BackendConfig.defaultBaseUrl).replaceAll(
        RegExp(r'/$'),
        '',
      ),
      _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    final cleanPath = path.startsWith('/') ? path : '/$path';
    final uri = Uri.parse('$baseUrl$cleanPath');

    if (query == null || query.isEmpty) {
      return uri;
    }

    return uri.replace(
      queryParameters: query.map(
        (key, value) => MapEntry(key, value.toString()),
      ),
    );
  }

  Future<Map<String, dynamic>> _get(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    final response = await _client
        .get(_uri(path, query))
        .timeout(BackendConfig.requestTimeout);

    return _decodeResponse(response);
  }

  Future<Map<String, dynamic>> _post(
    String path, {
    Map<String, dynamic>? body,
    Map<String, dynamic>? query,
  }) async {
    final response = await _client
        .post(
          _uri(path, query),
          headers: const {'Content-Type': 'application/json'},
          body: jsonEncode(body ?? <String, dynamic>{}),
        )
        .timeout(BackendConfig.requestTimeout);

    return _decodeResponse(response);
  }

  Map<String, dynamic> _decodeResponse(http.Response response) {
    final text = response.body.trim();

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw BackendApiException(
        text.isEmpty ? 'Backend request failed' : text,
        statusCode: response.statusCode,
      );
    }

    if (text.isEmpty) {
      return <String, dynamic>{'success': true};
    }

    final decoded = jsonDecode(text);

    if (decoded is Map<String, dynamic>) {
      return decoded;
    }

    return <String, dynamic>{'data': decoded};
  }

  Future<Map<String, dynamic>> healthCheck() {
    return _get('/');
  }

  Future<Map<String, dynamic>> getEnergyStatus() {
    return _get('/api/energy/status');
  }

  Future<Map<String, dynamic>> getEnergyLatest() {
    return _get('/api/energy/latest');
  }

  Future<Map<String, dynamic>> getEnergyLogs({int limit = 50}) {
    return _get('/api/energy/logs', query: {'limit': limit});
  }

  Future<Map<String, dynamic>> getEnergyForecastLatest({int limit = 4}) {
    return _get('/api/energy/forecast/latest', query: {'limit': limit});
  }

  Future<Map<String, dynamic>> runEnergyForecast({
    int weeks = 4,
    bool preferDb = true,
    String source = 'flutter_app',
  }) {
    return _post(
      '/api/energy/forecast/run',
      body: {'weeks': weeks, 'prefer_db': preferDb, 'source': source},
    );
  }

  Future<Map<String, dynamic>> openDoor({
    String? deviceId,
    String source = 'flutter_app',
    String reason = 'manual_open_from_flutter',
    String? openedBy,
  }) {
    return _post(
      '/api/door/open',
      body: {
        if (deviceId != null) 'device_id': deviceId,
        'source': source,
        'reason': reason,
        if (openedBy != null) 'opened_by': openedBy,
      },
    );
  }

  Future<Map<String, dynamic>> openSpecificDoor({
    required String deviceRef,
    String source = 'flutter_app',
    String reason = 'manual_open_from_flutter',
    String? openedBy,
  }) {
    return _post(
      '/api/devices/$deviceRef/door/open',
      body: {
        'source': source,
        'reason': reason,
        if (openedBy != null) 'opened_by': openedBy,
      },
    );
  }

  Future<Map<String, dynamic>> getFaceStatus() {
    return _get('/api/face/status');
  }

  Future<Map<String, dynamic>> getFaceEvents({int limit = 20}) {
    return _get('/api/face/events', query: {'limit': limit});
  }

  Future<Map<String, dynamic>> verifyFaceEmbedding({
    required List<double> faceEmbedding,
    String source = 'flutter_app',
  }) {
    return _post(
      '/api/face/verify',
      body: {'face_embedding': faceEmbedding, 'source': source},
    );
  }

  Future<Map<String, dynamic>> recognizeCapture({
    required String captureUrl,
    String source = 'flutter_app',
    bool saveUnknownSnapshot = true,
  }) {
    return _post(
      '/api/face/recognize-capture',
      body: {
        'capture_url': captureUrl,
        'source': source,
        'save_unknown_snapshot': saveUnknownSnapshot,
      },
    );
  }

  void close() {
    _client.close();
  }
}
