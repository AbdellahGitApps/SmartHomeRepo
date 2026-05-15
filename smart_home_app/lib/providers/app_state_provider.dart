import 'package:flutter/material.dart';

class AppStateProvider with ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;
  Locale _locale = const Locale('en');
  bool _isLoggedIn = false;
  String _userName = '1';
  String _userRole = 'Admin';
  String _password = '1';

  // --- Network Settings ---
  String _serverIp = '192.168.1.100';
  String _cameraUrl = 'http://192.168.1.100:8080/video_feed';
  String _homeCode = 'HOME2025';

  // --- Security Settings ---
  String _userPin = '1234';
  bool _appLockEnabled = false;

  ThemeMode get themeMode => _themeMode;
  Locale get locale => _locale;
  bool get isLoggedIn => _isLoggedIn;
  String get userName => _userName;
  String get userRole => _userRole;
  String get password => _password;

  String get serverIp => _serverIp;
  String get cameraUrl => _cameraUrl;
  String get homeCode => _homeCode;
  String get userPin => _userPin;
  bool get appLockEnabled => _appLockEnabled;

  void toggleTheme(bool isDark) {
    _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
  }

  void switchLanguage(String languageCode) {
    _locale = Locale(languageCode);
    notifyListeners();
  }

  void updateName(String newName) {
    _userName = newName;
    notifyListeners();
  }

  void updatePassword(String newPassword) {
    _password = newPassword;
    notifyListeners();
  }

  void updateNetworkSettings({String? serverIp, String? cameraUrl, String? homeCode}) {
    if (serverIp != null) _serverIp = serverIp;
    if (cameraUrl != null) _cameraUrl = cameraUrl;
    if (homeCode != null) _homeCode = homeCode;
    notifyListeners();
  }

  void updateSecuritySettings({String? pin, bool? appLock}) {
    if (pin != null && pin != _userPin) {
      _userPin = pin;
      _isLoggedIn = false; // Invalidate session on PIN change
    }
    if (appLock != null) _appLockEnabled = appLock;
    notifyListeners();
  }

  void resetToDefaults() {
    _serverIp = '192.168.1.100';
    _cameraUrl = 'http://192.168.1.100:8080/video_feed';
    _homeCode = 'HOME2025';
    _userPin = '1234';
    _password = '1';
    _appLockEnabled = false;
    notifyListeners();
  }

  void login(String name, String role) {
    _isLoggedIn = true;
    _userName = name;
    _userRole = role;
    notifyListeners();
  }

  void logout() {
    _isLoggedIn = false;
    notifyListeners();
  }

  // --- Family Members Module ---
  final List<FamilyMember> _familyMembers = [
    FamilyMember(id: '1', name: 'Abdullah', role: 'Admin', faceEnrolled: true),
    FamilyMember(id: '2', name: 'Sarah', role: 'Family', faceEnrolled: true),
    FamilyMember(id: '3', name: 'Hamza', role: 'Family', faceEnrolled: false),
  ];

  List<FamilyMember> get familyMembers => List.unmodifiable(_familyMembers);

  void addFamilyMember(String name, String role, bool faceEnrolled) {
    final newMember = FamilyMember(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      name: name,
      role: role,
      faceEnrolled: faceEnrolled,
    );
    _familyMembers.add(newMember);
    notifyListeners();
  }

  void deleteFamilyMember(String id) {
    _familyMembers.removeWhere((m) => m.id == id);
    notifyListeners();
  }
}

class FamilyMember {
  final String id;
  final String name;
  final String role;
  final bool faceEnrolled;

  FamilyMember({
    required this.id,
    required this.name,
    required this.role,
    required this.faceEnrolled,
  });
}
