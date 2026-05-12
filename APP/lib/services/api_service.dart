import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';
import '../models/door_event.dart';
import '../models/energy_forecast.dart';
import '../models/energy_reading.dart';
import '../models/family_member.dart';
import 'app_settings_service.dart';

class ApiService {
  final http.Client _client;
  final AppSettingsService _settingsService;

  ApiService({
    http.Client? client,
    AppSettingsService? settingsService,
  })  : _client = client ?? http.Client(),
        _settingsService = settingsService ?? AppSettingsService();

  Future<Uri> _buildUri(String path) async {
    final baseUrl = await _settingsService.getApiBaseUrl();
    final normalizedBaseUrl = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;

    return Uri.parse('$normalizedBaseUrl$path');
  }

  Future<dynamic> _get(String path) async {
    final response = await _client
        .get(await _buildUri(path))
        .timeout(AppConfig.requestTimeout);

    return _handleResponse(response);
  }

  Future<dynamic> _post(
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final response = await _client
        .post(
          await _buildUri(path),
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

  Map<String, dynamic> _asMap(dynamic data) {
    if (data is Map<String, dynamic>) {
      return data;
    }

    if (data is Map) {
      return Map<String, dynamic>.from(data);
    }

    throw Exception('Expected JSON object but received ${data.runtimeType}');
  }

  Future<Map<String, dynamic>> healthCheck() async {
    final data = await _get('/health');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> openDoor() async {
    final data = await _post(
      '/door/open',
      body: {
        'source': 'flutter_admin',
        'reason': 'manual_open_from_app',
      },
    );

    return _asMap(data);
  }

  Future<Map<String, dynamic>> logDirectDoorOpen() async {
    final data = await _post('/door/log/direct-open');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> createTestUnknownDoorEvent() async {
    final data = await _post('/door/events/unknown/test');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> getPendingDoorEvent() async {
    final data = await _get('/door/pending');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> openPendingDoorEvent({
    required int eventId,
  }) async {
    final data = await _post('/door/events/$eventId/open');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> denyPendingDoorEvent({
    required int eventId,
  }) async {
    final data = await _post('/door/events/$eventId/deny');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> addPendingEventToFamily({
    required int eventId,
    required String name,
  }) async {
    final data = await _post(
      '/door/events/$eventId/add-to-family',
      body: {
        'name': name,
      },
    );

    return _asMap(data);
  }

  Future<Map<String, dynamic>> addFamilyMember({
    required String name,
  }) async {
    final data = await _post(
      '/family/members',
      body: {
        'name': name,
        'role': 'family_member',
        'face_embedding': null,
      },
    );

    return _asMap(data);
  }

  Future<Map<String, dynamic>> addTestFamilyMember() async {
    final data = await _post('/family/members/test');
    return _asMap(data);
  }

  Future<Map<String, dynamic>> attachTestFaceEmbedding({
    required int memberId,
  }) async {
    final data = await _post(
      '/family/members/$memberId/face-embedding',
      body: {
        'face_embedding': [
          0.11,
          0.22,
          0.33,
          0.44,
          0.55,
          0.66,
          0.77,
          0.88,
        ],
      },
    );

    return _asMap(data);
  }

  Future<Map<String, dynamic>> verifyFaceEmbedding({
    required List<double> faceEmbedding,
    String source = 'flutter_face_engine',
    double threshold = 0.75,
  }) async {
    final data = await _post(
      '/face/verify',
      body: {
        'face_embedding': faceEmbedding,
        'source': source,
        'threshold': threshold,
      },
    );

    return _asMap(data);
  }

  Future<Map<String, dynamic>> verifyTestKnownFace() async {
    return verifyFaceEmbedding(
      faceEmbedding: [
        0.11,
        0.22,
        0.33,
        0.44,
        0.55,
        0.66,
        0.77,
        0.88,
      ],
      source: 'flutter_face_engine',
      threshold: 0.75,
    );
  }

  Future<Map<String, dynamic>> verifyTestUnknownFace() async {
    return verifyFaceEmbedding(
      faceEmbedding: [
        -0.11,
        -0.22,
        -0.33,
        -0.44,
        -0.55,
        -0.66,
        -0.77,
        -0.88,
      ],
      source: 'flutter_face_engine',
      threshold: 0.75,
    );
  }

  Future<List<FamilyMember>> getFamilyMembers() async {
    final data = await _get('/family/members');
    final map = _asMap(data);

    final items = map['items'];

    if (items is! List) {
      return [];
    }

    return items
        .whereType<Map>()
        .map((item) => FamilyMember.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<DoorEvent?> getLatestDoorEvent() async {
    final data = await _get('/door/latest');
    final map = _asMap(data);

    if (map.containsKey('latest')) {
      final latest = map['latest'];

      if (latest == null) {
        return null;
      }

      if (latest is Map) {
        return DoorEvent.fromJson(Map<String, dynamic>.from(latest));
      }

      return null;
    }

    return DoorEvent.fromJson(map);
  }

  Future<List<DoorEvent>> getDoorLogs() async {
    final data = await _get('/door/logs');
    final map = _asMap(data);

    final items = map['items'];

    if (items is! List) {
      return [];
    }

    return items
        .whereType<Map>()
        .map((item) => DoorEvent.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<EnergyReading> getLatestEnergyReading() async {
    final data = await _get('/energy/latest');
    return EnergyReading.fromJson(_asMap(data));
  }

  Future<EnergyForecast> getLatestEnergyForecast() async {
    final data = await _get('/energy/forecast/latest');
    return EnergyForecast.fromJson(_asMap(data));
  }
}