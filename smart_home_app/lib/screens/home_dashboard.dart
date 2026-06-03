import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import '../models/device_model.dart';
import '../widgets/device_card.dart';
import '../services/backend_api_service.dart';
import 'alerts_screen.dart';

class HomeDashboard extends StatefulWidget {
  const HomeDashboard({super.key});

  @override
  State<HomeDashboard> createState() => _HomeDashboardState();
}

class _HomeDashboardState extends State<HomeDashboard>
    with TickerProviderStateMixin {
  late AnimationController _controller;
  late AnimationController _pulseController;
  late Animation<double> _headerFade;
  late Animation<Offset> _headerSlide;
  late Animation<double> _summaryFade;
  late Animation<Offset> _summarySlide;
  late Animation<double> _gridFade;
  late Animation<Offset> _gridSlide;
  late Animation<double> _pulseAnimation;

  final BackendApiService _api = BackendApiService();
  Map<String, dynamic>? _homeSummary;
  bool _homeSummaryLoading = false;
  Timer? _alertPollTimer;

  // Mock Devices
  final List<DeviceModel> _devices = [
    DeviceModel(
      id: '1',
      titleKey: 'electricity',
      type: DeviceType.electricity,
      isActive: true,
      statusKey: 'statusNormal',
    ),
    DeviceModel(
      id: '2',
      titleKey: 'doors',
      type: DeviceType.door,
      isActive: false,
      statusKey: 'statusLocked',
    ),
    DeviceModel(
      id: '3',
      titleKey: 'energy',
      type: DeviceType.energy,
      isActive: true,
      statusKey: 'kW',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Staggered animations
    _headerFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.4, curve: Curves.easeOut),
      ),
    );
    _headerSlide = Tween<Offset>(begin: const Offset(0, -0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.0, 0.4, curve: Curves.easeOut),
          ),
        );

    _summaryFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.2, 0.6, curve: Curves.easeOut),
      ),
    );
    _summarySlide = Tween<Offset>(begin: const Offset(0, 0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.2, 0.6, curve: Curves.easeOut),
          ),
        );

    _gridFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.4, 1.0, curve: Curves.easeOut),
      ),
    );
    _gridSlide = Tween<Offset>(begin: const Offset(0, 0.4), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.4, 1.0, curve: Curves.easeOut),
          ),
        );

    _controller.forward();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadHomeSummary();
      _alertPollTimer?.cancel();
      _alertPollTimer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (mounted) {
          _loadHomeSummary();
        }
      });
    });
  }

  @override
  void dispose() {
    _alertPollTimer?.cancel();
    _controller.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) {
      return value.map((key, val) => MapEntry(key.toString(), val));
    }
    return <String, dynamic>{};
  }

  num _asNum(dynamic value, [num fallback = 0]) {
    if (value is num) return value;

    final parsed = num.tryParse(value?.toString() ?? '');
    return parsed ?? fallback;
  }

  int _countActiveAlertsFromResponse(Map<String, dynamic> response) {
    final rawItems =
        response['alerts'] ?? response['items'] ?? response['logs'] ?? [];

    if (rawItems is! List) return 0;

    return rawItems.where((item) {
      if (item is! Map) return false;

      final status = (item['status'] ?? '').toString().toLowerCase();
      final resolved =
          item['isResolved'] == true ||
          item['is_resolved'] == true ||
          item['resolved'] == true ||
          status == 'resolved' ||
          status == 'hidden' ||
          status == 'deleted';

      return !resolved;
    }).length;
  }

  bool _deviceLooksOnline(Map<String, dynamic> device) {
    final enabled = device['enabled'] ?? device['is_enabled'];
    if (enabled == false) return false;

    final status = [
      device['status'],
      device['claim_status'],
      device['connection_status'],
    ].where((v) => v != null).join(' ').toLowerCase();

    if (status.contains('offline') ||
        status.contains('disabled') ||
        status.contains('inactive') ||
        status.contains('error')) {
      return false;
    }

    return true;
  }

  bool _summaryEnergyDeviceOnline() {
    final energy = _asMap(_homeSummary?['energy']);
    final devices = energy['devices'];

    if (devices is List && devices.isNotEmpty) {
      return _deviceLooksOnline(_asMap(devices.first));
    }

    final status = (energy['status'] ?? '').toString().toLowerCase();

    if (status.contains('offline') ||
        status.contains('disabled') ||
        status.contains('inactive') ||
        status.contains('error')) {
      return false;
    }

    return true;
  }

  bool _summaryDoorDeviceOnline(AppStateProvider appState) {
    final door = _asMap(_homeSummary?['door']);
    final device = _asMap(door['device']);

    if (device.isNotEmpty) {
      return _deviceLooksOnline(device);
    }

    return appState.doors.isNotEmpty;
  }

  Future<void> _loadHomeSummary() async {
    if (_homeSummaryLoading) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    setState(() {
      _homeSummaryLoading = true;
    });

    try {
      final response = await _api.getHomeSummary(
        homeId: appState.homeId,
        homeCode: appState.homeCode,
        adminLogin: appState.adminName,
      );

      try {
        final alertsResponse = await _api.fetchAppAlerts(
          homeId: appState.homeDbId,
          homeCode: appState.homeCode,
          adminLogin: appState.adminName,
        );

        response['alerts_count'] = _countActiveAlertsFromResponse(
          alertsResponse,
        );
      } catch (_) {}

      final alertsValue = response['alerts_count'];
      if (alertsValue is num) {
        appState.setActiveAlertCount(alertsValue.toInt());
      }

      if (!mounted) return;

      setState(() {
        _homeSummary = response;
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _homeSummary = null;
      });
    } finally {
      if (!mounted) return;

      setState(() {
        _homeSummaryLoading = false;
      });
    }
  }

  String _summaryGreeting(AppStateProvider appState) {
    final name = appState.userName.trim().isNotEmpty
        ? appState.userName.trim()
        : appState.userName.trim();

    if (name.isEmpty) return 'Hello';

    return 'Hello, $name';
  }

  String _summaryPowerText(AppLocalizations l10n) {
    final energy = _asMap(_homeSummary?['energy']);

    final powerKw = _asNum(
      energy['power_kw'],
      _asNum(energy['power_w']) / 1000,
    );

    final cleanValue = powerKw % 1 == 0
        ? powerKw.toInt().toString()
        : powerKw.toStringAsFixed(1);

    return '$cleanValue ${l10n.kW}';
  }

  String _summaryEnergyStatus(AppLocalizations l10n) {
    final energy = _asMap(_homeSummary?['energy']);
    final status = (energy['status'] ?? '').toString().toLowerCase();

    if (status.contains('normal')) return l10n.statusNormal;
    if (status.contains('active')) return l10n.statusActive;

    return status.isEmpty ? l10n.statusNormal : status;
  }

  String _summaryElectricityCardStatus(AppLocalizations l10n) {
    final activeLabel = _summaryEnergyDeviceOnline()
        ? l10n.statusActive
        : 'Inactive';

    final usageLabel = _summaryEnergyUsageLevel().trim();

    return '$activeLabel • ${usageLabel.isEmpty ? l10n.statusNormal : usageLabel}';
  }

  String _summaryDoorLabel(AppLocalizations l10n) {
    final door = _asMap(_homeSummary?['door']);
    final label = (door['label'] ?? '').toString().trim();

    return label.isEmpty ? l10n.mainDoor : label;
  }

  bool _summaryDoorIsLocked(AppStateProvider appState) {
    final door = _asMap(_homeSummary?['door']);
    final status = (door['status'] ?? '').toString().toLowerCase();

    if (status.contains('unlock') || status == 'open') return false;
    if (status.contains('lock') || status == 'closed') return true;

    if (appState.doors.isNotEmpty) {
      return appState.doors[0]['isLocked'] == true;
    }

    return true;
  }

  String _summaryDoorStatusText(
    AppLocalizations l10n,
    AppStateProvider appState,
  ) {
    return _summaryDoorIsLocked(appState) ? 'Locked' : 'Unlocked';
  }

  List<Map<String, dynamic>> _summaryDevicesByType(List<String> keywords) {
    final rawDevices = _homeSummary?['devices'];

    if (rawDevices is! List) return <Map<String, dynamic>>[];

    return rawDevices
        .whereType<Map>()
        .map((item) {
          return item.map((key, value) => MapEntry(key.toString(), value));
        })
        .where((device) {
          final text = [
            device['device_type'],
            device['type'],
            device['device_name'],
            device['name'],
            device['device_id'],
          ].where((value) => value != null).join(' ').toLowerCase();

          return keywords.any((keyword) => text.contains(keyword));
        })
        .toList();
  }

  bool _deviceIsOnline(Map<String, dynamic> device) {
    final status = (device['status'] ?? '').toString().toLowerCase();
    final enabled = (device['enabled'] ?? '1').toString().toLowerCase();

    if (enabled == '0' || enabled == 'false' || enabled == 'no') return false;

    if (status.contains('offline') ||
        status.contains('disabled') ||
        status.contains('fault') ||
        status.contains('error')) {
      return false;
    }

    return true;
  }

  bool _summaryEnergyOnline() {
    final devices = _summaryDevicesByType(['energy', 'meter']);
    if (devices.isEmpty) return _homeSummary?['energy'] != null;
    return devices.any(_deviceIsOnline);
  }

  bool _summaryDoorOnline(AppStateProvider appState) {
    final devices = _summaryDevicesByType(['door', 'camera']);
    if (devices.isEmpty) return appState.doors.isNotEmpty;
    return devices.any(_deviceIsOnline);
  }

  String _summaryEnergyUsageLevel() {
    final energy = _asMap(_homeSummary?['energy']);
    final dailyKwh = _asNum(
      energy['kwh_today'],
      _asNum(energy['consumption_kwh'], _asNum(energy['daily_kwh'])),
    );

    if (dailyKwh >= 25) return 'High';
    if (dailyKwh >= 15) return 'Medium';
    return 'Normal';
  }

  int _summaryAlertCount(AppStateProvider appState) {
    return appState.activeAlertCount;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    final summaryAlertCount = _summaryAlertCount(appState);

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Premium Live Status Header
              FadeTransition(
                opacity: _headerFade,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      FadeTransition(
                        opacity: _pulseAnimation,
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: Colors.green,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        l10n.systemSecure,
                        style: TextStyle(
                          color: Colors.green.shade700,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.1,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Animated Header
              SlideTransition(
                position: _headerSlide,
                child: FadeTransition(
                  opacity: _headerFade,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${l10n.welcomeBack},',
                            style: Theme.of(context).textTheme.bodyMedium!
                                .copyWith(
                                  color: Colors.grey,
                                  fontWeight: FontWeight.w500,
                                ),
                          ),
                          Text(
                            appState.userName,
                            style: Theme.of(context).textTheme.headlineSmall!
                                .copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '${l10n.lastUpdate}: ${appState.lastUpdateText}',
                            style: TextStyle(
                              color: isDark
                                  ? Colors.grey.shade400
                                  : Colors.grey.shade600,
                              fontSize: 12,
                            ),
                          ),
                        ],
                      ),
                      Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isDark
                              ? const Color(0xFF1E293B)
                              : Colors.white,
                          boxShadow: isDark
                              ? []
                              : [
                                  BoxShadow(
                                    color: Colors.black.withOpacity(0.05),
                                    blurRadius: 10,
                                  ),
                                ],
                        ),
                        child: Stack(
                          clipBehavior: Clip.none,
                          children: [
                            IconButton(
                              icon: const Icon(LucideIcons.bell),
                              onPressed: () {
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => const AlertsScreen(),
                                  ),
                                );
                              },
                            ),
                            if (summaryAlertCount > 0)
                              Positioned(
                                right: 8,
                                top: 6,
                                child: Container(
                                  padding: const EdgeInsets.all(4),
                                  decoration: const BoxDecoration(
                                    color: Colors.red,
                                    shape: BoxShape.circle,
                                  ),
                                  constraints: const BoxConstraints(
                                    minWidth: 18,
                                    minHeight: 18,
                                  ),
                                  child: Text(
                                    summaryAlertCount > 9
                                        ? '9+'
                                        : summaryAlertCount.toString(),
                                    textAlign: TextAlign.center,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // Animated Home Summary Card (Premium Design)
              SlideTransition(
                position: _summarySlide,
                child: FadeTransition(
                  opacity: _summaryFade,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(32),
                      gradient: LinearGradient(
                        colors: isDark
                            ? [const Color(0xFF334155), const Color(0xFF0F172A)]
                            : [
                                Theme.of(context).primaryColor,
                                Theme.of(context).primaryColor.withOpacity(0.8),
                              ],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Theme.of(
                            context,
                          ).primaryColor.withOpacity(0.3),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: Stack(
                      children: [
                        Positioned(
                          right: -20,
                          top: -20,
                          child: Icon(
                            LucideIcons.home,
                            size: 120,
                            color: Colors.white.withOpacity(0.1),
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _summaryGreeting(appState),
                              style: Theme.of(context).textTheme.titleLarge!
                                  .copyWith(
                                    color: Colors.white,
                                    fontWeight: FontWeight.bold,
                                  ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              _summaryEnergyStatus(l10n),
                              style: const TextStyle(
                                color: Colors.white70,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 32),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                _buildSummaryItem(
                                  l10n.energyConsumption,
                                  _summaryPowerText(l10n),
                                  true, // force light text for gradient card
                                ),
                                _buildSummaryItem(
                                  _summaryDoorLabel(l10n),
                                  _summaryDoorStatusText(l10n, appState),
                                  true,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 32),

              // Animated Devices Grid
              SlideTransition(
                position: _gridSlide,
                child: FadeTransition(
                  opacity: _gridFade,
                  child: LayoutBuilder(
                    builder: (context, constraints) {
                      final spacing = 16.0;
                      final cardWidth = (constraints.maxWidth - spacing) / 2;

                      Widget buildDeviceCard(int index) {
                        final device = _devices[index];
                        String translatedTitle = '';
                        String translatedStatus = '';

                        final energyOnline = _summaryEnergyOnline();
                        final doorOnline = _summaryDoorOnline(appState);

                        if (device.type == DeviceType.electricity) {
                          device.isActive = energyOnline;
                          translatedTitle = l10n.electricity;
                          translatedStatus = energyOnline
                              ? '${l10n.statusActive} • ${_summaryEnergyUsageLevel()}'
                              : 'Inactive • ${_summaryEnergyUsageLevel()}';
                        } else if (device.type == DeviceType.door) {
                          device.isActive = doorOnline;
                          translatedTitle = l10n.doors;
                          translatedStatus = doorOnline
                              ? _summaryDoorStatusText(l10n, appState)
                              : 'Offline';
                        } else if (device.type == DeviceType.energy) {
                          device.isActive = energyOnline;
                          translatedTitle = l10n.energy;
                          translatedStatus = energyOnline
                              ? _summaryPowerText(l10n)
                              : 'Offline';
                        }

                        return SizedBox(
                          width: cardWidth,
                          height: cardWidth / 1.1,
                          child: DeviceCard(
                            device: device,
                            localizedTitle: translatedTitle,
                            localizedStatus: translatedStatus,
                            onTap: null,
                          ),
                        );
                      }

                      return Wrap(
                        alignment: WrapAlignment.center,
                        spacing: spacing,
                        runSpacing: spacing,
                        children: List.generate(_devices.length, buildDeviceCard),
                      );
                    },
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSummaryItem(String label, String value, bool isDark) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium!.copyWith(
            color: isDark ? Colors.white54 : Colors.black54,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge!.copyWith(
            color: isDark ? Colors.white : Colors.black87,
          ),
        ),
      ],
    );
  }
}
