import 'package:permission_handler/permission_handler.dart';
import 'dart:developer' as developer;

class PermissionService {
  static Future<bool> requestCameraPermission() async {
    PermissionStatus status = await Permission.camera.status;
    developer.log('Camera Permission Status: $status', name: 'PermissionService');

    if (status.isGranted) return true;

    status = await Permission.camera.request();
    developer.log('Requested Camera Permission: $status', name: 'PermissionService');
    
    return status.isGranted;
  }

  static Future<bool> requestGalleryPermission() async {
    PermissionStatus status = await Permission.photos.status;
    developer.log('Gallery Permission Status: $status', name: 'PermissionService');

    if (status.isGranted) return true;

    status = await Permission.photos.request();
    developer.log('Requested Gallery Permission: $status', name: 'PermissionService');

    return status.isGranted;
  }

  static Future<void> openSettings() async {
    await openAppSettings();
  }
}
