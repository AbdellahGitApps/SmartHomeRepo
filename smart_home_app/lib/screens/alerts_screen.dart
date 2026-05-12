import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import 'package:lucide_icons/lucide_icons.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _listController;

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
        'titleKey': 'alertTypeHighEnergy',
        'timeKey': 'justNow',
        'type': 'highEnergy',
        'icon': LucideIcons.zap,
        'color': Colors.orange,
        'isResolved': false,
        'comparison': '+18%',
      },
      {
        'titleKey': 'alertTypeUnknownFace',
        'timeKey': 'minsAgo',
        'type': 'unknownFace',
        'icon': LucideIcons.userX,
        'color': Colors.red,
        'isResolved': false,
        'comparison': null,
      },
      {
        'titleKey': 'alertTypeHighEnergy',
        'timeKey': 'hoursAgo',
        'type': 'highEnergy',
        'icon': LucideIcons.zap,
        'color': Colors.orange,
        'isResolved': true,
        'comparison': '+12%',
      },
      {
        'titleKey': 'systemUpdateCompleted',
        'timeKey': 'hoursAgo',
        'type': 'system',
        'icon': LucideIcons.checkCircle,
        'color': Colors.green,
        'isResolved': true,
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
      case 'systemUpdateCompleted':
        return l10n.systemUpdateCompleted;
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    bool isDark = Theme.of(context).brightness == Brightness.dark;

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
        child: mockAlerts.isEmpty
            ? Center(child: Text(l10n.noAlerts))
            : ListView.separated(
                padding: const EdgeInsets.all(24.0),
                itemCount: mockAlerts.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (context, index) {
                  final alert = mockAlerts[index];
                  bool isResolved = alert['isResolved'] as bool;

                  final itemAnimation = Tween<double>(begin: 0, end: 1).animate(
                    CurvedAnimation(
                      parent: _listController,
                      curve: Interval(
                        (index / mockAlerts.length).clamp(0.0, 1.0),
                        ((index + 1) / mockAlerts.length).clamp(0.0, 1.0),
                        curve: Curves.easeOutCubic,
                      ),
                    ),
                  );

                  return AnimatedBuilder(
                    animation: itemAnimation,
                    builder: (context, child) {
                      return Transform.translate(
                        offset: Offset(50 * (1 - itemAnimation.value), 0),
                        child: Opacity(
                          opacity: itemAnimation.value,
                          child: child,
                        ),
                      );
                    },
                    child: AnimatedOpacity(
                      duration: const Duration(milliseconds: 400),
                      opacity: isResolved ? 0.6 : 1.0,
                      child: Container(
                        padding: const EdgeInsets.all(20),
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
                              : isResolved
                              ? null
                              : Border.all(
                                  color: (alert['color'] as Color).withOpacity(
                                    0.3,
                                  ),
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
                          children: [
                            Row(
                              children: [
                                TweenAnimationBuilder<double>(
                                  tween: Tween(begin: 0.0, end: 1.0),
                                  duration: Duration(
                                    milliseconds: 600 + (index * 200),
                                  ),
                                  curve: Curves.elasticOut,
                                  builder: (context, value, child) {
                                    return Transform.scale(
                                      scale: value,
                                      child: child,
                                    );
                                  },
                                  child: Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: (alert['color'] as Color)
                                          .withOpacity(0.1),
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      alert['icon'],
                                      color: alert['color'],
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        _getAlertTitle(l10n, alert['titleKey']),
                                        style: Theme.of(
                                          context,
                                        ).textTheme.titleLarge,
                                      ),
                                      const SizedBox(height: 4),
                                      Wrap(
                                        spacing: 8,
                                        runSpacing: 4,
                                        children: [
                                          Text(
                                            _getAlertTime(
                                              l10n,
                                              alert['timeKey'],
                                            ),
                                            style: Theme.of(
                                              context,
                                            ).textTheme.bodyMedium,
                                          ),
                                          // Status badge
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 8,
                                              vertical: 3,
                                            ),
                                            decoration: BoxDecoration(
                                              color: isResolved
                                                  ? Colors.green.withOpacity(
                                                      0.1,
                                                    )
                                                  : Colors.red.withOpacity(0.1),
                                              borderRadius:
                                                  BorderRadius.circular(8),
                                            ),
                                            child: Text(
                                              isResolved
                                                  ? l10n.resolved
                                                  : l10n.activeAlert,
                                              style: TextStyle(
                                                color: isResolved
                                                    ? Colors.green
                                                    : Colors.red,
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
                            // Comparison for high energy alerts
                            if (alert['comparison'] != null)
                              Padding(
                                padding: const EdgeInsets.only(top: 12),
                                child: Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 14,
                                    vertical: 10,
                                  ),
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
                              ),
                            // Resolve button
                            if (!isResolved)
                              Padding(
                                padding: const EdgeInsets.only(top: 12),
                                child: SizedBox(
                                  width: double.infinity,
                                  child: OutlinedButton.icon(
                                    onPressed: () {
                                      setState(() {
                                        alert['isResolved'] = true;
                                      });
                                    },
                                    icon: const Icon(
                                      LucideIcons.checkCircle,
                                      size: 18,
                                    ),
                                    label: Text(l10n.resolve),
                                    style: OutlinedButton.styleFrom(
                                      foregroundColor: Colors.green,
                                      side: BorderSide(
                                        color: Colors.green.withOpacity(0.3),
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(14),
                                      ),
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 10,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
      ),
    );
  }
}
