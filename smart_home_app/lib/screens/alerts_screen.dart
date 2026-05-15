import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../widgets/add_member_bottom_sheet.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _listController;

  // Filter: 0 = All, 1 = Security, 2 = System
  int _filterIndex = 0;

  // Mock Alerts with types and resolve status
  late List<Map<String, dynamic>> mockAlerts;

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _listController.forward();

    mockAlerts = [
      {
        'titleKey': 'unknownFaceDetected',
        'timeKey': 'justNow',
        'type': 'unknownFace',
        'category': 'security',
        'icon': LucideIcons.userX,
        'color': Colors.red,
        'isResolved': false,
        'cameraKey': 'frontDoor',
        'statusKey': 'pendingDecision',
        'comparison': null,
      },
      {
        'titleKey': 'alertTypeHighEnergy',
        'timeKey': 'minsAgo',
        'type': 'highEnergy',
        'category': 'system',
        'icon': LucideIcons.zap,
        'color': Colors.orange,
        'isResolved': false,
        'camera': null,
        'status': null,
        'comparison': '+18%',
      },
      {
        'titleKey': 'deviceOffline',
        'timeKey': 'minsAgo',
        'type': 'deviceOffline',
        'category': 'system',
        'icon': LucideIcons.wifiOff,
        'color': const Color(0xFFEF4444),
        'isResolved': false,
        'camera': null,
        'status': null,
        'comparison': null,
        'deviceNameKey': 'livingRoomSensor',
      },
      {
        'titleKey': 'alertTypeHighEnergy',
        'timeKey': 'hoursAgo',
        'type': 'highEnergy',
        'category': 'system',
        'icon': LucideIcons.zap,
        'color': Colors.orange,
        'isResolved': true,
        'camera': null,
        'status': null,
        'comparison': '+12%',
      },
      {
        'titleKey': 'systemUpdateCompleted',
        'timeKey': 'hoursAgo',
        'type': 'system',
        'category': 'system',
        'icon': LucideIcons.checkCircle,
        'color': Colors.green,
        'isResolved': true,
        'camera': null,
        'status': null,
        'comparison': null,
      },
    ];
  }

  @override
  void dispose() {
    _listController.dispose();
    super.dispose();
  }

  String _getAlertTitle(AppLocalizations l10n, String key) {
    switch (key) {
      case 'alertTypeHighEnergy':
        return l10n.alertTypeHighEnergy;
      case 'alertTypeUnknownFace':
        return l10n.alertTypeUnknownFace;
      case 'unknownFaceDetected':
        return l10n.unknownFaceDetected;
      case 'systemUpdateCompleted':
        return l10n.systemUpdateCompleted;
      case 'deviceOffline':
        return l10n.deviceOffline;
      default:
        return key;
    }
  }

  String _getAlertTime(AppLocalizations l10n, String key) {
    switch (key) {
      case 'justNow':
        return l10n.justNow;
      case 'minsAgo':
        return l10n.minsAgo;
      case 'hoursAgo':
        return l10n.hoursAgo;
      default:
        return key;
    }
  }

  List<Map<String, dynamic>> get _filteredAlerts {
    if (_filterIndex == 0) return mockAlerts;
    if (_filterIndex == 1) {
      return mockAlerts.where((a) => a['category'] == 'security').toList();
    }
    return mockAlerts.where((a) => a['category'] == 'system').toList();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    bool isDark = Theme.of(context).brightness == Brightness.dark;
    final filtered = _filteredAlerts;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.alerts),
        actions: [
          TextButton(
            onPressed: () {
              setState(() {
                for (var alert in mockAlerts) {
                  alert['isResolved'] = true;
                }
              });
            },
            child: Text(
              l10n.clear,
              style: TextStyle(color: Theme.of(context).primaryColor),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // ── Filter tabs ──
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 16),
              child: Container(
                decoration: BoxDecoration(
                  color: isDark
                      ? const Color(0xFF0F172A)
                      : const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(14),
                ),
                padding: const EdgeInsets.all(4),
                child: Row(
                  children: [
                    _buildFilterTab(l10n.allAlerts, 0, isDark),
                    _buildFilterTab(l10n.securityAlerts, 1, isDark),
                    _buildFilterTab(l10n.systemAlerts, 2, isDark),
                  ],
                ),
              ),
            ),

            // ── Alert list ──
            Expanded(
              child: filtered.isEmpty
                  ? Center(child: Text(l10n.noAlerts))
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 16),
                      itemBuilder: (context, index) {
                        final alert = filtered[index];
                        bool isResolved = alert['isResolved'] as bool;

                        final itemAnimation =
                            Tween<double>(begin: 0, end: 1).animate(
                          CurvedAnimation(
                            parent: _listController,
                            curve: Interval(
                              (index / filtered.length).clamp(0.0, 1.0),
                              ((index + 1) / filtered.length).clamp(0.0, 1.0),
                              curve: Curves.easeOutCubic,
                            ),
                          ),
                        );

                        return AnimatedBuilder(
                          animation: itemAnimation,
                          builder: (context, child) {
                            return Transform.translate(
                              offset:
                                  Offset(50 * (1 - itemAnimation.value), 0),
                              child: Opacity(
                                opacity: itemAnimation.value,
                                child: child,
                              ),
                            );
                          },
                          child: _buildAlertCard(
                              alert, isResolved, isDark, l10n, index),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // ── Filter tab button ──
  Widget _buildFilterTab(String label, int index, bool isDark) {
    bool isSelected = _filterIndex == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _filterIndex = index),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeInOut,
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: isSelected
                ? Theme.of(context).primaryColor
                : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: isSelected
                  ? Colors.white
                  : (isDark
                      ? const Color(0xFF94A3B8)
                      : const Color(0xFF757575)),
            ),
          ),
        ),
      ),
    );
  }

  // ── Alert card builder ──
  Widget _buildAlertCard(
    Map<String, dynamic> alert,
    bool isResolved,
    bool isDark,
    AppLocalizations l10n,
    int index,
  ) {
    final alertColor = alert['color'] as Color;

    return AnimatedOpacity(
      duration: const Duration(milliseconds: 400),
      opacity: isResolved ? 0.55 : 1.0,
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isDark
              ? Theme.of(context).colorScheme.surface
              : Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(22),
          border: isDark
              ? Border.all(color: const Color(0xFF334155), width: 1)
              : isResolved
                  ? null
                  : Border.all(
                      color: alertColor.withOpacity(0.25),
                      width: 1,
                    ),
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
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header row ──
            Row(
              children: [
                // Animated icon
                TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0.0, end: 1.0),
                  duration: Duration(milliseconds: 600 + (index * 150)),
                  curve: Curves.elasticOut,
                  builder: (context, value, child) {
                    return Transform.scale(scale: value, child: child);
                  },
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: alertColor.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      alert['icon'],
                      color: alertColor,
                      size: 22,
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                // Title + time + badge
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getAlertTitle(l10n, alert['titleKey']),
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontSize: 16,
                            ),
                      ),
                      const SizedBox(height: 4),
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        children: [
                          Text(
                            _getAlertTime(l10n, alert['timeKey']),
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: isResolved
                                  ? Colors.green.withOpacity(0.1)
                                  : Colors.red.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              isResolved ? l10n.resolved : l10n.activeAlert,
                              style: TextStyle(
                                color:
                                    isResolved ? Colors.green : Colors.red,
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),

            // ── Unknown Face details ──
            if (alert['type'] == 'unknownFace') ...[
              const SizedBox(height: 14),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: isDark
                      ? const Color(0xFF0F172A)
                      : const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: isDark
                        ? const Color(0xFF334155)
                        : const Color(0xFFE2E8F0),
                  ),
                ),
                child: Column(
                  children: [
                    _buildDetailRow(
                      LucideIcons.clock,
                      l10n.detectionTime,
                      '2026-05-16  00:47',
                      isDark,
                    ),
                    const SizedBox(height: 8),
                    _buildDetailRow(
                      LucideIcons.video,
                      l10n.cameraLabel,
                      alert['cameraKey'] == 'frontDoor' ? l10n.frontDoor : (alert['camera'] ?? l10n.frontDoor),
                      isDark,
                    ),
                    const SizedBox(height: 8),
                    _buildDetailRow(
                      LucideIcons.alertTriangle,
                      l10n.statusLabel,
                      l10n.pendingDecision,
                      isDark,
                      valueColor: Colors.orange,
                    ),
                  ],
                ),
              ),
              // Action buttons
              if (!isResolved) ...[
                const SizedBox(height: 14),
                Row(
                  children: [
                    _buildActionButton(
                      label: l10n.openAction,
                      icon: LucideIcons.eye,
                      color: const Color(0xFF3B82F6),
                      isDark: isDark,
                      onTap: () {},
                    ),
                    const SizedBox(width: 8),
                    _buildActionButton(
                      label: l10n.denyAction,
                      icon: LucideIcons.xCircle,
                      color: Colors.red,
                      isDark: isDark,
                      onTap: () {
                        setState(() => alert['isResolved'] = true);
                      },
                    ),
                    const SizedBox(width: 8),
                    _buildActionButton(
                      label: l10n.addToFamily,
                      icon: LucideIcons.userPlus,
                      color: Colors.green,
                      isDark: isDark,
                      onTap: () {
                        AddMemberBottomSheet.show(
                          context,
                          l10n: l10n,
                          appState: Provider.of<AppStateProvider>(context, listen: false),
                          isDark: isDark,
                          onAdded: () {
                            setState(() => alert['isResolved'] = true);
                          },
                        );
                      },
                    ),
                  ],
                ),
              ],
            ],

            // ── Device Offline details ──
            if (alert['type'] == 'deviceOffline' && !isResolved) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(LucideIcons.router, size: 16, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        alert['deviceNameKey'] == 'livingRoomSensor' ? l10n.livingRoomSensor : (alert['deviceName'] ?? 'Unknown Device'),
                        style: const TextStyle(
                          fontSize: 13,
                          color: Colors.red,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // ── High energy comparison ──
            if (alert['comparison'] != null) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: Colors.orange.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.trendingUp,
                      size: 16,
                      color: Colors.orange,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${alert['comparison']} ${l10n.higherThanAverage} — ${l10n.comparedToPrevious}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Colors.orange,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // ── Resolve button (for non-unknownFace alerts) ──
            if (!isResolved && alert['type'] != 'unknownFace') ...[
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () {
                    setState(() => alert['isResolved'] = true);
                  },
                  icon: const Icon(LucideIcons.checkCircle, size: 18),
                  label: Text(l10n.resolve),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.green,
                    side: BorderSide(
                      color: Colors.green.withOpacity(0.3),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // ── Detail row for unknown face card ──
  Widget _buildDetailRow(
    IconData icon,
    String label,
    String value,
    bool isDark, {
    Color? valueColor,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 15,
          color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF757575),
        ),
        const SizedBox(width: 8),
        Text(
          '$label: ',
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: isDark ? const Color(0xFF94A3B8) : const Color(0xFF757575),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: valueColor ??
                  (isDark ? const Color(0xFFF8FAFC) : const Color(0xFF1A1A1A)),
            ),
          ),
        ),
      ],
    );
  }

  // ── Compact action button ──
  Widget _buildActionButton({
    required String label,
    required IconData icon,
    required Color color,
    required bool isDark,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 10),
          decoration: BoxDecoration(
            color: color.withOpacity(isDark ? 0.15 : 0.08),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: color.withOpacity(0.2)),
          ),
          child: Column(
            children: [
              Icon(icon, size: 18, color: color),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
