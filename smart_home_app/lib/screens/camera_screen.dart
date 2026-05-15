import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _listController;

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _listController.forward();
  }

  @override
  void dispose() {
    _listController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.cameraEvents),
          bottom: TabBar(
            indicatorColor: Theme.of(context).primaryColor,
            labelColor: Theme.of(context).primaryColor,
            tabs: [
              Tab(
                text: l10n.camera,
                icon: const Icon(LucideIcons.camera, size: 18),
              ),
              Tab(
                text: l10n.faceEvents,
                icon: const Icon(LucideIcons.scanFace, size: 18),
              ),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildCamerasTab(context, l10n),
            _buildFaceEventsTab(context, l10n),
          ],
        ),
      ),
    );
  }

  Widget _buildCamerasTab(BuildContext context, AppLocalizations l10n) {
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    final List<Map<String, dynamic>> cameras = [
      {
        'name': l10n.frontDoorCamera,
        'status': l10n.motionDetected,
        'icon': LucideIcons.camera,
        'isLive': true,
        'color': Colors.red,
      },
      {
        'name': l10n.garageCamera,
        'status': l10n.noMotion,
        'icon': LucideIcons.camera,
        'isLive': false,
        'color': Colors.green,
      },
      {
        'name': l10n.backyardCamera,
        'status': l10n.personDetected,
        'icon': LucideIcons.camera,
        'isLive': true,
        'color': Colors.orange,
      },
    ];

    return ListView.separated(
      padding: const EdgeInsets.all(24.0),
      itemCount: cameras.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (context, index) {
        final cam = cameras[index];

        final itemAnimation = Tween<double>(begin: 0, end: 1).animate(
          CurvedAnimation(
            parent: _listController,
            curve: Interval(
              (index / cameras.length).clamp(0.0, 1.0),
              ((index + 1) / cameras.length).clamp(0.0, 1.0),
              curve: Curves.easeOutCubic,
            ),
          ),
        );

        return AnimatedBuilder(
          animation: itemAnimation,
          builder: (context, child) {
            return Transform.translate(
              offset: Offset(0, 40 * (1 - itemAnimation.value)),
              child: Opacity(opacity: itemAnimation.value, child: child),
            );
          },
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: isDark
                  ? Theme.of(context).colorScheme.surface
                  : Theme.of(context).cardColor,
              borderRadius: BorderRadius.circular(24),
              border: isDark
                  ? Border.all(color: const Color(0xFF334155), width: 1)
                  : null,
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
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
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
                              color: (cam['color'] as Color).withOpacity(0.1),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(cam['icon'], color: cam['color']),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              cam['name'],
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              cam['status'],
                              style: Theme.of(context).textTheme.bodyMedium!
                                  .copyWith(color: cam['color']),
                            ),
                          ],
                        ),
                      ],
                    ),
                    if (cam['isLive'] == true)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: Colors.red.withOpacity(0.3),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: BoxDecoration(
                                color: Colors.red,
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.red.withOpacity(0.5),
                                    blurRadius: 6,
                                    spreadRadius: 1,
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              l10n.live,
                              style: const TextStyle(
                                color: Colors.red,
                                fontWeight: FontWeight.w600,
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  height: 160,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0F172A) : Colors.grey[200],
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          LucideIcons.video,
                          size: 40,
                          color: isDark ? Colors.white24 : Colors.grey,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          cam['isLive'] == true 
                            ? (index == 0 ? appState.cameraUrl : l10n.live)
                            : l10n.recording,
                          style: Theme.of(context).textTheme.bodyMedium!
                              .copyWith(
                                color: isDark ? Colors.white30 : Colors.grey,
                                fontSize: index == 0 ? 10 : 12,
                              ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildFaceEventsTab(BuildContext context, AppLocalizations l10n) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    final faceEvents = [
      {
        'camera': l10n.frontDoorCamera,
        'type': 'registered',
        'name': l10n.greeting,
        'time': '2026-03-01 01:15',
        'icon': LucideIcons.userCheck,
        'color': Colors.green,
      },
      {
        'camera': l10n.frontDoorCamera,
        'type': 'unknown',
        'name': l10n.unknownPerson,
        'time': '2026-03-01 00:45',
        'icon': LucideIcons.userX,
        'color': Colors.red,
      },
      {
        'camera': l10n.backyardCamera,
        'type': 'registered',
        'name': l10n.greeting,
        'time': '2026-02-28 22:10',
        'icon': LucideIcons.userCheck,
        'color': Colors.green,
      },
      {
        'camera': l10n.garageCamera,
        'type': 'unknown',
        'name': l10n.unknownPerson,
        'time': '2026-02-28 20:30',
        'icon': LucideIcons.userX,
        'color': Colors.red,
      },
    ];

    return ListView.separated(
      padding: const EdgeInsets.all(24),
      itemCount: faceEvents.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final event = faceEvents[index];
        bool isUnknown = event['type'] == 'unknown';

        return Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: isDark
                ? Theme.of(context).colorScheme.surface
                : Theme.of(context).cardColor,
            borderRadius: BorderRadius.circular(20),
            border: isDark
                ? Border.all(color: const Color(0xFF334155), width: 1)
                : isUnknown
                ? Border.all(color: Colors.red.withOpacity(0.2), width: 1)
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
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: (event['color'] as Color).withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  event['icon'] as IconData,
                  color: event['color'] as Color,
                  size: 22,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            event['name'] as String,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                        ),
                        if (isUnknown)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.red.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(
                                  LucideIcons.alertTriangle,
                                  size: 12,
                                  color: Colors.red,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  l10n.unknownFaceDetected,
                                  style: const TextStyle(
                                    color: Colors.red,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          )
                        else
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.green.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              l10n.registeredFace,
                              style: const TextStyle(
                                color: Colors.green,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Icon(
                          LucideIcons.camera,
                          size: 13,
                          color: isDark ? Colors.white38 : Colors.grey,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          event['camera'] as String,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        const SizedBox(width: 12),
                        Icon(
                          LucideIcons.clock,
                          size: 13,
                          color: isDark ? Colors.white38 : Colors.grey,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          event['time'] as String,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
