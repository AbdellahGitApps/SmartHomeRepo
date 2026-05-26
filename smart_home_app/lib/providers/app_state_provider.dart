import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/backend_api_service.dart';

class AppStateProvider with ChangeNotifier {
  final BackendApiService _api = BackendApiService();

  AppStateProvider() {
    _loadSavedAccountState();
  }

  ThemeMode _themeMode = ThemeMode.system;
  Locale _locale = const Locale('en');
  bool _isLoggedIn = false;
  String _userName = 'Ali';
  String _adminName = 'Ali';
  String _userRole = 'Admin';
  String _password = '1';

  String _doorPin = '1234';
  String _userAccountPassword = '123';
  int _activeAlertCount = 3;
  DateTime _lastUpdatedAt = DateTime.now();

  String _serverIp = '192.168.1.100';
  String _cameraUrl = 'http://192.168.1.100:8080/video_feed';
  String _homeCode = 'HOME2025';

  bool _appLockEnabled = false;

  bool _familyLoading = false;
  String? _familyError;

  ThemeMode get themeMode => _themeMode;
  Locale get locale => _locale;
  bool get isLoggedIn => _isLoggedIn;
  String get userName => _userName;
  String get adminName => _adminName;
  String get userRole => _userRole;
  String get password => _password;

  String get doorPin => _doorPin;
  String get userPin => _doorPin;
  String get userAccountPassword => _userAccountPassword;
  int get activeAlertCount => _activeAlertCount;
  String get lastUpdateText => _formatDateTime(_lastUpdatedAt);

  String get serverIp => _serverIp;
  String get cameraUrl => _cameraUrl;
  String get homeCode => _homeCode;
  bool get appLockEnabled => _appLockEnabled;

  bool get isAdmin => _userRole.toLowerCase() == 'admin';
  bool get isUser => _userRole.toLowerCase() == 'user';

  bool get canManageFamily => isAdmin;
  bool get canOpenDoor => isAdmin;
  bool get canManageAlerts => isAdmin;
  bool get canViewFamily => true;
  bool get canViewDoors => isAdmin;

  bool get familyLoading => _familyLoading;
  String? get familyError => _familyError;

  String _two(int value) => value.toString().padLeft(2, '0');

  String _formatDateTime(DateTime value) {
    return '${value.year}-${_two(value.month)}-${_two(value.day)} ${_two(value.hour)}:${_two(value.minute)}:${_two(value.second)}';
  }

  void touchLastUpdate() {
    _lastUpdatedAt = DateTime.now();
  }

  Future<void> _loadSavedAccountState() async {
    final prefs = await SharedPreferences.getInstance();

    _adminName = prefs.getString('admin_name') ?? 'Ali';
    _password = prefs.getString('admin_password') ?? '1';
    _doorPin = prefs.getString('door_pin') ?? '1234';
    _userAccountPassword = prefs.getString('user_account_password') ?? '123';

    if (isAdmin || _userName.trim().isEmpty || _userName == '1') {
      _userName = _adminName;
    }

    notifyListeners();
  }

  Future<void> _saveAccountState() async {
    final prefs = await SharedPreferences.getInstance();

    await prefs.setString('admin_name', _adminName);
    await prefs.setString('admin_password', _password);
    await prefs.setString('door_pin', _doorPin);
    await prefs.setString('user_account_password', _userAccountPassword);
  }

  void toggleTheme(bool isDark) {
    _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
    touchLastUpdate();
    notifyListeners();
  }

  void switchLanguage(String languageCode) {
    _locale = Locale(languageCode);
    touchLastUpdate();
    notifyListeners();
  }

  void updateName(String newName) {
    final cleanName = newName.trim().isEmpty ? 'Ali' : newName.trim();
    _adminName = cleanName;
    if (isAdmin) {
      _userName = cleanName;
    }
    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void updatePassword(String newPassword) {
    if (newPassword.trim().isNotEmpty) {
      _password = newPassword.trim();
      _saveAccountState();
      touchLastUpdate();
      notifyListeners();
    }
  }

  void updateDoorPin(String newPin) {
    _doorPin = newPin;
    touchLastUpdate();
    notifyListeners();
  }

  void updateUserAccountPassword(String newPassword) {
    _userAccountPassword = newPassword;
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
    if (serverIp != null) _serverIp = serverIp;
    if (cameraUrl != null) _cameraUrl = cameraUrl;
    if (homeCode != null) _homeCode = homeCode;
    touchLastUpdate();
    notifyListeners();
  }

  void updateSecuritySettings({String? pin, bool? appLock}) {
    if (pin != null && pin.trim().isNotEmpty) {
      _doorPin = pin.trim();
    }
    if (appLock != null) _appLockEnabled = appLock;
    _saveAccountState();
    touchLastUpdate();
    notifyListeners();
  }

  void resetToDefaults() {
    _serverIp = '192.168.1.100';
    _cameraUrl = 'http://192.168.1.100:8080/video_feed';
    _homeCode = 'HOME2025';
    _doorPin = '1234';
    _userAccountPassword = '123';
    _password = '1';
    _appLockEnabled = false;
    _activeAlertCount = 3;
    touchLastUpdate();
    notifyListeners();
  }

  void login(String name, String role) {
    _isLoggedIn = true;
    _userRole = role;

    if (role.toLowerCase() == 'admin') {
      _adminName = name.trim().isEmpty ? _adminName : name.trim();
      _userName = _adminName;
      _saveAccountState();
    } else {
      _userName = name.trim().isEmpty ? 'User Guest' : name.trim();
    }

    touchLastUpdate();
    loadFamilyMembers();
    notifyListeners();
  }

  void logout() {
    _isLoggedIn = false;
    touchLastUpdate();
    notifyListeners();
  }

  final List<FamilyMember> _familyMembers = [];

  List<FamilyMember> get familyMembers => List.unmodifiable(_familyMembers);

  Future<void> loadFamilyMembers() async {
    _familyLoading = true;
    _familyError = null;
    notifyListeners();

    try {
      final response = await _api.getFamilyMembers();
      final rawMembers = response['members'];

      _familyMembers
        ..clear()
        ..addAll(
          rawMembers is List
              ? rawMembers
                    .whereType<Map>()
                    .map(
                      (item) => FamilyMember.fromJson(
                        Map<String, dynamic>.from(item),
                      ),
                    )
                    .toList()
              : <FamilyMember>[],
        );

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
    bool faceEnrolled,
  ) async {
    if (!canManageFamily) return;

    final response = await _api.createFamilyMember(
      name: name,
      role: role,
      faceEnrolled: faceEnrolled,
      enabled: true,
    );

    final member = response['member'];

    if (member is Map) {
      _familyMembers.insert(
        0,
        FamilyMember.fromJson(Map<String, dynamic>.from(member)),
      );
      touchLastUpdate();
      notifyListeners();
    } else {
      await loadFamilyMembers();
    }
  }

  Future<void> deleteFamilyMember(String id) async {
    if (!canManageFamily) return;

    await _api.deleteFamilyMember(id);
    _familyMembers.removeWhere((member) => member.id == id);
    touchLastUpdate();
    notifyListeners();
  }

  Future<void> updateFamilyMember(
    String id,
    String name,
    String role,
    bool faceEnrolled,
  ) async {
    if (!canManageFamily) return;

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
      name: name,
      role: role,
      faceEnrolled: faceEnrolled,
      enabled: oldMember.isEnabled,
    );

    final member = response['member'];

    if (member is Map) {
      final index = _familyMembers.indexWhere((item) => item.id == id);
      if (index != -1) {
        _familyMembers[index] = FamilyMember.fromJson(
          Map<String, dynamic>.from(member),
        );
        touchLastUpdate();
        notifyListeners();
      }
    } else {
      await loadFamilyMembers();
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
      await loadFamilyMembers();
    }
  }

  final List<Map<String, dynamic>> _doors = [
    {'id': '1', 'nameKey': 'mainDoor', 'isLocked': true},
    {'id': '2', 'nameKey': 'garageDoor', 'isLocked': false},
    {'id': '3', 'nameKey': 'backDoor', 'isLocked': true},
  ];

  List<Map<String, dynamic>> get doors => List.unmodifiable(_doors);

  void toggleDoorState(String id) {
    if (!canOpenDoor) return;

    final index = _doors.indexWhere((door) => door['id'] == id);
    if (index != -1) {
      _doors[index] = {
        ..._doors[index],
        'isLocked': !_doors[index]['isLocked'],
      };
      touchLastUpdate();
      notifyListeners();
    }
  }

  void setDoorState(String id, bool isLocked) {
    if (!canOpenDoor) return;

    final index = _doors.indexWhere((door) => door['id'] == id);
    if (index != -1) {
      _doors[index] = {..._doors[index], 'isLocked': isLocked};
      touchLastUpdate();
      notifyListeners();
    }
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
    _api.close();
    super.dispose();
  }
}

class FamilyMember {
  final String id;
  final String name;
  final String role;
  final bool faceEnrolled;
  final bool isEnabled;

  FamilyMember({
    required this.id,
    required this.name,
    required this.role,
    required this.faceEnrolled,
    this.isEnabled = true,
  });

  factory FamilyMember.fromJson(Map<String, dynamic> json) {
    bool readBool(List<String> keys, {bool fallback = false}) {
      for (final key in keys) {
        final value = json[key];

        if (value is bool) return value;
        if (value is num) return value != 0;

        final text = value?.toString().toLowerCase();
        if (text == 'true' || text == '1' || text == 'yes') return true;
        if (text == 'false' || text == '0' || text == 'no') return false;
      }

      return fallback;
    }

    return FamilyMember(
      id: (json['id'] ?? json['raw_id'] ?? '').toString(),
      name: (json['name'] ?? 'Unknown').toString(),
      role: (json['role'] ?? 'Family').toString(),
      faceEnrolled: readBool(['faceEnrolled', 'face_enrolled']),
      isEnabled: readBool(['isEnabled', 'enabled'], fallback: true),
    );
  }
}
