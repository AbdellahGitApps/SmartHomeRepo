import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:smart_home_app/providers/app_state_provider.dart';
import '../l10n/app_localizations.dart';
import '../services/backend_api_service.dart';
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

  final List<Map<String, dynamic>> _accessLog = [
    {
      'doorKey': 'mainDoor',
      'userKey': 'greeting',
      'method': 'aiRecognition',
      'result': 'accessGranted',
      'time': '2026-03-01 01:15',
    },
    {
      'doorKey': 'mainDoor',
      'userKey': null,
      'method': 'aiRecognition',
      'result': 'accessDenied',
      'time': '2026-03-01 00:45',
    },
    {
      'doorKey': 'garageDoor',
      'userKey': 'greeting',
      'method': 'manualApp',
      'result': 'accessGranted',
      'time': '2026-02-28 22:10',
    },
    {
      'doorKey': 'backDoor',
      'userKey': 'greeting',
      'method': 'aiRecognition',
      'result': 'accessGranted',
      'time': '2026-02-28 18:30',
    },
  ];

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _listController.forward();
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
    final now = DateTime.now();
    return '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')} '
        '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}';
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
                          if (pinController.text != '1234') {
                            setDialogState(() {
                              pinError = l10n.pinError;
                            });
                            _addAccessLog(
                              doorKey: door['nameKey'],
                              granted: false,
                            );
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
                            await _api.openDoor(
                              source: 'flutter_app',
                              reason: 'manual_open_from_flutter',
                              openedBy: appState.userName,
                            );

                            if (!mounted) return;

                            appState.setDoorState(door['id'], false);
                            _addAccessLog(
                              doorKey: door['nameKey'],
                              granted: true,
                            );

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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.doors),
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
                                      door['isLocked']
                                          ? l10n.statusLocked
                                          : l10n.statusUnlocked,
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
                                      onPressed: () => appState.setDoorState(
                                        door['id'],
                                        true,
                                      ),
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
            _accessLog.isEmpty
                ? Center(child: Text(l10n.noAccessLogs))
                : ListView.separated(
                    padding: const EdgeInsets.all(24.0),
                    itemCount: _accessLog.length,
                    separatorBuilder: (context, index) =>
                        const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final log = _accessLog[index];
                      bool isGranted = log['result'] == 'accessGranted';
                      String door = _getDoorName(l10n, log['doorKey']);
                      String user = log['userKey'] != null
                          ? l10n.greeting
                          : l10n.unknownPerson;
                      String method = log['method'] == 'aiRecognition'
                          ? l10n.aiRecognition
                          : l10n.manualApp;
                      String result = isGranted
                          ? l10n.accessGranted
                          : l10n.accessDenied;

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
                                color: isGranted
                                    ? Colors.green.withOpacity(0.1)
                                    : Colors.red.withOpacity(0.1),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                isGranted
                                    ? LucideIcons.shieldCheck
                                    : LucideIcons.shieldAlert,
                                color: isGranted ? Colors.green : Colors.red,
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
                                    style: Theme.of(
                                      context,
                                    ).textTheme.titleMedium,
                                  ),
                                  const SizedBox(height: 4),
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 3,
                                        ),
                                        decoration: BoxDecoration(
                                          color: isGranted
                                              ? Colors.green.withOpacity(0.1)
                                              : Colors.red.withOpacity(0.1),
                                          borderRadius: BorderRadius.circular(
                                            8,
                                          ),
                                        ),
                                        child: Text(
                                          result,
                                          style: TextStyle(
                                            color: isGranted
                                                ? Colors.green
                                                : Colors.red,
                                            fontSize: 11,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        method,
                                        style: Theme.of(
                                          context,
                                        ).textTheme.bodySmall,
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    log['time'],
                                    style: Theme.of(
                                      context,
                                    ).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ],
        ),
      ),
    );
  }
}
