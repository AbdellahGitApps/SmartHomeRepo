import 'package:flutter/material.dart';

class AppStateProvider with ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;
  Locale _locale = const Locale('en');
  bool _isLoggedIn = false;
  String _userName = 'Abdullah';
  String _userRole = 'Admin';

  ThemeMode get themeMode => _themeMode;
  Locale get locale => _locale;
  bool get isLoggedIn => _isLoggedIn;
  String get userName => _userName;
  String get userRole => _userRole;

  void toggleTheme(bool isDark) {
    _themeMode = isDark ? ThemeMode.dark : ThemeMode.light;
    notifyListeners();
  }

  void switchLanguage(String languageCode) {
    _locale = Locale(languageCode);
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
}
