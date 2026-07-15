import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import '../services/backend_api_service.dart';
import '../utils/date_formatter.dart';
import '../widgets/add_member_bottom_sheet.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  final BackendApiService _api = BackendApiService();

  int _filterIndex = 0;
  bool _loading = false;
  List<Map<String, dynamic>> _alerts = [];
  final Set<String> _processingAlerts = {};

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback(
      (_) => _loadAlerts(markSeen: true),
    );
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  Future<void> _loadAlerts({bool markSeen = false}) async {
    if (_loading) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    setState(() {
      _loading = true;
    });

    try {
      final response = await _api.fetchAppAlerts(
        homeId: appState.homeDbId,
        homeCode: appState.homeCode,
        adminLogin: appState.adminName,
        viewerRole: appState.userRole,
      );

      final rawAlerts = response['alerts'];
      final items = rawAlerts is List
          ? rawAlerts
                .whereType<Map>()
                .map(
                  (item) =>
                      item.map((key, value) => MapEntry(key.toString(), value)),
                )
                .toList()
          : <Map<String, dynamic>>[];
      items.sort(
        (a, b) => _d7AlertSortMillis(b).compareTo(_d7AlertSortMillis(a)),
      );

      if (!mounted) return;

      setState(() {
        _alerts = items;
      });

      final activeCount = items
          .where((item) => item['isResolved'] != true)
          .length;
      appState.setActiveAlertCount(markSeen ? 0 : activeCount);
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _alerts = [];
      });

      appState.setActiveAlertCount(0);
    } finally {
      if (!mounted) return;

      setState(() {
        _loading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _filteredAlerts {
    if (_filterIndex == 0) return _alerts;

    if (_filterIndex == 1) {
      return _alerts.where((alert) => alert['category'] == 'security').toList();
    }

    return _alerts.where((alert) => alert['category'] == 'system').toList();
  }

  bool _canManageAlerts(BuildContext context) {
    return Provider.of<AppStateProvider>(
      context,
      listen: false,
    ).canManageAlerts;
  }

  String _d7AlertTwo(int value) => value.toString().padLeft(2, '0');

  DateTime? _d7ParseAlertDateTime(String rawValue) {
    var value = rawValue.trim();

    if (value.isEmpty || value.toLowerCase() == 'just now') {
      return null;
    }

    value = value.replaceAll(RegExp(r'\s+'), ' ');

    final hasExplicitTimezone = RegExp(
      r'(Z|[+-]\d{2}:?\d{2})$',
    ).hasMatch(value);

    try {
      final parsed = DateTime.parse(value);
      return parsed.isUtc || hasExplicitTimezone ? parsed.toLocal() : parsed;
    } catch (_) {
      // Try manual formats below.
    }

    final normalized = value.replaceFirst(', ', ' ');

    final match12 = RegExp(
      r'^(\d{4})-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)$',
      caseSensitive: false,
    ).firstMatch(normalized);

    if (match12 != null) {
      final year = int.parse(match12.group(1)!);
      final month = int.parse(match12.group(2)!);
      final day = int.parse(match12.group(3)!);
      var hour = int.parse(match12.group(4)!);
      final minute = int.parse(match12.group(5)!);
      final second = int.tryParse(match12.group(6) ?? '0') ?? 0;
      final period = match12.group(7)!.toUpperCase();

      if (period == 'PM' && hour != 12) hour += 12;
      if (period == 'AM' && hour == 12) hour = 0;

      return DateTime(year, month, day, hour, minute, second);
    }

    final match24 = RegExp(
      r'^(\d{4})-(\d{1,2})-(\d{1,2}) (\d{1,2}):(\d{2})(?::(\d{2}))?$',
    ).firstMatch(normalized);

    if (match24 != null) {
      return DateTime(
        int.parse(match24.group(1)!),
        int.parse(match24.group(2)!),
        int.parse(match24.group(3)!),
        int.parse(match24.group(4)!),
        int.parse(match24.group(5)!),
        int.tryParse(match24.group(6) ?? '0') ?? 0,
      );
    }

    return null;
  }

  int _d7AlertSortMillis(Map<String, dynamic> alert) {
    final raw =
        (alert['timestamp'] ?? alert['created_at'] ?? alert['time'] ?? '')
            .toString();

    final parsed = _d7ParseAlertDateTime(raw);

    return parsed?.millisecondsSinceEpoch ?? 0;
  }

  String _formatTime(DateTime value) {
    return DateFormatter.format(value);
  }

  String _d7FormatAlertDateTime(DateTime value) {
    return DateFormatter.formatWithComma(value);
  }

  String _d7AlertDisplayTime(Map<String, dynamic> alert) {
    final timestamp = (alert['timestamp'] ?? alert['created_at'] ?? '')
        .toString();

    final parsedTimestamp = _d7ParseAlertDateTime(timestamp);
    if (parsedTimestamp != null) {
      return _d7FormatAlertDateTime(parsedTimestamp);
    }

    final fallback = (alert['time'] ?? '').toString();
    final parsedFallback = _d7ParseAlertDateTime(fallback);

    if (parsedFallback != null) {
      return _d7FormatAlertDateTime(parsedFallback);
    }

    return fallback.trim().isEmpty ? 'Just now' : fallback;
  }

  IconData _iconFor(Map<String, dynamic> alert) {
    final type = (alert['type'] ?? '').toString();

    switch (type) {
      case 'unknownFace':
        return LucideIcons.userX;
      case 'highEnergy':
        return LucideIcons.zap;
      case 'deviceOffline':
        return LucideIcons.wifiOff;
      case 'energyMonitor':
        return LucideIcons.gauge;
      case 'passwordRecovery':
        return LucideIcons.keyRound;
      case 'doorEvent':
        return LucideIcons.lock;
      default:
        return LucideIcons.bell;
    }
  }

  Color _mainColor(Map<String, dynamic> alert) {
    final severity = (alert['severity'] ?? '').toString().toLowerCase();

    if (severity == 'error' || severity == 'critical') return Colors.red;
    if (severity == 'warning') return Colors.orange;

    return Colors.green;
  }

  Future<void> _resolveAlert(Map<String, dynamic> alert) async {
    final id = (alert['id'] ?? '').toString();

    if (id.isEmpty) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    await _api.resolveAppAlert(
      id,
      homeId: appState.homeDbId,
      homeCode: appState.homeCode,
      adminLogin: appState.adminName,
      viewerRole: appState.userRole,
    );
    await _loadAlerts();
  }

  Future<void> _deleteAlert(Map<String, dynamic> alert) async {
    final id = (alert['id'] ?? '').toString();

    if (id.isEmpty) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    await _api.hideAppAlert(
      id,
      homeId: appState.homeDbId,
      homeCode: appState.homeCode,
      adminLogin: appState.adminName,
      viewerRole: appState.userRole,
    );
    await _loadAlerts();
  }

  Future<void> _handleUnknownDecision(
    Map<String, dynamic> alert,
    String action, {
    String? memberName,
    bool faceEnrolled = false,
  }) async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final id = (alert['id'] ?? '').toString();

    if (id.isEmpty) return;
    
    if (_processingAlerts.contains(id)) return;
    setState(() {
      _processingAlerts.add(id);
    });

    try {
      await _api.decideAppAlert(
        alertId: id,
        action: action,
        homeId: appState.homeDbId,
        homeCode: appState.homeCode,
        adminLogin: appState.adminName,
        memberName: memberName,
        faceEnrolled: faceEnrolled,
      );

      await _loadAlerts();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.toString().contains('503') || e.toString().contains('offline')
                ? 'Door controller is currently offline. Please check the device connection.'
                : 'Failed to process request. Please try again.',
          ),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          _processingAlerts.remove(id);
        });
      }
    }
  }

  void _addUnknownToFamily(Map<String, dynamic> alert, bool isDark) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final l10n = AppLocalizations.of(context)!;

    AddMemberBottomSheet.show(
      context,
      l10n: l10n,
      appState: appState,
      isDark: isDark,
      fixedRole: 'Family',
      initialFaceEnrolled: true,
      onSaveOverride: (name, role, faceEnrolled) async {
        await _handleUnknownDecision(
          alert,
          'add_family',
          memberName: name,
          faceEnrolled: faceEnrolled,
        );
      },
    );
  }

  Future<void> _markAllAlertsResolved() async {
    final activeAlerts = _alerts.where((alert) {
      final status = (alert['status'] ?? '').toString().toLowerCase();

      return alert['isResolved'] != true &&
          alert['is_resolved'] != true &&
          alert['resolved'] != true &&
          status != 'resolved' &&
          status != 'hidden' &&
          status != 'deleted';
    }).toList();

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final futures = activeAlerts.map((alert) {
      final id = (alert['id'] ?? '').toString();

      if (id.isNotEmpty) {
        return _api.resolveAppAlert(
          id,
          homeId: appState.homeDbId,
          homeCode: appState.homeCode,
          adminLogin: appState.adminName,
          viewerRole: appState.userRole,
        );
      }
      return Future<Map<String, dynamic>>.value({});
    }).toList();

    await Future.wait(futures);

    if (!mounted) return;

    Provider.of<AppStateProvider>(
      context,
      listen: false,
    ).setActiveAlertCount(0);
    await _loadAlerts(markSeen: true);
  }

  Future<void> _clearAlerts() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Clear alerts'),
        content: const Text('Hide all current alerts for this home?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Clear'),
          ),
        ],
      ),
    );

    if (ok != true) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    await _api.clearAppAlerts(
      homeId: appState.homeDbId,
      homeCode: appState.homeCode,
      adminLogin: appState.adminName,
      viewerRole: appState.userRole,
    );

    await _loadAlerts();
  }

  Widget _buildFilterTab(String label, int index, bool isDark) {
    final selected = _filterIndex == index;

    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _filterIndex = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          padding: const EdgeInsets.symmetric(vertical: 14),
          decoration: BoxDecoration(
            color: selected
                ? Theme.of(context).primaryColor
                : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
          ),
          alignment: Alignment.center,
          child: Text(
            label,
            style: TextStyle(
              color: selected
                  ? Colors.white
                  : (isDark ? Colors.white70 : Colors.black87),
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildAlertCard(Map<String, dynamic> alert, bool isDark) {
    final color = _mainColor(alert);
    final resolved =
        alert['isResolved'] == true || alert['is_resolved'] == true;
    String title = (alert['title'] ?? 'Alert').toString();
    String message = (alert['message'] ?? '').toString();
    final time = _d7AlertDisplayTime(alert);
    final status = resolved ? 'Resolved' : 'Active';
    final type = (alert['type'] ?? '').toString();

    String? snapshotPath;

    try {
      final parsed = jsonDecode(message);
      if (parsed is Map) {
        final reason = parsed['reason']?.toString() ?? '';
        final cmd = parsed['command']?.toString() ?? '';
        snapshotPath = parsed['snapshot_file']?.toString() ?? parsed['snapshot_path']?.toString();

        if (reason == 'unknown_face' || type == 'unknownFace') {
          title = 'Unknown Person Detected';
          message = 'An unrecognized person was detected near your entrance.';
        } else if (reason == 'recognized_face' || reason == 'known_face') {
          title = 'Family Member Detected';
          message = 'A family member was recognized successfully.';
        } else if (reason == 'door_unlocked' || cmd == 'open' || reason.contains('manual_open')) {
          title = 'Door Unlocked';
          message = 'Your smart door was unlocked successfully.';
        } else if (reason == 'door_locked' || cmd == 'lock' || reason.contains('manual_lock')) {
          title = 'Door Locked';
          message = 'Your smart door has been locked.';
        } else if (reason == 'access_denied') {
          title = 'Access Denied';
          message = 'An unauthorized access attempt was blocked.';
        } else {
          message = 'System alert registered.';
        }
      }
    } catch (_) {
      final lowerMsg = message.toLowerCase();
      final lowerTitle = title.toLowerCase();

      if (lowerMsg.contains('reason: unknown_face') || lowerTitle.contains('unknown')) {
        title = 'Unknown Person Detected';
        message = 'An unrecognized person was detected near your entrance.';
      } else if (lowerMsg.contains('reason: recognized_face') || lowerMsg.contains('reason: known_face') || lowerTitle.contains('family')) {
        title = 'Family Member Detected';
        message = 'A family member was recognized successfully.';
      } else if (lowerMsg.contains('unlocked') || lowerMsg.contains('manual_open')) {
        title = 'Door Unlocked';
        message = 'Your smart door was unlocked successfully.';
      } else if (lowerMsg.contains('locked') || lowerMsg.contains('manual_lock')) {
        title = 'Door Locked';
        message = 'Your smart door has been locked.';
      } else if (lowerMsg.contains('denied') || lowerMsg.contains('unauthorized')) {
        title = 'Access Denied';
        message = 'An unauthorized access attempt was blocked.';
      }

      final snapMatch = RegExp(r"snapshot_file[^\w]+([\w/.-]+)").firstMatch(message);
      if (snapMatch != null) {
        snapshotPath = snapMatch.group(1);
      } else {
        if (message.trim().startsWith('{')) {
          message = 'System alert registered.';
        }
      }
    }

    final idStr = (alert['id'] ?? '').toString();
    final isProcessing = _processingAlerts.contains(idStr);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF111827) : Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: color.withOpacity(resolved ? 0.15 : 0.35)),
        boxShadow: isDark
            ? []
            : [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 12,
                  offset: const Offset(0, 5),
                ),
              ],
      ),
      child: Opacity(
        opacity: resolved ? 0.55 : (isProcessing ? 0.7 : 1),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(13),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(_iconFor(alert), color: color),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Expanded(
                            child: Text(time.isEmpty ? 'Just now' : time),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: resolved
                                  ? Colors.green.withOpacity(0.12)
                                  : Colors.red.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              status,
                              style: TextStyle(
                                color: resolved ? Colors.green : Colors.red,
                                fontWeight: FontWeight.w700,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                if (true)
                  IconButton(
                    tooltip: 'Delete alert',
                    onPressed: isProcessing ? null : () => _deleteAlert(alert),
                    icon: const Icon(LucideIcons.trash2, color: Colors.red),
                  ),
              ],
            ),
            if (message.isNotEmpty) ...[
              const SizedBox(height: 14),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.07),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Text(message),
              ),
            ],
            if (snapshotPath != null && snapshotPath.isNotEmpty) ...[
              const SizedBox(height: 14),
              OutlinedButton.icon(
                onPressed: () {
                  final url = snapshotPath!.startsWith('/') ? '${_api.baseUrl}$snapshotPath' : snapshotPath!;
                  showDialog(
                    context: context,
                    builder: (ctx) => Dialog(
                      clipBehavior: Clip.antiAlias,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Image.network(
                        url,
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => const Padding(
                          padding: EdgeInsets.all(32),
                          child: Icon(LucideIcons.imageOff, size: 48, color: Colors.grey),
                        ),
                      ),
                    ),
                  );
                },
                icon: const Icon(LucideIcons.image, size: 16),
                label: const Text('View Image'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                ),
              ),
            ],
            if (!resolved && _canManageAlerts(context)) ...[
              const SizedBox(height: 14),
              if (type == 'unknownFace')
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: isProcessing ? null : () => _handleUnknownDecision(alert, 'open'),
                        icon: isProcessing 
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Icon(LucideIcons.unlock, size: 16),
                        label: const Text('Open'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: isProcessing ? null : () => _handleUnknownDecision(alert, 'deny'),
                        icon: isProcessing 
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                            : const Icon(LucideIcons.xCircle, size: 16),
                        label: const Text('Deny'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: isProcessing ? null : () => _addUnknownToFamily(alert, isDark),
                        icon: const Icon(LucideIcons.userPlus, size: 16),
                        label: const Text('Add'),
                      ),
                    ),
                  ],
                )
              else
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: isProcessing ? null : () => _resolveAlert(alert),
                    icon: isProcessing
                        ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(LucideIcons.checkCircle),
                    label: const Text('Resolve'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.green,
                      side: const BorderSide(color: Colors.green),
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final filtered = _filteredAlerts;
    final compactAppBar = MediaQuery.of(context).size.width < 430;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.alerts,
          maxLines: 1,
          overflow: TextOverflow.visible,
          softWrap: false,
          style: TextStyle(fontSize: compactAppBar ? 19 : null),
        ),
        centerTitle: !compactAppBar,
        titleSpacing: compactAppBar ? 0 : null,
        actions: compactAppBar
            ? [
                IconButton(
                  tooltip: 'Refresh',
                  onPressed: () => _loadAlerts(),
                  icon: const Icon(Icons.refresh, size: 20),
                ),
                PopupMenuButton<String>(
                  tooltip: 'More',
                  onSelected: (value) {
                    if (value == 'resolve') {
                      _markAllAlertsResolved();
                    } else if (value == 'clear') {
                      _clearAlerts();
                    }
                  },
                  itemBuilder: (context) => [
                    PopupMenuItem<String>(
                      value: 'resolve',
                      enabled: _alerts.isNotEmpty,
                      child: const Text('Mark All Resolved'),
                    ),
                    PopupMenuItem<String>(
                      value: 'clear',
                      enabled: _alerts.isNotEmpty,
                      child: Text(l10n.clear),
                    ),
                  ],
                ),
                const SizedBox(width: 4),
              ]
            : [
                IconButton(
                  tooltip: 'Refresh',
                  onPressed: () => _loadAlerts(),
                  icon: const Icon(Icons.refresh, size: 20),
                ),
                TextButton(
                  onPressed: _alerts.isEmpty ? null : _markAllAlertsResolved,
                  child: const Text(
                    'Mark All Resolved',
                    style: TextStyle(color: Colors.green),
                  ),
                ),
                TextButton(
                  onPressed: _alerts.isEmpty ? null : _clearAlerts,
                  child: Text(
                    l10n.clear,
                    style: TextStyle(color: Theme.of(context).primaryColor),
                  ),
                ),
                const SizedBox(width: 8),
              ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _loadAlerts(),
        child: Column(
          children: [
            Container(
              margin: const EdgeInsets.fromLTRB(24, 10, 24, 20),
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: isDark
                    ? const Color(0xFF0F172A)
                    : const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  _buildFilterTab(l10n.allAlerts, 0, isDark),
                  _buildFilterTab(l10n.securityAlerts, 1, isDark),
                  _buildFilterTab(l10n.systemAlerts, 2, isDark),
                ],
              ),
            ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : filtered.isEmpty
                  ? ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        const SizedBox(height: 160),
                        Center(child: Text(l10n.noAlerts)),
                      ],
                    )
                  : ListView.builder(
                      physics: const AlwaysScrollableScrollPhysics(),
                      padding: const EdgeInsets.fromLTRB(24, 0, 24, 100),
                      itemCount: filtered.length,
                      itemBuilder: (context, index) {
                        return _buildAlertCard(filtered[index], isDark);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
