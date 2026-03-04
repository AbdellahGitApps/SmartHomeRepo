import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';

enum DeviceType { door, electricity, energy, alert }

class DeviceModel {
  final String id;
  final String titleKey; // L10n key
  final DeviceType type;
  bool isActive;
  String statusKey;

  DeviceModel({
    required this.id,
    required this.titleKey,
    required this.type,
    this.isActive = false,
    required this.statusKey,
  });

  IconData get icon {
    switch (type) {
      case DeviceType.door:
        return LucideIcons.lock;
      case DeviceType.electricity:
        return LucideIcons.zap;
      case DeviceType.energy:
        return LucideIcons.lineChart; // Using lineChart for energy
      case DeviceType.alert:
        return LucideIcons.bellRing;
    }
  }
}
