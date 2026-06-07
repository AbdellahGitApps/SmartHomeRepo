import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_home_app/providers/app_state_provider.dart';
import '../l10n/app_localizations.dart';
import '../services/backend_api_service.dart';
import '../utils/date_formatter.dart';
import 'package:lucide_icons/lucide_icons.dart';

class DoorsScreen extends StatefulWidget {
  const DoorsScreen({super.key});

  @override
  State<DoorsScreen> createState() => _DoorsScreenState();
}

class _DoorsScreenState extends State<DoorsScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _listController;
  final BackendApiService _api = BackendApiService();

  final List<Map<String, dynamic>> _accessLog = [];
  bool _accessLogLoading = false;
  String _selectedAccessDate = 'all';
  String _selectedAccessActor = 'all';

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _listController.forward();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadAccessLogs());
  }

  @override
  void dispose() {
    _api.close();
    _listController.dispose();
    super.dispose();
  }

  String _getDoorName(AppLocalizations l10n, String nameKey) {
    switch (nameKey) {
      case 'mainDoor':
        return l10n.mainDoor;
      case 'garageDoor':
        return l10n.garageDoor;
      case 'backDoor':
        return l10n.backDoor;
      default:
        return nameKey;
    }
  }

  String _nowText() {
    return _formatLogTime(DateTime.now().toIso8601String());
  }

  String _formatLogTime(dynamic value) {
    return DateFormatter.formatDoorsDate(value?.toString());
  }

  void _addAccessLog({required String doorKey, required bool granted}) {
    setState(() {
      _accessLog.insert(0, {
        'doorKey': doorKey,
        'userKey': granted ? 'greeting' : null,
        'method': 'manualApp',
        'result': granted ? 'accessGranted' : 'accessDenied',
        'time': _nowText(),
      });
    });
  }

  String _asText(dynamic value) => (value ?? '').toString().trim();

  Future<void> _loadAccessLogs() async {
    if (_accessLogLoading) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    setState(() {
      _accessLogLoading = true;
    });

    try {
      final response = await _api.getDoorAccessLogs(
        homeId: appState.homeDbId,
        homeCode: appState.homeCode,
        adminLogin: appState.adminName,
        viewerRole: appState.userRole,
      );

      final rawItems = response['items'];

      if (!mounted) return;

      setState(() {
        _accessLog
          ..clear()
          ..addAll(
            rawItems is List
                ? rawItems
                      .whereType<Map>()
                      .map((item) => Map<String, dynamic>.from(item))
                      .toList()
                : <Map<String, dynamic>>[],
          );
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _accessLog.clear();
      });
    } finally {
      if (!mounted) return;

      setState(() {
        _accessLogLoading = false;
      });
    }
  }

  Future<void> _refreshDoorPage() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    await appState.loadHomeSummary();
    await _loadAccessLogs();
  }

  String _doorDeviceId(Map<String, dynamic> door) {
    return (door['deviceId'] ?? door['device_id'] ?? door['id'] ?? '')
        .toString();
  }

  String _doorDeviceName(Map<String, dynamic> door) {
    return (door['displayName'] ??
            door['device_name'] ??
            door['name'] ??
            door['nameKey'] ??
            _doorDeviceId(door))
        .toString();
  }

  void _showPinDialog(BuildContext context, Map<String, dynamic> door) {
    final l10n = AppLocalizations.of(context)!;
    final pinController = TextEditingController();
    String? pinError;
    bool isSubmitting = false;

    showDialog(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24),
              ),
              title: Row(
                children: [
                  Icon(
                    LucideIcons.shieldCheck,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(width: 12),
                  Text(l10n.manualUnlock),
                ],
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(l10n.enterPin),
                  const SizedBox(height: 16),
                  TextField(
                    controller: pinController,
                    obscureText: true,
                    keyboardType: TextInputType.number,
                    maxLength: 4,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 24,
                      letterSpacing: 12,
                      fontWeight: FontWeight.bold,
                    ),
                    decoration: InputDecoration(
                      hintText: '• • • •',
                      counterText: '',
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      errorText: pinError,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: isSubmitting
                      ? null
                      : () => Navigator.pop(dialogContext),
                  child: Text(l10n.cancel),
                ),
                ElevatedButton(
                  onPressed: isSubmitting
                      ? null
                      : () async {
                          final expectedDoorPin = Provider.of<AppStateProvider>(
                            context,
                            listen: false,
                          ).doorPin.trim();

                          if (expectedDoorPin.isEmpty ||
                              pinController.text.trim() != expectedDoorPin) {
                            setDialogState(() {
                              pinError = l10n.pinError;
                            });
                            return;
                          }

                          setDialogState(() {
                            isSubmitting = true;
                            pinError = null;
                          });

                          final appState = Provider.of<AppStateProvider>(
                            context,
                            listen: false,
                          );

                          try {
                            final doorDeviceId = _doorDeviceId(door);
                            final doorDeviceName = _doorDeviceName(door);
                            final actorName =
                                appState.adminName.trim().isNotEmpty
                                ? appState.adminName
                                : appState.userName;

                            await _api.logDoorManualAction(
                              action: 'open',
                              homeId: appState.homeDbId,
                              homeCode: appState.homeCode,
                              deviceId: doorDeviceId,
                              deviceName: doorDeviceName,
                              source: 'flutter_app',
                              actor: actorName,
                              reason: 'manual_open_from_flutter',
                            );

                            if (!mounted) return;

                            appState.setDoorState(door['id'], false);
                            await _refreshDoorPage();

                            Navigator.pop(dialogContext);

                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(l10n.doorUnlockedManually),
                                backgroundColor: Colors.green,
                                behavior: SnackBarBehavior.floating,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                            );
                          } catch (error) {
                            setDialogState(() {
                              isSubmitting = false;
                              pinError = 'Backend error';
                            });

                            if (!mounted) return;

                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Door backend error: $error'),
                                backgroundColor: Colors.red,
                                behavior: SnackBarBehavior.floating,
                              ),
                            );
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).primaryColor,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: isSubmitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : Text(l10n.unlock),
                ),
              ],
            );
          },
        );
      },
    );
  }

  List<String> get _accessLogDates {
    final dates = <String>{};

    for (final log in _accessLog) {
      final raw = (log['timestamp'] ?? log['time'] ?? '').toString();

      if (raw.length >= 10) {
        dates.add(raw.substring(0, 10));
      }
    }

    final sorted = dates.toList()..sort((a, b) => b.compareTo(a));
    return ['all', ...sorted];
  }

  List<String> get _accessLogActors {
    final actors = <String>{};

    for (final log in _accessLog) {
      final actor = (log['actor'] ?? log['user'] ?? log['userKey'] ?? '')
          .toString()
          .trim();

      if (actor.isNotEmpty) {
        actors.add(actor);
      }
    }

    final sorted = actors.toList()..sort();
    return ['all', ...sorted];
  }

  List<Map<String, dynamic>> get _filteredAccessLogs {
    return _accessLog.where((log) {
      final rawDate = (log['timestamp'] ?? log['time'] ?? '').toString();
      final date = rawDate.length >= 10 ? rawDate.substring(0, 10) : rawDate;

      final actor = (log['actor'] ?? log['user'] ?? log['userKey'] ?? '')
          .toString()
          .trim();

      final dateOk =
          _selectedAccessDate == 'all' || date == _selectedAccessDate;
      final actorOk =
          _selectedAccessActor == 'all' || actor == _selectedAccessActor;

      return dateOk && actorOk;
    }).toList();
  }

  Future<bool> _confirmAccessLogDelete(String message) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete log'),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    return result == true;
  }

  Future<void> _deleteSingleAccessLog(Map<String, dynamic> log) async {
    final ok = await _confirmAccessLogDelete('Delete this access log event?');

    if (!ok) return;

    final sourceTable = (log['source_table'] ?? 'system_logs').toString();
    final sourceId = (log['source_id'] ?? log['id'] ?? '').toString();

    if (sourceId.isEmpty) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    await _api.deleteDoorAccessLog(
      sourceTable: sourceTable,
      sourceId: sourceId,
      homeId: appState.homeDbId,
      homeCode: appState.homeCode,
      adminLogin: appState.adminName,
      viewerRole: appState.userRole,
    );

    await _loadAccessLogs();
  }

  Future<void> _deleteFilteredAccessLogs() async {
    final ok = await _confirmAccessLogDelete(
      'Delete access logs matching the selected filters?',
    );

    if (!ok) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    await _api.bulkDeleteDoorAccessLogs(
      homeId: appState.homeDbId,
      homeCode: appState.homeCode,
      adminLogin: appState.adminName,
      viewerRole: appState.userRole,
      date: _selectedAccessDate,
      actor: _selectedAccessActor,
    );

    if (mounted) {
      setState(() {
        _selectedAccessDate = 'all';
        _selectedAccessActor = 'all';
      });
    }

    await _loadAccessLogs();
  }

  Widget _buildAccessLogFilters(BuildContext context, bool isDark) {
    Widget dateFilter() {
      return DropdownButtonFormField<String>(
        initialValue: _accessLogDates.contains(_selectedAccessDate)
            ? _selectedAccessDate
            : 'all',
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Date',
          border: OutlineInputBorder(),
        ),
        items: _accessLogDates
            .map(
              (date) => DropdownMenuItem(
                value: date,
                child: Text(
                  date == 'all' ? 'All Dates' : date,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            )
            .toList(),
        onChanged: (value) {
          setState(() {
            _selectedAccessDate = value ?? 'all';
          });
        },
      );
    }

    Widget actorFilter() {
      return DropdownButtonFormField<String>(
        initialValue: _accessLogActors.contains(_selectedAccessActor)
            ? _selectedAccessActor
            : 'all',
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'Actor',
          border: OutlineInputBorder(),
        ),
        items: _accessLogActors
            .map(
              (actor) => DropdownMenuItem(
                value: actor,
                child: Text(
                  actor == 'all' ? 'All Actors' : actor,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            )
            .toList(),
        onChanged: (value) {
          setState(() {
            _selectedAccessActor = value ?? 'all';
          });
        },
      );
    }

    Widget deleteButton({bool wide = false}) {
      return SizedBox(
        width: wide ? double.infinity : null,
        child: OutlinedButton.icon(
          onPressed: _filteredAccessLogs.isEmpty
              ? null
              : _deleteFilteredAccessLogs,
          icon: const Icon(LucideIcons.trash2, color: Colors.red),
          label: const Text('Delete', style: TextStyle(color: Colors.red)),
          style: OutlinedButton.styleFrom(
            side: const BorderSide(color: Colors.red),
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18),
          ),
        ),
      );
    }

    return Container(
      margin: const EdgeInsets.fromLTRB(24, 18, 24, 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF111827) : Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: isDark
            ? []
            : [
                BoxShadow(
                  color: Colors.black.withOpacity(0.04),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 520;

          if (compact) {
            return Column(
              children: [
                dateFilter(),
                const SizedBox(height: 12),
                actorFilter(),
                const SizedBox(height: 12),
                deleteButton(wide: true),
              ],
            );
          }

          return Row(
            children: [
              Expanded(child: dateFilter()),
              const SizedBox(width: 12),
              Expanded(child: actorFilter()),
              const SizedBox(width: 12),
              deleteButton(),
            ],
          );
        },
      ),
    );
  }

  Color _accessLogVisualColor(String label) {
    final value = label.toLowerCase();

    if (value.contains('unknown face') ||
        value.contains('pending') ||
        value.contains('waiting')) {
      return Colors.orange;
    }

    if (value.contains('opened') ||
        value.contains('enabled') ||
        value.contains('granted')) {
      return Colors.green;
    }

    if (value.contains('restart')) {
      return Colors.orange;
    }

    return Colors.red;
  }

  IconData _accessLogIcon(String label) {
    final value = label.toLowerCase();

    if (value.contains('restart')) return LucideIcons.rotateCcw;
    if (value.contains('opened') ||
        value.contains('enabled') ||
        value.contains('granted')) {
      return LucideIcons.shieldCheck;
    }

    return LucideIcons.shieldAlert;
  }

  Widget _buildAccessLogTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    if (_accessLogLoading && _filteredAccessLogs.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    return Column(
      children: [
        _buildAccessLogFilters(context, isDark),
        Expanded(
          child: _filteredAccessLogs.isEmpty
              ? Center(child: Text(l10n.noAccessLogs))
              : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                  itemCount: _filteredAccessLogs.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final log = _filteredAccessLogs[index];

                    final customResult = _asText(log['resultLabel']);
                    final result = customResult.isNotEmpty
                        ? customResult
                        : log['result'] == 'accessGranted'
                        ? l10n.accessGranted
                        : l10n.accessDenied;

                    final color = _accessLogVisualColor(result);
                    final door = _asText(log['door']).isNotEmpty
                        ? _asText(log['door'])
                        : _getDoorName(l10n, log['doorKey']);

                    final actor = _asText(log['actor']).isNotEmpty
                        ? _asText(log['actor'])
                        : _asText(log['user']).isNotEmpty
                        ? _asText(log['user'])
                        : _asText(log['userKey']).isNotEmpty
                        ? _asText(log['userKey'])
                        : 'Server';

                    final customMethod = _asText(log['methodLabel']);
                    final method = customMethod.isNotEmpty
                        ? customMethod
                        : log['method'] == 'aiRecognition'
                        ? l10n.aiRecognition
                        : l10n.manualApp;

                    return Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: isDark
                            ? Theme.of(context).colorScheme.surface
                            : Theme.of(context).cardColor,
                        borderRadius: BorderRadius.circular(20),
                        border: isDark
                            ? Border.all(
                                color: const Color(0xFF334155),
                                width: 1,
                              )
                            : null,
                        boxShadow: isDark
                            ? []
                            : [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.03),
                                  blurRadius: 8,
                                  offset: const Offset(0, 3),
                                ),
                              ],
                      ),
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final compact = constraints.maxWidth < 390;

                          return Row(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: color.withOpacity(0.12),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  _accessLogIcon(result),
                                  color: color,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '$door — $actor',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(
                                        context,
                                      ).textTheme.titleMedium,
                                    ),
                                    const SizedBox(height: 6),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 5,
                                      crossAxisAlignment:
                                          WrapCrossAlignment.center,
                                      children: [
                                        Container(
                                          padding: const EdgeInsets.symmetric(
                                            horizontal: 8,
                                            vertical: 3,
                                          ),
                                          decoration: BoxDecoration(
                                            color: color.withOpacity(0.12),
                                            borderRadius: BorderRadius.circular(
                                              8,
                                            ),
                                          ),
                                          child: Text(
                                            result,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyle(
                                              color: color,
                                              fontSize: compact ? 10 : 11,
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ),
                                        ConstrainedBox(
                                          constraints: BoxConstraints(
                                            maxWidth: compact ? 110 : 160,
                                          ),
                                          child: Text(
                                            method,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: Theme.of(context)
                                                .textTheme
                                                .bodySmall
                                                ?.copyWith(
                                                  fontSize: compact ? 11 : null,
                                                ),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 5),
                                    Text(
                                      log['time_label'] ??
                                          _formatLogTime(
                                            log['timestamp'] ?? log['time'],
                                          ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(
                                        context,
                                      ).textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ),
                              compact
                                  ? IconButton(
                                      onPressed: () =>
                                          _deleteSingleAccessLog(log),
                                      icon: const Icon(
                                        LucideIcons.trash2,
                                        color: Colors.red,
                                        size: 20,
                                      ),
                                    )
                                  : TextButton.icon(
                                      onPressed: () =>
                                          _deleteSingleAccessLog(log),
                                      icon: const Icon(
                                        LucideIcons.trash2,
                                        color: Colors.red,
                                        size: 18,
                                      ),
                                      label: const Text(
                                        'Delete',
                                        style: TextStyle(color: Colors.red),
                                      ),
                                    ),
                            ],
                          );
                        },
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    if (appState.isUser) {
      return Scaffold(
        appBar: AppBar(
          title: Text(l10n.doors),
          actions: [
            IconButton(
              tooltip: 'Refresh',
              onPressed: _accessLogLoading ? null : _refreshDoorPage,
              icon: _accessLogLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh, size: 20),
            ),
          ],
        ),
        body: Column(
          children: [
            _buildAccessLogFilters(context, isDark),
            Expanded(
              child: _accessLogLoading && _filteredAccessLogs.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : _filteredAccessLogs.isEmpty
                  ? Center(child: Text(l10n.noAccessLogs))
                  : ListView.separated(
                      padding: const EdgeInsets.all(24.0),
                      itemCount: _filteredAccessLogs.length,
                      separatorBuilder: (context, index) =>
                          const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final log = _filteredAccessLogs[index];
                        bool isGranted = log['result'] == 'accessGranted';
                        String door = _getDoorName(l10n, log['doorKey']);
                        final customUser = _asText(log['user']);
                        String user = customUser.isNotEmpty
                            ? customUser
                            : log['userKey'] != null
                            ? l10n.greeting
                            : l10n.unknownPerson;
                        final customMethod = _asText(log['methodLabel']);
                        String method = customMethod.isNotEmpty
                            ? customMethod
                            : log['method'] == 'aiRecognition'
                            ? l10n.aiRecognition
                            : l10n.manualApp;
                        final customResult = _asText(log['resultLabel']);
                        String result = customResult.isNotEmpty
                            ? customResult
                            : isGranted
                            ? l10n.accessGranted
                            : l10n.accessDenied;
                        final resultLower = result.toLowerCase();
                        final rawResultKey = _asText(
                          log['result'],
                        ).toLowerCase();

                        final isRestart = resultLower.contains('restart');

                        final isPendingUnknown =
                            (resultLower.contains('unknown face detected') ||
                                resultLower.contains('pending') ||
                                resultLower.contains('waiting')) &&
                            !resultLower.contains('opened') &&
                            !resultLower.contains('denied') &&
                            !resultLower.contains('after family add') &&
                            !resultLower.contains('granted');

                        final isAccessGranted =
                            rawResultKey == 'accessgranted' ||
                            resultLower.contains('opened once') ||
                            resultLower.contains('door opened') ||
                            resultLower.contains('manual door opened') ||
                            resultLower.contains('after family add') ||
                            resultLower.contains(
                              'family member access granted',
                            ) ||
                            resultLower.contains('access granted');

                        final isAccessDenied =
                            rawResultKey == 'accessdenied' ||
                            resultLower.contains('denied') ||
                            resultLower.contains('access denied') ||
                            resultLower.contains('manual door locked') ||
                            resultLower.contains('door locked') ||
                            resultLower.contains('disabled');

                        final resultColor = (isPendingUnknown || isRestart)
                            ? Colors.orange
                            : isAccessGranted
                            ? Colors.green
                            : isAccessDenied
                            ? Colors.red
                            : isGranted
                            ? Colors.green
                            : Colors.red;

                        final resultIcon = isRestart
                            ? LucideIcons.refreshCcw
                            : isAccessGranted
                            ? LucideIcons.shieldCheck
                            : LucideIcons.shieldAlert;

                        return Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: isDark
                                ? Theme.of(context).colorScheme.surface
                                : Theme.of(context).cardColor,
                            borderRadius: BorderRadius.circular(20),
                            border: isDark
                                ? Border.all(
                                    color: const Color(0xFF334155),
                                    width: 1,
                                  )
                                : null,
                            boxShadow: isDark
                                ? []
                                : [
                                    BoxShadow(
                                      color: Colors.black.withOpacity(0.03),
                                      blurRadius: 8,
                                      offset: const Offset(0, 3),
                                    ),
                                  ],
                          ),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: resultColor.withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  resultIcon,
                                  color: resultColor,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '$door — $user',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: Theme.of(
                                        context,
                                      ).textTheme.titleMedium,
                                    ),
                                    const SizedBox(height: 4),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 4,
                                      crossAxisAlignment:
                                          WrapCrossAlignment.center,
                                      children: [
                                        ConstrainedBox(
                                          constraints: const BoxConstraints(
                                            maxWidth: 150,
                                          ),
                                          child: Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 8,
                                              vertical: 3,
                                            ),
                                            decoration: BoxDecoration(
                                              color: resultColor.withOpacity(
                                                0.1,
                                              ),
                                              borderRadius:
                                                  BorderRadius.circular(8),
                                            ),
                                            child: Text(
                                              result,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: TextStyle(
                                                color: resultColor,
                                                fontSize: 10.5,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ),
                                        ),
                                        ConstrainedBox(
                                          constraints: const BoxConstraints(
                                            maxWidth: 120,
                                          ),
                                          child: Text(
                                            method,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: Theme.of(context)
                                                .textTheme
                                                .bodySmall
                                                ?.copyWith(fontSize: 11),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      log['time_label'] ??
                                          _formatLogTime(
                                            log['timestamp'] ?? log['time'],
                                          ),
                                      style: Theme.of(
                                        context,
                                      ).textTheme.bodySmall,
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              IconButton(
                                tooltip: 'Delete',
                                onPressed: () => _deleteSingleAccessLog(log),
                                icon: const Icon(
                                  LucideIcons.trash2,
                                  color: Colors.red,
                                  size: 18,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      );
    }

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.doors),
          actions: [
            IconButton(
              tooltip: 'Refresh',
              onPressed: _accessLogLoading ? null : _refreshDoorPage,
              icon: _accessLogLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh, size: 20),
            ),
          ],
          bottom: TabBar(
            indicatorColor: Theme.of(context).primaryColor,
            labelColor: Theme.of(context).primaryColor,
            tabs: [
              Tab(
                text: l10n.doors,
                icon: const Icon(LucideIcons.doorClosed, size: 18),
              ),
              Tab(
                text: l10n.accessLog,
                icon: const Icon(LucideIcons.clipboardList, size: 18),
              ),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            SafeArea(
              child: ListView.separated(
                padding: const EdgeInsets.all(24.0),
                itemCount: appState.doors.length,
                separatorBuilder: (context, index) =>
                    const SizedBox(height: 16),
                itemBuilder: (context, index) {
                  final door = appState.doors[index];
                  String displayName = _getDoorName(l10n, door['nameKey']);

                  final itemAnimation = Tween<double>(begin: 0, end: 1).animate(
                    CurvedAnimation(
                      parent: _listController,
                      curve: Interval(
                        (index / appState.doors.length).clamp(0.0, 1.0),
                        ((index + 1) / appState.doors.length).clamp(0.0, 1.0),
                        curve: Curves.easeOutCubic,
                      ),
                    ),
                  );

                  return AnimatedBuilder(
                    animation: itemAnimation,
                    builder: (context, child) {
                      return Transform.translate(
                        offset: Offset(0, 30 * (1 - itemAnimation.value)),
                        child: Opacity(
                          opacity: itemAnimation.value,
                          child: child,
                        ),
                      );
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 400),
                      curve: Curves.easeInOut,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 20,
                      ),
                      decoration: BoxDecoration(
                        color: isDark
                            ? Theme.of(context).colorScheme.surface
                            : Theme.of(context).cardColor,
                        borderRadius: BorderRadius.circular(24),
                        border: isDark
                            ? Border.all(
                                color: const Color(0xFF334155),
                                width: 1,
                              )
                            : null,
                        boxShadow: isDark
                            ? []
                            : [
                                BoxShadow(
                                  color: door['isLocked']
                                      ? Colors.black.withOpacity(0.04)
                                      : Colors.red.withOpacity(0.08),
                                  blurRadius: 10,
                                  offset: const Offset(0, 4),
                                ),
                              ],
                      ),
                      child: Column(
                        children: [
                          Row(
                            children: [
                              AnimatedContainer(
                                duration: const Duration(milliseconds: 400),
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: door['isLocked']
                                      ? Theme.of(
                                          context,
                                        ).primaryColor.withOpacity(0.2)
                                      : Colors.red.withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: AnimatedSwitcher(
                                  duration: const Duration(milliseconds: 400),
                                  transitionBuilder: (child, animation) {
                                    return RotationTransition(
                                      turns: Tween<double>(
                                        begin: 0.5,
                                        end: 1,
                                      ).animate(animation),
                                      child: FadeTransition(
                                        opacity: animation,
                                        child: child,
                                      ),
                                    );
                                  },
                                  child: Icon(
                                    door['isLocked']
                                        ? LucideIcons.lock
                                        : LucideIcons.unlock,
                                    key: ValueKey<bool>(door['isLocked']),
                                    color: door['isLocked']
                                        ? Theme.of(context).primaryColor
                                        : Colors.red,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 16),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    displayName,
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleLarge,
                                  ),
                                  const SizedBox(height: 4),
                                  AnimatedDefaultTextStyle(
                                    duration: const Duration(milliseconds: 300),
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium!
                                        .copyWith(
                                          color: door['isLocked']
                                              ? Colors.green
                                              : Colors.red,
                                        ),
                                    child: Text(
                                      door['isLocked'] ? 'Locked' : 'Unlocked',
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          Padding(
                            padding: const EdgeInsets.only(top: 16),
                            child: SizedBox(
                              width: double.infinity,
                              child: door['isLocked']
                                  ? OutlinedButton.icon(
                                      onPressed: () =>
                                          _showPinDialog(context, door),
                                      icon: const Icon(
                                        LucideIcons.unlock,
                                        size: 16,
                                      ),
                                      label: Text(
                                        l10n.unlockManual,
                                        style: const TextStyle(fontSize: 14),
                                      ),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor: Theme.of(
                                          context,
                                        ).primaryColor,
                                        side: BorderSide(
                                          color: Theme.of(
                                            context,
                                          ).primaryColor.withOpacity(0.3),
                                        ),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            16,
                                          ),
                                        ),
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 12,
                                        ),
                                      ),
                                    )
                                  : ElevatedButton.icon(
                                      onPressed: () async {
                                        final doorDeviceId = _doorDeviceId(
                                          door,
                                        );
                                        final doorDeviceName = _doorDeviceName(
                                          door,
                                        );
                                        final actorName =
                                            appState.adminName.trim().isNotEmpty
                                            ? appState.adminName
                                            : appState.userName;

                                        await _api.logDoorManualAction(
                                          action: 'lock',
                                          homeId: appState.homeDbId,
                                          homeCode: appState.homeCode,
                                          deviceId: doorDeviceId,
                                          deviceName: doorDeviceName,
                                          source: 'flutter_app',
                                          actor: actorName,
                                          reason: 'manual_lock_from_flutter',
                                        );

                                        appState.setDoorState(door['id'], true);
                                        await _refreshDoorPage();
                                      },
                                      icon: const Icon(
                                        LucideIcons.lock,
                                        size: 16,
                                      ),
                                      label: Text(
                                        l10n.lockManual,
                                        style: const TextStyle(fontSize: 14),
                                      ),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Theme.of(
                                          context,
                                        ).primaryColor,
                                        foregroundColor: Colors.white,
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(
                                            16,
                                          ),
                                        ),
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 12,
                                        ),
                                      ),
                                    ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            Column(
              children: [
                _buildAccessLogFilters(context, isDark),
                Expanded(
                  child: _accessLogLoading && _filteredAccessLogs.isEmpty
                      ? const Center(child: CircularProgressIndicator())
                      : _filteredAccessLogs.isEmpty
                      ? Center(child: Text(l10n.noAccessLogs))
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(14, 8, 14, 24),
                          itemCount: _filteredAccessLogs.length,
                          separatorBuilder: (context, index) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final log = _filteredAccessLogs[index];
                            bool isGranted = log['result'] == 'accessGranted';
                            String door = _getDoorName(l10n, log['doorKey']);
                            final customUser = _asText(log['user']);
                            String user = customUser.isNotEmpty
                                ? customUser
                                : log['userKey'] != null
                                ? l10n.greeting
                                : l10n.unknownPerson;
                            final customMethod = _asText(log['methodLabel']);
                            String method = customMethod.isNotEmpty
                                ? customMethod
                                : log['method'] == 'aiRecognition'
                                ? l10n.aiRecognition
                                : l10n.manualApp;
                            final customResult = _asText(log['resultLabel']);
                            String result = customResult.isNotEmpty
                                ? customResult
                                : isGranted
                                ? l10n.accessGranted
                                : l10n.accessDenied;
                            final resultLower = result.toLowerCase();
                            final rawResultKey = _asText(
                              log['result'],
                            ).toLowerCase();

                            final isRestart = resultLower.contains('restart');

                            final isPendingUnknown =
                                (resultLower.contains(
                                      'unknown face detected',
                                    ) ||
                                    resultLower.contains('pending') ||
                                    resultLower.contains('waiting')) &&
                                !resultLower.contains('opened') &&
                                !resultLower.contains('denied') &&
                                !resultLower.contains('after family add') &&
                                !resultLower.contains('granted');

                            final isAccessGranted =
                                rawResultKey == 'accessgranted' ||
                                resultLower.contains('opened once') ||
                                resultLower.contains('door opened') ||
                                resultLower.contains('manual door opened') ||
                                resultLower.contains('after family add') ||
                                resultLower.contains(
                                  'family member access granted',
                                ) ||
                                resultLower.contains('access granted');

                            final isAccessDenied =
                                rawResultKey == 'accessdenied' ||
                                resultLower.contains('denied') ||
                                resultLower.contains('access denied') ||
                                resultLower.contains('manual door locked') ||
                                resultLower.contains('door locked') ||
                                resultLower.contains('disabled');

                            final resultColor = (isPendingUnknown || isRestart)
                                ? Colors.orange
                                : isAccessGranted
                                ? Colors.green
                                : isAccessDenied
                                ? Colors.red
                                : isGranted
                                ? Colors.green
                                : Colors.red;

                            final resultIcon = isRestart
                                ? LucideIcons.refreshCcw
                                : isAccessGranted
                                ? LucideIcons.shieldCheck
                                : LucideIcons.shieldAlert;

                            return Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: isDark
                                    ? Theme.of(context).colorScheme.surface
                                    : Theme.of(context).cardColor,
                                borderRadius: BorderRadius.circular(20),
                                border: isDark
                                    ? Border.all(
                                        color: const Color(0xFF334155),
                                        width: 1,
                                      )
                                    : null,
                                boxShadow: isDark
                                    ? []
                                    : [
                                        BoxShadow(
                                          color: Colors.black.withOpacity(0.03),
                                          blurRadius: 8,
                                          offset: const Offset(0, 3),
                                        ),
                                      ],
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(10),
                                    decoration: BoxDecoration(
                                      color: resultColor.withOpacity(0.1),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      resultIcon,
                                      color: resultColor,
                                      size: 20,
                                    ),
                                  ),
                                  const SizedBox(width: 14),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '$door — $user',
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: Theme.of(
                                            context,
                                          ).textTheme.titleMedium,
                                        ),
                                        const SizedBox(height: 4),
                                        Wrap(
                                          spacing: 8,
                                          runSpacing: 4,
                                          crossAxisAlignment:
                                              WrapCrossAlignment.center,
                                          children: [
                                            ConstrainedBox(
                                              constraints: const BoxConstraints(
                                                maxWidth: 150,
                                              ),
                                              child: Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                      horizontal: 8,
                                                      vertical: 3,
                                                    ),
                                                decoration: BoxDecoration(
                                                  color: resultColor
                                                      .withOpacity(0.1),
                                                  borderRadius:
                                                      BorderRadius.circular(8),
                                                ),
                                                child: Text(
                                                  result,
                                                  maxLines: 1,
                                                  overflow:
                                                      TextOverflow.ellipsis,
                                                  style: TextStyle(
                                                    color: resultColor,
                                                    fontSize: 10.5,
                                                    fontWeight: FontWeight.w600,
                                                  ),
                                                ),
                                              ),
                                            ),
                                            ConstrainedBox(
                                              constraints: const BoxConstraints(
                                                maxWidth: 120,
                                              ),
                                              child: Text(
                                                method,
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: Theme.of(context)
                                                    .textTheme
                                                    .bodySmall
                                                    ?.copyWith(fontSize: 11),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          log['time_label'] ??
                                              _formatLogTime(
                                                log['timestamp'] ?? log['time'],
                                              ),
                                          style: Theme.of(
                                            context,
                                          ).textTheme.bodySmall,
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  IconButton(
                                    tooltip: 'Delete',
                                    onPressed: () =>
                                        _deleteSingleAccessLog(log),
                                    icon: const Icon(
                                      LucideIcons.trash2,
                                      color: Colors.red,
                                      size: 18,
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
