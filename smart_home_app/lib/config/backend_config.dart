import 'dart:io';
import 'package:flutter/foundation.dart';

class BackendConfig {
  static String get defaultBaseUrl {
    if (kReleaseMode) {
      return 'http://127.0.0.1:8000';
    }
    try {
      if (!kIsWeb && Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {}
    return 'http://127.0.0.1:8000';
  }

  static const Duration requestTimeout = Duration(seconds: 12);
}
