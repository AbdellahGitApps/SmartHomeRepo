import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../services/backend_api_service.dart';
import '../utils/date_formatter.dart';
import '../config/backend_config.dart';

class AppStateProvider with ChangeNotifier, WidgetsBindingObserver {
  final BackendApiService _api = BackendApiService();
  final _secureStorage = const FlutterSecureStorage();
  List<Map<String, dynamic>> _localAppAccounts = [];

  AppStateProvider() {
    _loadSavedAccountState();
    WidgetsBinding.instance.addObserver(this);
  }

  ThemeMode _themeMode = ThemeMode.system;
  Locale _locale = const Locale('en');
  bool _isLoggedIn = false;
  String _userName = '';
  String _adminName = '';
  String _ownerName = '';
  String _userRole = 'Admin';
  String _password = '';

  String _doorPin = '';
  String _cameraPin = '';
  String _userAccountPassword = '';
  String _userAccountUsername = '';
  int _activeAlertCount = 0;
  DateTime _lastUpdatedAt = DateTime.now();

  Map<String, dynamic>? _homeSummary;
  bool _homeSummaryLoading = false;
  Timer? _accountStatusTimer;

  String _serverIp = '192.168.1.100';
  String _cameraUrl = 'http://192.168.1.100:8080/video_feed';
  String _homeCode = '';
  String _homeId = '';
  String _homeDbId = '';
  String _apartmentNumber = '';

  bool _appLockEnabled = false;
  bool _biometricAuthEnabled = false;

  bool _familyLoading = false;
  String? _familyError;
  String? _lastAuthError;

  ThemeMode get themeMode => _themeMode;
  Locale get locale => _locale;
  bool get isLoggedIn => _isLoggedIn;
  bool get biometricAuthEnabled => _biometricAuthEnabled;
  String _firstTwoWords(String value) {
    final clean = value.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (clean.isEmpty) return '';
    final parts = clean.split(' ');
    if (parts.length == 1) return parts.first;
    return '${parts[0]} ${parts[1]}';
  }

  bool _onlyDigits(String value) {
    return RegExp(r'^[0-9]+$').hasMatch(value.trim());
  }

  String get displayName {
    final role = _userRole.toLowerCase().trim();

    if (role == 'user') {
      final username = _userAccountUsername.trim();
      if (username.isNotEmpty) return username;

      final localUser = _userName.trim();
      if (localUser.isNotEmpty && localUser != 'User Guest') return localUser;

      return 'User';
    }

    final ownerShort = _firstTwoWords(_ownerName);
    if (ownerShort.isNotEmpty) return ownerShort;

    final localName = _firstTwoWords(_userName);
    if (localName.isNotEmpty && !_onlyDigits(localName)) return localName;

    final phone = _adminName.trim();
    if (phone.isNotEmpty) return phone;

    return 'Admin';
  }

  String get userName => displayName;
  String get adminName => _adminName;
  String get ownerName => _ownerName;
  String get userRole => _userRole;
  String get password => _password;

  String get doorPin => _doorPin;
  String get cameraPin => _cameraPin;
  String get userPin => _doorPin;
  String get userAccountPassword => _userAccountPassword;
  String get userAccountUsername => _userAccountUsername;
  int get activeAlertCount => _activeAlertCount;
  String get lastUpdateText => _formatDateTime(_lastUpdatedAt);

  String get serverIp => _serverIp;
  String get cameraUrl => _cameraUrl;
  String get homeCode => _homeCode;
  String get homeId => _homeId;
  String get homeDbId => _homeDbId;
  String get apartmentNumber => _apartmentNumber;
  bool get appLockEnabled => _appLockEnabled;
  bool get isDeviceLinked => _homeCode.isNotEmpty && _adminName.isNotEmpty;

  bool get isAdmin => _userRole.toLowerCase() == 'admin';
  bool get isUser => _userRole.toLowerCase() == 'user';

  bool get canManageFamily => isAdmin;
  bool get canOpenDoor => isAdmin;
  bool get canManageAlerts => isAdmin;
  bool get canViewFamily => true;
  bool get canViewDoors => true;

  bool get familyLoading => _familyLoading;
  String? get familyError => _familyError;
  String? get lastAuthError => _lastAuthError;

  Map<String, dynamic>? get homeSummary => _homeSummary;
  bool get homeSummaryLoading => _homeSummaryLoading;

  List<Map<String, dynamic>> get homeSummaryDevices {
    final devices = _d7AsMapList(_d7AsMap(_homeSummary)['devices']);
    return List.unmodifiable(devices);
  }

  List<Map<String, dynamic>> get homeSummaryDoorDevices {
    return List.unmodifiable(
      homeSummaryDevices.where((device) {
        final type = (device['device_type'] ?? device['type'] ?? '')
            .toString()
            .toLowerCase();
        return type.contains('door');
      }).toList(),
    );
  }

  List<Map<String, dynamic>> get homeSummaryEnergyDevices {
    return List.unmodifiable(
      homeSummaryDevices.where((device) {
        final type = (device['device_type'] ?? device['type'] ?? '')
            .toString()
            .toLowerCase();
        return type.contains('energy') || type.contains('meter');
      }).toList(),
    );
  }

  List<Map<String, dynamic>> get homeSummaryCameraDevices {
    return List.unmodifiable(
      homeSummaryDevices.where((device) {
        final type = (device['device_type'] ?? device['type'] ?? '')
            .toString()
            .toLowerCase();
        return type.contains('door') || type.contains('camera');
      }).toList(),
    );
  }

  Map<String, dynamic> _d7AsMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return value.map((key, val) => MapEntry(key.toString(), val));
    }
    return <String, dynamic>{};
  }

  List<Map<String, dynamic>> _d7AsMapList(dynamic value) {
    if (value is! List) return <Map<String, dynamic>>[];

    return value
        .whereType<Map>()
        .map((item) => item.map((key, val) => MapEntry(key.toString(), val)))
        .toList();
  }

  int? _d7CurrentHomeNumericId() {
    final fromDbId = int.tryParse(_homeDbId.trim());
    if (fromDbId != null) return fromDbId;

    final summaryHome = _d7AsMap(_d7AsMap(_homeSummary)['home']);

    final fromSummary = int.tryParse(
      (summaryHome['id'] ?? summaryHome['raw_id'] ?? '').toString(),
    );
    if (fromSummary != null) return fromSummary;

    return null;
  }

  void _startAccountStatusWatcher() {
    _accountStatusTimer?.cancel();

    if (!_isLoggedIn) return;

    _accountStatusTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      checkCurrentAccountStatus();
    });

    checkCurrentAccountStatus();
  }

  void _stopAccountStatusWatcher() {
    _accountStatusTimer?.cancel();
    _accountStatusTimer = null;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused) {
      _stopAccountStatusWatcher();
    } else if (state == AppLifecycleState.resumed) {
      _startAccountStatusWatcher();
    }
  }

  bool _backendSaysAccountActive(Map<String, dynamic> response) {
    final active = response['active'];
    if (active is bool) return active;

    final status = (response['status'] ?? '').toString().toLowerCase();
    if (status == 'disabled' ||
        status == 'inactive' ||
        status == 'blocked' ||
        status == 'suspended') {
      return false;
    }

    return true;
  }

  Future<bool> checkCurrentAccountStatus() async {
    if (!_isLoggedIn) return true;

    try {
      final response = await _api.checkAppAccountStatus(
        homeId: _homeDbId.trim().isEmpty ? null : _homeDbId.trim(),
        homeCode: _homeCode,
        adminLogin: _adminName,
      );

      final active = _backendSaysAccountActive(response);

      final account = _d7AsMap(response['account']);
      final serverUserPassword = (account['user_password'] ?? '')
          .toString()
          .trim();

      if (isUser &&
          serverUserPassword.isNotEmpty &&
          serverUserPassword != _userAccountPassword.trim()) {
        _forceLogoutDisabled(
          'User password was changed. Please sign in again.',
        );
        return false;
      }

      if (!active) {
        _forceLogoutDisabled(
          (response['message'] ??
                  'This account has been disabled by System Owner.')
              .toString(),
        );
        return false;
      }

      return true;
    } catch (_) {
      // ?? ???? ???????? ??? ?????? ??????? ??????.
      return true;
    }
  }

  void _forceLogoutDisabled(String message) {
    _lastAuthError = message;
    _isLoggedIn = false;
    _activeAlertCount = 0;
    _homeSummary = null;
    _stopAccountStatusWatcher();
    touchLastUpdate();
    _saveAccountState();
    notifyListeners();
  }

  Future<void> loadHomeSummary() async {
    if (_homeSummaryLoading) return;

    _homeSummaryLoading = true;

    try {
      final response = await _api.getHomeSummary(
        homeId: _homeDbId.trim().isEmpty ? null : _homeDbId.trim(),
        homeCode: _homeCode,
        adminLogin: _adminName,
      );

      if (response['success'] == true) {
        _homeSummary = Map<String, dynamic>.from(response);

        final home = _d7AsMap(response['home']);
        _homeCode = (home['home_code'] ?? _homeCode).toString();
        _homeId = (home['home_id'] ?? _homeId).toString();
        _apartmentNumber = (home['apartment_number'] ?? _apartmentNumber)
            .toString();

        final alertValue = response['alerts_count'];
        if (alertValue is num) {
          _activeAlertCount = alertValue.toInt();
        } else {
          _activeAlertCount =
              int.tryParse(alertValue?.toString() ?? '') ?? _activeAlertCount;
        }

        await _saveAccountState();
        touchLastUpdate();
      }
    } catch (_) {
      // Keep current UI data if backend summary is temporarily unavailable.
    } finally {
      _homeSummaryLoading = false;
      notifyListeners();
    }
  }

  String _formatDateTime(DateTime value) {
    return DateFormatter.format(value);
  }

  void touchLastUpdate() {
    _lastUpdatedAt = DateTime.now();
  }

  Future<void> _loadSavedAccountState() async {
    final prefs = await SharedPreferences.getInstance();

    final isDarkMode = prefs.getBool('is_dark_mode') ?? true;
    _themeMode = isDarkMode ? ThemeMode.dark : ThemeMode.light;

    final langCode = prefs.getString('language_code') ?? 'en';
    _locale = Locale(langCode);

    _biometricAuthEnabled = prefs.getBool('biometric_auth_enabled') ?? false;

    final rawAccounts = prefs.getString('local_app_accounts');
    if (rawAccounts != null && rawAccounts.trim().isNotEmpty) {
      try {
        final decoded = jsonDecode(rawAccounts);
        if (decoded is List) {
          _localAppAccounts = decoded
              .whereType<Map>()
              .map((item) => Map<String, dynamic>.from(item))
              .toList();
        }
      } catch (_) {
        _localAppAccounts = [];
      }
    }

    _adminName = prefs.getString('admin_name') ?? '';
    _ownerName = prefs.getString('owner_name') ?? '';
    
    // Load sensitive credentials from flutter_secure_storage
    _password = await _secureStorage.read(key: 'admin_password') ?? '';
    _doorPin = await _secureStorage.read(key: 'door_pin') ?? '';
    _cameraPin = await _secureStorage.read(key: 'camera_pin') ?? '';
    _userAccountPassword = await _secureStorage.read(key: 'user_account_password') ?? '';
    
    _userAccountUsername = prefs.getString('user_account_username') ?? '';
    _homeCode = prefs.getString('home_code') ?? '';
    _homeId = prefs.getString('home_id') ?? _homeCode;
    _homeDbId = prefs.getString('home_db_id') ?? '';
    _apartmentNumber = prefs.getString('apartment_number') ?? '';
    _serverIp = prefs.getString('server_ip') ?? '';
    if (_serverIp.isEmpty) {
      try {
        final uri = Uri.parse(BackendConfig.defaultBaseUrl);
        _serverIp = uri.host;
      } catch (_) {
        _serverIp = '127.0.0.1';
      }
    }
    _cameraUrl = prefs.getString('camera_url') ?? 'http://$_serverIp:8080/video_feed';

    if (_serverIp.isNotEmpty) {
      BackendApiService().baseUrl = 'http://$_serverIp:8000';
    }

    if (isAdmin || _userName.trim().isEmpty || _userName == '1') {
      _userName = displayName;
    }

    notifyListeners();
  }

  Future<void> _saveAccountState() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('admin_name', _adminName);
    await prefs.setString('owner_name', _ownerName);
    
    // Save sensitive credentials to flutter_secure_storage
    await _secureStorage.write(key: 'admin_password', value: _password);
    await _secureStorage.write(key: 'door_pin', value: _doorPin);
    await _secureStorage.write(key: 'camera_pin', value: _cameraPin);
    await _secureStorage.write(key: 'user_account_password', value: _userAccountPassword);
    
    await prefs.setString('user_account_username', _userAccountUsername);
    await prefs.setString('home_code', _homeCode);
    await prefs.setString('home_id', _homeId);
    await prefs.setString('home_db_id', _homeDbId);
    await prefs.setString('apartment_number', _apartmentNumber);
    await prefs.setString('server_ip', _serverIp);
    await prefs.setString('camera_url', _cameraUrl);
  }

  void toggleTheme(bool isDark) {
    _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
    _saveThemeAndLanguage();
    touchLastUpdate();
    notifyListeners();
  }

  void switchLanguage(String languageCode) {
    _locale = Locale(languageCode);
    _saveThemeAndLanguage();
    touchLastUpdate();
    notifyListeners();
  }

  Future<void> _saveThemeAndLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('is_dark_mode', _themeMode == ThemeMode.dark);
    await prefs.setString('language_code', _locale.languageCode);
  }

  void updateName(String newName) {
    final cleanName = newName.trim();
    if (cleanName.isEmpty) return;

    final oldLogin = _adminName;
    final oldPassword = _password;

    _adminName = cleanName;
    if (isAdmin) {
      _userName = cleanName;
    }

    _api
        .updateAppAccountSettings(
          currentLogin: oldLogin,
          currentPassword: oldPassword,
          newLogin: cleanName,
        )
        .catchError((_) => <String, dynamic>{});

    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void updatePassword(String newPassword) {
    final cleanPassword = newPassword.trim();
    if (cleanPassword.isEmpty) return;

    final oldLogin = _adminName;
    final oldPassword = _password;

    _password = cleanPassword;

    _api
        .updateAppAccountSettings(
          currentLogin: oldLogin,
          currentPassword: oldPassword,
          newAdminPassword: cleanPassword,
        )
        .catchError((_) => <String, dynamic>{});

    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void updateDoorPin(String newPin) {
    final cleanPin = newPin.trim();
    if (cleanPin.isEmpty) return;

    _doorPin = cleanPin;

    _api
        .updateAppAccountSettings(
          currentLogin: _adminName,
          currentPassword: _password,
          doorPin: cleanPin,
        )
        .catchError((_) => <String, dynamic>{});

    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void updateCameraPin(String newPin) {
    final cleanPin = newPin.trim();
    if (cleanPin.isEmpty) return;

    _cameraPin = cleanPin;

    _api
        .updateAppAccountSettings(
          currentLogin: _adminName,
          currentPassword: _password,
          cameraPin: cleanPin,
        )
        .catchError((_) => <String, dynamic>{});

    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  Future<bool> updateUserAccountUsername(String newUsername) async {
    final cleanUsername = newUsername.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (cleanUsername.isEmpty) {
      _lastAuthError = 'Username is required.';
      notifyListeners();
      return false;
    }

    final oldUsername = _userAccountUsername;

    if (cleanUsername.toLowerCase() == oldUsername.trim().toLowerCase()) {
      return true;
    }

    try {
      final response = await _api.updateAppAccountSettings(
        currentLogin: _adminName,
        currentPassword: _password,
        userUsername: cleanUsername,
      );

      final account = response['account'];
      if (account is Map) {
        _userAccountUsername = (account['user_username'] ?? cleanUsername)
            .toString();
        _userAccountPassword =
            (account['user_password'] ?? _userAccountPassword).toString();
      } else {
        _userAccountUsername = cleanUsername;
      }

      if (_userRole.toLowerCase().trim() == 'user') {
        _userName = _userAccountUsername;
      }

      _lastAuthError = null;
      await _saveAccountState();
      touchLastUpdate();
      notifyListeners();
      return true;
    } catch (error) {
      _userAccountUsername = oldUsername;
      _lastAuthError = _readBackendError(error, 'Could not update username.');
      await _saveAccountState();
      notifyListeners();
      return false;
    }
  }

  void updateUserAccountPassword(String newPassword) {
    final cleanPassword = newPassword.trim();
    if (cleanPassword.isEmpty) return;

    _userAccountPassword = cleanPassword;

    _api
        .updateAppAccountSettings(
          currentLogin: _adminName,
          currentPassword: _password,
          userPassword: cleanPassword,
        )
        .catchError((_) => <String, dynamic>{});

    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void setActiveAlertCount(int count) {
    _activeAlertCount = count < 0 ? 0 : count;
    touchLastUpdate();
    notifyListeners();
  }

  void updateNetworkSettings({
    String? serverIp,
    String? cameraUrl,
    String? homeCode,
  }) {
    if (serverIp != null) {
      _serverIp = serverIp;
      BackendApiService().baseUrl = 'http://$serverIp:8000';
    }
    if (cameraUrl != null) _cameraUrl = cameraUrl;
    if (homeCode != null) _homeCode = homeCode;
    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void updateSecuritySettings({String? pin, bool? appLock, bool? biometricAuth}) {
    if (pin != null && pin.trim().isNotEmpty) {
      _doorPin = pin.trim();
    }
    if (appLock != null) _appLockEnabled = appLock;
    if (biometricAuth != null) {
      _biometricAuthEnabled = biometricAuth;
      SharedPreferences.getInstance().then((prefs) {
        prefs.setBool('biometric_auth_enabled', _biometricAuthEnabled);
      });
    }
    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void resetToDefaults() {
    try {
      final uri = Uri.parse(BackendConfig.defaultBaseUrl);
      _serverIp = uri.host;
    } catch (_) {
      _serverIp = '127.0.0.1';
    }
    _cameraUrl = 'http://$_serverIp:8080/video_feed';
    BackendApiService().baseUrl = 'http://$_serverIp:8000';
    _homeCode = '';
    _homeDbId = '';
    _doorPin = '';
    _cameraPin = '';
    _userAccountPassword = '';
    _ownerName = '';
    _userAccountUsername = '';
    _password = '';
    _appLockEnabled = false;
    _activeAlertCount = 0;
    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  String _cleanApartmentNumber(String value) {
    return value.trim().replaceAll(RegExp(r'[^0-9]'), '');
  }

  Future<void> _saveLocalAppAccounts() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('local_app_accounts', jsonEncode(_localAppAccounts));
  }

  Future<void> _loadLocalAppAccountsOnly() async {
    final prefs = await SharedPreferences.getInstance();
    final rawAccounts = prefs.getString('local_app_accounts');

    if (rawAccounts == null || rawAccounts.trim().isEmpty) {
      _localAppAccounts = [];
      return;
    }

    try {
      final decoded = jsonDecode(rawAccounts);
      if (decoded is List) {
        _localAppAccounts = decoded
            .whereType<Map>()
            .map((item) => Map<String, dynamic>.from(item))
            .toList();
      }
    } catch (_) {
      _localAppAccounts = [];
    }
  }

  int _localAccountIndexByApartment(String apartmentNumber) {
    final cleanApartment = _cleanApartmentNumber(apartmentNumber);

    return _localAppAccounts.indexWhere((account) {
      final accountApartment = _cleanApartmentNumber(
        (account['apartment_number'] ?? '').toString(),
      );
      return accountApartment == cleanApartment;
    });
  }

  Future<void> _applyLocalAppAccount(
    Map<String, dynamic> account,
    String role,
  ) async {
    _adminName = (account['admin_username'] ?? '').toString();
    _ownerName = (account['owner_name'] ?? _ownerName).toString();
    _userAccountUsername = (account['user_username'] ?? _userAccountUsername)
        .toString();
    _userName = role.toLowerCase() == 'admin'
        ? displayName
        : (_userAccountUsername.trim().isNotEmpty
              ? _userAccountUsername.trim()
              : 'User');
    _password = (account['admin_password'] ?? '').toString();
    _homeCode = (account['home_code'] ?? '').toString();
    _homeId = (account['home_id'] ?? '').toString();
    _apartmentNumber = (account['apartment_number'] ?? '').toString();
    _userAccountPassword = (account['user_password'] ?? _userAccountPassword)
        .toString();
    _cameraPin = (account['camera_pin'] ?? _cameraPin).toString();

    _isLoggedIn = true;
    _userRole = role;

    await _saveAccountState();
    touchLastUpdate();
    _startAccountStatusWatcher();
    loadHomeSummary();
    loadFamilyMembers();
    notifyListeners();
  }

  Future<void> _upsertLocalAppAccount(Map<String, dynamic> account) async {
    await _loadLocalAppAccountsOnly();

    final index = _localAccountIndexByApartment(
      (account['apartment_number'] ?? '').toString(),
    );

    if (index >= 0) {
      _localAppAccounts[index] = {..._localAppAccounts[index], ...account};
    } else {
      _localAppAccounts.add(account);
    }

    await _saveLocalAppAccounts();
  }

  void _updateCurrentLocalAppAccount() {
    final index = _localAccountIndexByApartment(_apartmentNumber);
    if (index < 0) return;

    _localAppAccounts[index] = {
      ..._localAppAccounts[index],
      'admin_username': _adminName,
      'owner_name': _ownerName,
      'admin_password': _password,
      'home_code': _homeCode,
      'home_id': _homeId,
      'apartment_number': _apartmentNumber,
      'user_password': _userAccountPassword,
      'user_username': _userAccountUsername,
      'camera_pin': _cameraPin,
    };

    _saveLocalAppAccounts();
  }

  void _applyAppAuthPayload(Map<String, dynamic> response, String role) {
    final home = response['home'];
    final account = response['account'];

    if (home is Map) {
      _homeCode = (home['home_code'] ?? '').toString();
      _ownerName = (home['owner_name'] ?? _ownerName).toString();
      _homeDbId = (home['id'] ?? home['raw_id'] ?? '').toString();
      _homeId = (home['home_id'] ?? '').toString();

      if (_homeId.trim().isEmpty && _homeDbId.trim().isNotEmpty) {
        final parsedHomeId = int.tryParse(_homeDbId);
        if (parsedHomeId == null) {
          _homeId = _homeDbId;
        } else {
          _homeId = 'HOME-' + parsedHomeId.toString().padLeft(3, '0');
        }
      }

      _apartmentNumber = (home['apartment_number'] ?? '').toString();
    }

    if (account is Map) {
      _adminName = (account['owner_phone'] ?? account['admin_login'] ?? '')
          .toString();
      _password = (account['admin_password'] ?? '').toString();
      _userAccountPassword = (account['user_password'] ?? '').toString();
      _userAccountUsername = (account['user_username'] ?? '').toString();
      _doorPin = (account['door_pin'] ?? '').toString();
      _cameraPin = (account['camera_pin'] ?? '').toString();
    }

    _userRole = role;
    _isLoggedIn = true;
    _userName = role.toLowerCase() == 'admin'
        ? displayName
        : (_userAccountUsername.trim().isNotEmpty
              ? _userAccountUsername.trim()
              : 'User');

    _saveAccountState();
    touchLastUpdate();
    _startAccountStatusWatcher();
    loadHomeSummary();
    loadFamilyMembers();
    notifyListeners();
  }

  String _readBackendError(dynamic error, String fallback) {
    final text = error.toString();
    
    final isNetworkError = text.contains('SocketException') ||
        text.contains('HttpException') ||
        text.contains('ClientException') ||
        text.contains('TimeoutException') ||
        text.toLowerCase().contains('failed host lookup') ||
        text.toLowerCase().contains('connection refused') ||
        text.toLowerCase().contains('connection timed out') ||
        text.toLowerCase().contains('network is unreachable');
        
    if (isNetworkError) {
      return 'Network connection failed. Please check your server address and network connection. Details: $text';
    }

    final detailMatch = RegExp(r'"detail"\s*:\s*"([^"]+)"').firstMatch(text);
    if (detailMatch != null) {
      return detailMatch.group(1) ?? fallback;
    }

    if (text.contains('BackendApiException')) {
      return text.replaceFirst(
        RegExp(r'^BackendApiException(\([0-9]+\))?:\s*'),
        '',
      );
    }

    return fallback;
  }

  Future<bool> signInAdminWithHomeCode({
    required String username,
    required String password,
    required String homeCode,
  }) async {
    _lastAuthError = null;

    final login = username.trim();
    final cleanPassword = password.trim();
    final cleanHomeCode = homeCode.trim();

    if (login.isEmpty || cleanPassword.isEmpty || cleanHomeCode.isEmpty) {
      _lastAuthError = 'Phone Number, Password, and Home Code are required.';
      return false;
    }

    try {
      await _api.registerAppAdmin(
        login: login,
        password: cleanPassword,
        homeCode: cleanHomeCode,
      );

      return true;
    } catch (error) {
      _lastAuthError = _readBackendError(
        error,
        'Could not register this account.',
      );
      return false;
    }
  }

  Future<bool> loginAdminWithApartment({
    required String username,
    required String password,
    required String apartmentNumber,
  }) async {
    await _loadLocalAppAccountsOnly();

    final cleanUsername = username.trim().toLowerCase();
    final cleanPassword = password.trim();
    final cleanApartment = _cleanApartmentNumber(apartmentNumber);

    for (final account in _localAppAccounts) {
      final accountUsername = (account['admin_username'] ?? '')
          .toString()
          .trim()
          .toLowerCase();
      final accountPassword = (account['admin_password'] ?? '')
          .toString()
          .trim();
      final accountApartment = _cleanApartmentNumber(
        (account['apartment_number'] ?? '').toString(),
      );

      if (accountUsername == cleanUsername &&
          accountPassword == cleanPassword &&
          accountApartment == cleanApartment) {
        await _applyLocalAppAccount(account, 'Admin');
        return true;
      }
    }

    return false;
  }

  Future<bool> loginUserWithApartment({
    required String userPassword,
    required String apartmentNumber,
  }) async {
    await _loadLocalAppAccountsOnly();

    final cleanPassword = userPassword.trim();
    final cleanApartment = _cleanApartmentNumber(apartmentNumber);

    for (final account in _localAppAccounts) {
      final accountPassword = (account['user_password'] ?? '123')
          .toString()
          .trim();
      final accountApartment = _cleanApartmentNumber(
        (account['apartment_number'] ?? '').toString(),
      );

      if (accountPassword == cleanPassword &&
          accountApartment == cleanApartment) {
        await _applyLocalAppAccount(account, 'User');
        return true;
      }
    }

    return false;
  }

  Future<bool> loginAdminWithServer({
    required String login,
    required String password,
  }) async {
    _lastAuthError = null;

    if (login.trim().isEmpty || password.trim().isEmpty) {
      _lastAuthError = 'Phone Number and Password are required.';
      return false;
    }

    try {
      final response = await _api.loginAppAdmin(
        login: login.trim(),
        password: password.trim(),
      );

      _applyAppAuthPayload(response, 'Admin');
      return true;
    } catch (error) {
      _lastAuthError = _readBackendError(
        error,
        'Invalid username or password.',
      );
      return false;
    }
  }

  Future<bool> loginUserWithServer({
    required String adminLogin,
    required String userPassword,
  }) async {
    _lastAuthError = null;

    if (adminLogin.trim().isEmpty || userPassword.trim().isEmpty) {
      _lastAuthError = 'Username and User Password are required.';
      return false;
    }

    try {
      final response = await _api.loginAppUser(
        adminLogin: adminLogin.trim(),
        userPassword: userPassword.trim(),
      );

      _applyAppAuthPayload(response, 'User');
      return true;
    } catch (error) {
      _lastAuthError = _readBackendError(error, 'Invalid user login.');
      return false;
    }
  }

  Future<bool> requestPasswordRecoveryCode(String phone) async {
    _lastAuthError = null;

    if (phone.trim().isEmpty) {
      _lastAuthError = 'Phone number is required.';
      return false;
    }

    try {
      await _api.requestPasswordRecovery(phone: phone.trim());
      return true;
    } catch (error) {
      _lastAuthError = _readBackendError(
        error,
        'Could not generate recovery code.',
      );
      return false;
    }
  }

  Future<bool> resetPasswordWithRecoveryCode({
    required String phone,
    required String otp,
    required String newPassword,
  }) async {
    _lastAuthError = null;

    if (phone.trim().isEmpty ||
        otp.trim().isEmpty ||
        newPassword.trim().isEmpty) {
      _lastAuthError = 'Phone, recovery code, and new password are required.';
      return false;
    }

    try {
      await _api.resetPasswordWithRecoveryCode(
        phone: phone.trim(),
        otp: otp.trim(),
        newPassword: newPassword.trim(),
      );
      return true;
    } catch (error) {
      _lastAuthError = _readBackendError(error, 'Could not reset password.');
      return false;
    }
  }

  void login(String name, String role) {
    _isLoggedIn = true;
    _userRole = role;

    if (role.toLowerCase() == 'admin') {
      _adminName = name.trim().isEmpty ? _adminName : name.trim();
      _userName = displayName;
      _saveAccountState();
    } else {
      _userName = name.trim().isEmpty
          ? (_userAccountUsername.trim().isNotEmpty
                ? _userAccountUsername.trim()
                : 'User')
          : name.trim();
    }

    touchLastUpdate();
    _startAccountStatusWatcher();
    loadHomeSummary();
    loadFamilyMembers();
    notifyListeners();
  }

  void logout() {
    _isLoggedIn = false;
    _activeAlertCount = 0;
    _homeSummary = null;
    _stopAccountStatusWatcher();
    touchLastUpdate();
    notifyListeners();
  }

  final List<FamilyMember> _familyMembers = [];
  Map<String, String> _familyPhotoDataById = {};

  List<FamilyMember> get familyMembers => List.unmodifiable(_familyMembers);

  Future<void> _loadFamilyPhotoData() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('family_photo_data_by_id') ?? '{}';

    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map) {
        _familyPhotoDataById = decoded.map(
          (key, value) => MapEntry(key.toString(), value.toString()),
        );
      }
    } catch (_) {
      _familyPhotoDataById = {};
    }
  }

  Future<void> _saveFamilyPhotoData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      'family_photo_data_by_id',
      jsonEncode(_familyPhotoDataById),
    );
  }

  FamilyMember _attachLocalPhoto(FamilyMember member) {
    final photo = _familyPhotoDataById[member.id] ?? member.photoData;
    if (photo.trim().isEmpty) return member;
    return member.copyWith(photoData: photo);
  }

  FamilyMember _attachBestPhoto(
    FamilyMember member,
    Map<String, String> remotePhotos,
  ) {
    final remotePhoto = remotePhotos[member.id]?.trim() ?? '';
    final memberPhoto = member.photoData.trim();
    final localPhoto = _familyPhotoDataById[member.id]?.trim() ?? '';
    final bestPhoto = remotePhoto.isNotEmpty
        ? remotePhoto
        : memberPhoto.isNotEmpty
        ? memberPhoto
        : localPhoto;

    if (bestPhoto.isEmpty) return member;

    _familyPhotoDataById[member.id] = bestPhoto;
    return member.copyWith(photoData: bestPhoto);
  }

  Future<void> _syncLocalFamilyPhotosToBackend(
    int homeId,
    Map<String, String> remotePhotos,
  ) async {
    final futures = _familyPhotoDataById.entries.map((entry) async {
      final photo = entry.value.trim();
      if (photo.isEmpty || remotePhotos.containsKey(entry.key)) return;

      try {
        await _api.saveFamilyMemberPhoto(
          homeId: homeId,
          memberId: entry.key,
          photoData: photo,
        );
      } catch (_) {}
    });

    await Future.wait(futures);
  }

  Future<void> loadFamilyMembers() async {
    _familyLoading = true;
    _familyError = null;
    notifyListeners();

    try {
      final currentHomeId = _d7CurrentHomeNumericId();

      if (currentHomeId == null) {
        _familyMembers.clear();
        return;
      }

      await _loadFamilyPhotoData();

      final response = await _api.getFamilyMembers(homeId: currentHomeId);
      final rawMembers = response['members'];

      final remotePhotos = <String, String>{};
      try {
        final photoResponse = await _api.getFamilyMemberPhotos(
          homeId: currentHomeId,
        );
        final rawPhotos = photoResponse['photos'];
        if (rawPhotos is Map) {
          rawPhotos.forEach((key, value) {
            final photo = value?.toString().trim() ?? '';
            if (photo.isNotEmpty) remotePhotos[key.toString()] = photo;
          });
        }
      } catch (_) {}

      _familyMembers
        ..clear()
        ..addAll(
          rawMembers is List
              ? rawMembers
                    .whereType<Map>()
                    .map(
                      (item) => _attachBestPhoto(
                        FamilyMember.fromJson(Map<String, dynamic>.from(item)),
                        remotePhotos,
                      ),
                    )
                    .toList()
              : <FamilyMember>[],
        );

      await _saveFamilyPhotoData();
      await _syncLocalFamilyPhotosToBackend(currentHomeId, remotePhotos);

      touchLastUpdate();
    } catch (error) {
      _familyError = error.toString();
    } finally {
      _familyLoading = false;
      notifyListeners();
    }
  }

  Future<void> addFamilyMember(
    String name,
    String role,
    bool faceEnrolled, {
    String? faceImageData,
  }) async {
    if (!canManageFamily) return;

    final currentHomeId = _d7CurrentHomeNumericId();
    if (currentHomeId == null) return;

    final response = await _api.createFamilyMember(
      homeId: currentHomeId,
      name: name,
      role: role,
      faceEnrolled: faceEnrolled,
      enabled: true,
      faceImageData: faceImageData,
    );

    final member = response['member'];

    if (member is Map) {
      _familyMembers.insert(
        0,
        (() {
          final saved = FamilyMember.fromJson(
            Map<String, dynamic>.from(member),
          );
          final photo = (faceImageData ?? '').trim();
          if (photo.isNotEmpty) {
            _familyPhotoDataById[saved.id] = photo;
            _saveFamilyPhotoData();
            _api.saveFamilyMemberPhoto(
              homeId: currentHomeId,
              memberId: saved.id,
              photoData: photo,
            );
            return saved.copyWith(photoData: photo);
          }
          return _attachLocalPhoto(saved);
        })(),
      );
      touchLastUpdate();
      notifyListeners();
    } else {
      await loadHomeSummary();
      loadFamilyMembers();
    }
  }

  Future<void> deleteFamilyMember(String id) async {
    if (!canManageFamily) return;

    await _api.deleteFamilyMember(id);
    _familyMembers.removeWhere((member) => member.id == id);
    touchLastUpdate();
    notifyListeners();
  }

  Future<void> clearFamilyMembers() async {
    if (!canManageFamily) return;

    final currentHomeId = _d7CurrentHomeNumericId()?.toString();

    await _api.clearFamilyMembers(homeId: currentHomeId);

    _familyMembers.clear();
    touchLastUpdate();
    notifyListeners();

    await loadFamilyMembers();
  }

  Future<void> updateFamilyMember(
    String id,
    String name,
    String role,
    bool faceEnrolled, {
    String? faceImageData,
  }) async {
    if (!canManageFamily) return;

    final currentHomeId = _d7CurrentHomeNumericId();
    if (currentHomeId == null) return;

    final oldMember = _familyMembers.firstWhere(
      (member) => member.id == id,
      orElse: () => FamilyMember(
        id: id,
        name: name,
        role: role,
        faceEnrolled: faceEnrolled,
      ),
    );

    final response = await _api.updateFamilyMember(
      id: id,
      homeId: currentHomeId,
      name: name,
      role: role,
      faceEnrolled: faceEnrolled,
      enabled: oldMember.isEnabled,
      faceImageData: faceImageData,
    );

    final member = response['member'];

    if (member is Map) {
      final index = _familyMembers.indexWhere((item) => item.id == id);
      if (index != -1) {
        final saved = FamilyMember.fromJson(Map<String, dynamic>.from(member));
        final photo = (faceImageData ?? '').trim();
        if (photo.isNotEmpty) {
          _familyPhotoDataById[saved.id] = photo;
          _saveFamilyPhotoData();
          _api.saveFamilyMemberPhoto(
            homeId: currentHomeId,
            memberId: saved.id,
            photoData: photo,
          );
          _familyMembers[index] = saved.copyWith(photoData: photo);
        } else {
          _familyMembers[index] = _attachLocalPhoto(saved);
        }
        touchLastUpdate();
        notifyListeners();
      }
    } else {
      await loadHomeSummary();
      loadFamilyMembers();
    }
  }

  Future<void> toggleFamilyMemberStatus(String id) async {
    if (!canManageFamily) return;

    final index = _familyMembers.indexWhere((member) => member.id == id);
    if (index == -1) return;

    final oldMember = _familyMembers[index];

    final response = oldMember.isEnabled
        ? await _api.disableFamilyMember(id)
        : await _api.enableFamilyMember(id);

    final member = response['member'];

    if (member is Map) {
      _familyMembers[index] = FamilyMember.fromJson(
        Map<String, dynamic>.from(member),
      );
      touchLastUpdate();
      notifyListeners();
    } else {
      await loadHomeSummary();
      loadFamilyMembers();
    }
  }

  final List<Map<String, dynamic>> _doors = [
    {'id': '1', 'nameKey': 'mainDoor', 'isLocked': true},
    {'id': '2', 'nameKey': 'garageDoor', 'isLocked': false},
    {'id': '3', 'nameKey': 'backDoor', 'isLocked': true},
  ];

  List<Map<String, dynamic>> get doors {
    final summaryDoors = homeSummaryDoorDevices;

    if (summaryDoors.isEmpty) {
      return List.unmodifiable(_doors);
    }

    final doorInfo = _d7AsMap(_d7AsMap(_homeSummary)['door']);
    final mainStatus = (doorInfo['status'] ?? '').toString().toLowerCase();

    return List.unmodifiable(
      summaryDoors.asMap().entries.map((entry) {
        final index = entry.key;
        final device = entry.value;

        final id = (device['device_id'] ?? device['id'] ?? index + 1)
            .toString();

        final name =
            (device['device_name'] ??
                    device['name'] ??
                    doorInfo['label'] ??
                    'Main Door')
                .toString();

        final status = index == 0
            ? mainStatus
            : (device['door_status'] ?? device['status'] ?? '')
                  .toString()
                  .toLowerCase();

        final isLocked = status.contains('unlock') || status == 'open'
            ? false
            : true;

        return <String, dynamic>{
          'id': id,
          'deviceId': id,
          'nameKey': name,
          'displayName': name,
          'isLocked': isLocked,
          'raw': device,
        };
      }).toList(),
    );
  }

  void toggleDoorState(String id) {
    if (!canOpenDoor) return;

    final targetDoor = doors.firstWhere(
      (door) => door['id'].toString() == id.toString(),
      orElse: () => <String, dynamic>{},
    );

    final currentLocked = targetDoor['isLocked'] == true;
    setDoorState(id, !currentLocked);
  }

  void setDoorState(String id, bool isLocked) {
    if (!canOpenDoor) return;

    final index = _doors.indexWhere(
      (door) => door['id'].toString() == id.toString(),
    );
    if (index != -1) {
      _doors[index] = {..._doors[index], 'isLocked': isLocked};
    }

    if (_homeSummary != null) {
      final summary = Map<String, dynamic>.from(_homeSummary!);
      final door = Map<String, dynamic>.from(_d7AsMap(summary['door']));

      door['status'] = isLocked ? 'locked' : 'unlocked';
      door['status_text'] = isLocked ? 'Locked' : 'Unlocked';
      door['last_event'] = _formatDateTime(DateTime.now());

      summary['door'] = door;
      _homeSummary = summary;
    }

    touchLastUpdate();
    notifyListeners();
  }

  Future<bool> openDoorFromAlert() async {
    if (!canOpenDoor) return false;

    try {
      await _api.openDoor(
        source: 'flutter_alert',
        reason: 'unknown_face_alert_open',
        openedBy: _userName,
      );

      setDoorState('1', false);
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _stopAccountStatusWatcher();
    _api.close();
    super.dispose();
  }
}

class FamilyMember {
  final String id;
  final String name;
  final String role;
  final bool faceEnrolled;
  final String photoData;
  final bool isEnabled;
  final String createdAt;
  final String updatedAt;

  FamilyMember({
    required this.id,
    required this.name,
    required this.role,
    required this.faceEnrolled,
    this.photoData = '',
    this.isEnabled = true,
    this.createdAt = '',
    this.updatedAt = '',
  });

  bool get hasPhoto => photoData.trim().isNotEmpty;

  String get addedAtLabel {
    final raw = createdAt.trim().isNotEmpty
        ? createdAt.trim()
        : updatedAt.trim();
    return _formatFamilyMemberDate(raw);
  }

  String _formatFamilyMemberDate(String raw) {
    return DateFormatter.formatFamilyDate(raw);
  }

  FamilyMember copyWith({
    String? id,
    String? name,
    String? role,
    bool? faceEnrolled,
    bool? isEnabled,
    String? createdAt,
    String? updatedAt,
    String? photoData,
  }) {
    return FamilyMember(
      id: id ?? this.id,
      name: name ?? this.name,
      role: role ?? this.role,
      faceEnrolled: faceEnrolled ?? this.faceEnrolled,
      isEnabled: isEnabled ?? this.isEnabled,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      photoData: photoData ?? this.photoData,
    );
  }

  factory FamilyMember.fromJson(Map<String, dynamic> json) {
    bool readBool(List<String> keys, {bool fallback = false}) {
      for (final key in keys) {
        final value = json[key];

        if (value is bool) return value;
        if (value is num) return value != 0;

        final text = value?.toString().toLowerCase();
        if (text == 'true' || text == '1' || text == 'yes' || text == 'enabled')
          return true;
        if (text == 'false' ||
            text == '0' ||
            text == 'no' ||
            text == 'disabled')
          return false;
      }

      return fallback;
    }

    return FamilyMember(
      id: (json['id'] ?? json['raw_id'] ?? '').toString(),
      name: (json['name'] ?? 'Unknown').toString(),
      role: 'Family',
      faceEnrolled: readBool(['faceEnrolled', 'face_enrolled']),
      photoData:
          (json['photoData'] ??
                  json['photo_data'] ??
                  json['face_image_data'] ??
                  '')
              .toString(),
      isEnabled: readBool(['isEnabled', 'enabled'], fallback: true),
      createdAt: (json['createdAt'] ?? json['created_at'] ?? '').toString(),
      updatedAt: (json['updatedAt'] ?? json['updated_at'] ?? '').toString(),
    );
  }
}
