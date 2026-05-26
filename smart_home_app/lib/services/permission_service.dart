import 'package:flutter/foundation.dart';
import 'package:permission_handler/permission_handler.dart';

class PermissionService {
  static Future<bool> requestCameraPermission() async {
    if (kIsWeb) return true;

    final status = await Permission.camera.request();
    return status.isGranted;
  }

  static Future<bool> requestGalleryPermission() async {
    if (kIsWeb) return true;

    final status = await Permission.photos.request();
    return status.isGranted || status.isLimited;
  }

  static Future<bool> requestStoragePermission() async {
    if (kIsWeb) return true;

    final status = await Permission.storage.request();
    return status.isGranted;
  }

  static Future<bool> requestMicrophonePermission() async {
    if (kIsWeb) return true;

    final status = await Permission.microphone.request();
    return status.isGranted;
  }

  static Future<bool> openSettings() async {
    if (kIsWeb) return true;

    return openAppSettings();
  }
}
