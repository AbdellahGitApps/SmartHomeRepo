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

  Future<Map<String, dynamic>> _patch(
    String path, {
    Map<String, dynamic>? body,
    Map<String, dynamic>? query,
  }) async {
    final response = await _client
        .patch(
          _uri(path, query),
          headers: const {'Content-Type': 'application/json'},
          body: jsonEncode(body ?? <String, dynamic>{}),
        )
        .timeout(BackendConfig.requestTimeout);

    return _decodeResponse(response);
  }

  Future<Map<String, dynamic>> _delete(
    String path, {
    Map<String, dynamic>? query,
    Map<String, dynamic>? body,
  }) async {
    final response = await _client
        .delete(
          _uri(path, query),
          headers: const {'Content-Type': 'application/json'},
          body: body == null ? null : jsonEncode(body),
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

  Future<Map<String, dynamic>> verifyHomeCode(
    String homeCode,
    String apartmentNumber,
  ) {
    return _get(
      '/api/app/home-by-code',
      query: {'home_code': homeCode, 'apartment_number': apartmentNumber},
    );
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

  Future<Map<String, dynamic>> getFamilyStatus() {
    return _get('/api/family/status');
  }

  Future<Map<String, dynamic>> getFamilyMembers({
    int? homeId,
    bool includeDisabled = true,
  }) {
    return _get(
      '/api/family/members',
      query: {
        if (homeId != null) 'home_id': homeId,
        'include_disabled': includeDisabled,
      },
    );
  }

  Future<Map<String, dynamic>> createFamilyMember({
    required String name,
    required String role,
    required int homeId,
    bool faceEnrolled = false,
    bool enabled = true,
    String? notes,
  }) {
    return _post(
      '/api/family/members',
      body: {
        'home_id': homeId,
        'name': name,
        'role': role,
        'face_enrolled': faceEnrolled,
        'enabled': enabled,
        if (notes != null) 'notes': notes,
      },
    );
  }

  Future<Map<String, dynamic>> updateFamilyMember({
    required String id,
    required String name,
    required String role,
    bool faceEnrolled = false,
    bool enabled = true,
    required int homeId,
    String? notes,
  }) {
    return _patch(
      '/api/family/members/$id',
      body: {
        'home_id': homeId,
        'name': name,
        'role': role,
        'face_enrolled': faceEnrolled,
        'enabled': enabled,
        if (notes != null) 'notes': notes,
      },
    );
  }

  Future<Map<String, dynamic>> enableFamilyMember(String id) {
    return _patch('/api/family/members/$id/enable');
  }

  Future<Map<String, dynamic>> disableFamilyMember(String id) {
    return _patch('/api/family/members/$id/disable');
  }

  Future<Map<String, dynamic>> deleteFamilyMember(String id) {
    return _delete('/api/family/members/$id');
  }

  Future<Map<String, dynamic>> registerAppAdmin({
    required String login,
    required String password,
    required String homeCode,
  }) {
    return _post(
      '/api/app/auth/register-admin',
      body: {'login': login, 'password': password, 'home_code': homeCode},
    );
  }

  Future<Map<String, dynamic>> loginAppAdmin({
    required String login,
    required String password,
  }) {
    return _post(
      '/api/app/auth/login-admin',
      body: {'login': login, 'password': password},
    );
  }

  Future<Map<String, dynamic>> loginAppUser({
    required String adminLogin,
    required String userPassword,
  }) {
    return _post(
      '/api/app/auth/login-user',
      body: {'admin_login': adminLogin, 'user_password': userPassword},
    );
  }

  Future<Map<String, dynamic>> updateAppAccountSettings({
    required String currentLogin,
    required String currentPassword,
    String? newLogin,
    String? newAdminPassword,
    String? userPassword,
    String? doorPin,
  }) {
    return _post(
      '/api/app/auth/settings',
      body: {
        'current_login': currentLogin,
        'current_password': currentPassword,
        if (newLogin != null) 'new_login': newLogin,
        if (newAdminPassword != null) 'new_admin_password': newAdminPassword,
        if (userPassword != null) 'user_password': userPassword,
        if (doorPin != null) 'door_pin': doorPin,
      },
    );
  }

  Future<Map<String, dynamic>> requestPasswordRecovery({
    required String phone,
  }) {
    return _post('/api/app/auth/recovery/request', body: {'phone': phone});
  }

  Future<Map<String, dynamic>> resetPasswordWithRecoveryCode({
    required String phone,
    required String otp,
    required String newPassword,
  }) {
    return _post(
      '/api/app/auth/recovery/reset',
      body: {'phone': phone, 'otp': otp, 'new_password': newPassword},
    );
  }

  Future<Map<String, dynamic>> getHomeSummary({
    String? homeId,
    String? homeCode,
    String? adminLogin,
  }) {
    final query = <String, dynamic>{};

    if (homeId != null && homeId.trim().isNotEmpty) {
      query['home_id'] = homeId.trim();
    }

    if (homeCode != null && homeCode.trim().isNotEmpty) {
      query['home_code'] = homeCode.trim();
    }

    if (adminLogin != null && adminLogin.trim().isNotEmpty) {
      query['admin_login'] = adminLogin.trim();
    }

    return _get('/api/app/home-summary', query: query);
  }

  Future<Map<String, dynamic>> getDoorAccessLogs({
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
    int limit = 50,
  }) {
    final query = <String, dynamic>{'limit': limit, 'viewer_role': viewerRole};

    if (homeId != null && homeId.trim().isNotEmpty) {
      query['home_id'] = homeId.trim();
    }

    if (homeCode != null && homeCode.trim().isNotEmpty) {
      query['home_code'] = homeCode.trim();
    }

    if (adminLogin != null && adminLogin.trim().isNotEmpty) {
      query['admin_login'] = adminLogin.trim();
    }

    return _get('/api/app/door-access-logs-final', query: query);
  }

  Future<Map<String, dynamic>> logDoorManualAction({
    required String action,
    String? homeId,
    String? homeCode,
    String? deviceId,
    String? deviceName,
    String source = 'flutter_app',
    String? actor,
    String? reason,
  }) {
    return _post(
      '/api/app/door-manual-action',
      body: {
        'action': action,
        if (homeId != null && homeId.trim().isNotEmpty)
          'home_id': homeId.trim(),
        if (homeCode != null && homeCode.trim().isNotEmpty)
          'home_code': homeCode.trim(),
        if (deviceId != null && deviceId.trim().isNotEmpty)
          'device_id': deviceId.trim(),
        if (deviceName != null && deviceName.trim().isNotEmpty)
          'device_name': deviceName.trim(),
        'source': source,
        if (actor != null && actor.trim().isNotEmpty) 'actor': actor.trim(),
        if (reason != null && reason.trim().isNotEmpty) 'reason': reason.trim(),
      },
    );
  }

  Future<Map<String, dynamic>> checkAppAccountStatus({
    String? homeId,
    String? homeCode,
    String? adminLogin,
  }) {
    return _get(
      '/api/app/auth/account-status',
      query: {
        if (homeId != null && homeId.trim().isNotEmpty)
          'home_id': homeId.trim(),
        if (homeCode != null && homeCode.trim().isNotEmpty)
          'home_code': homeCode.trim(),
        if (adminLogin != null && adminLogin.trim().isNotEmpty)
          'admin_login': adminLogin.trim(),
      },
    );
  }

  void close() {
    _client.close();
  }

  // D7M16_REAL_ALERTS_LOG_DELETE_API_START

  Future<Map<String, dynamic>> fetchAppAlerts({
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
  }) {
    return _get(
      '/api/app/alerts-final',
      query: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
      },
    );
  }

  Future<Map<String, dynamic>> resolveAppAlert(
    String alertId, {
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
  }) {
    return _post(
      '/api/app/alerts-final/${Uri.encodeComponent(alertId)}/resolve',
      query: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
      },
    );
  }

  Future<Map<String, dynamic>> hideAppAlert(
    String alertId, {
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
  }) {
    return _delete(
      '/api/app/alerts-final/${Uri.encodeComponent(alertId)}',
      query: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
      },
    );
  }

  Future<Map<String, dynamic>> decideAppAlert({
    required String alertId,
    required String action,
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String? memberName,
    bool faceEnrolled = false,
  }) {
    return _post(
      '/api/app/alerts-final/${Uri.encodeComponent(alertId)}/decision',
      body: {
        'action': action,
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        if (memberName != null && memberName.isNotEmpty)
          'member_name': memberName,
        'face_enrolled': faceEnrolled,
      },
    );
  }

  Future<Map<String, dynamic>> clearAppAlerts({
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
  }) {
    return _post(
      '/api/app/alerts-final/clear',
      body: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
      },
    );
  }

  Future<Map<String, dynamic>> deleteDoorAccessLog({
    required String sourceTable,
    required String sourceId,
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
  }) {
    return _delete(
      '/api/app/door-access-logs-final/$sourceTable/${Uri.encodeComponent(sourceId)}',
      query: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
      },
    );
  }

  Future<Map<String, dynamic>> bulkDeleteDoorAccessLogs({
    String? homeId,
    String? homeCode,
    String? adminLogin,
    String viewerRole = 'admin',
    String date = 'all',
    String actor = 'all',
  }) {
    return _delete(
      '/api/app/door-access-logs-final/bulk',
      body: {
        if (homeId != null && homeId.isNotEmpty) 'home_id': homeId,
        if (homeCode != null && homeCode.isNotEmpty) 'home_code': homeCode,
        if (adminLogin != null && adminLogin.isNotEmpty)
          'admin_login': adminLogin,
        'viewer_role': viewerRole,
        'date': date,
        'actor': actor,
      },
    );
  }

  // D7M16_REAL_ALERTS_LOG_DELETE_API_END


  Future<Map<String, dynamic>> clearFamilyMembers({
    String? homeId,
  }) {
    final query = homeId != null && homeId.trim().isNotEmpty
        ? '?home_id=${Uri.encodeQueryComponent(homeId.trim())}'
        : '';

    return _delete('/api/family/members$query');
  }

  // D7M16_APP_CAMERA_REAL_BINDING_START
  Future<Map<String, dynamic>> getAppCameras({
    String? homeId,
    String? homeCode,
    String? apartmentNumber,
    String? adminLogin,
  }) {
    final query = <String, dynamic>{};

    if (homeId != null && homeId.trim().isNotEmpty) {
      query['home_id'] = homeId.trim();
    }

    if (homeCode != null && homeCode.trim().isNotEmpty) {
      query['home_code'] = homeCode.trim();
    }

    if (apartmentNumber != null && apartmentNumber.trim().isNotEmpty) {
      query['apartment_number'] = apartmentNumber.trim();
    }

    if (adminLogin != null && adminLogin.trim().isNotEmpty) {
      query['admin_login'] = adminLogin.trim();
    }

    return _get('/api/app/cameras-real-v2', query: query);
  }

  Future<Map<String, dynamic>> getAppCameraFaceEvents({
    String? homeId,
    String? homeCode,
    String? apartmentNumber,
    String? adminLogin,
    int limit = 50,
  }) {
    final query = <String, dynamic>{'limit': limit};

    if (homeId != null && homeId.trim().isNotEmpty) {
      query['home_id'] = homeId.trim();
    }

    if (homeCode != null && homeCode.trim().isNotEmpty) {
      query['home_code'] = homeCode.trim();
    }

    if (apartmentNumber != null && apartmentNumber.trim().isNotEmpty) {
      query['apartment_number'] = apartmentNumber.trim();
    }

    if (adminLogin != null && adminLogin.trim().isNotEmpty) {
      query['admin_login'] = adminLogin.trim();
    }

    return _get('/api/app/camera-face-events-real-v2', query: query);
  }
  // D7M16_APP_CAMERA_REAL_BINDING_END


}
