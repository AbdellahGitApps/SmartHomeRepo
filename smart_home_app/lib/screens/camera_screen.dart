import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/backend_api_service.dart';
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
  final BackendApiService _api = BackendApiService();

  bool _isLoadingFaceEvents = true;
  String? _faceEventsError;
  List<Map<String, dynamic>> _faceEvents = [];

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _listController.forward();
    _loadFaceEvents();
  }

  @override
  void dispose() {
    _api.close();
    _listController.dispose();
    super.dispose();
  }

  Future<void> _loadFaceEvents() async {
    setState(() {
      _isLoadingFaceEvents = true;
      _faceEventsError = null;
    });

    try {
      final response = await _api.getFaceEvents(limit: 30);
      final events = response['events'];

      if (!mounted) return;

      setState(() {
        _faceEvents = events is List
            ? events
                  .whereType<Map>()
                  .map((item) => Map<String, dynamic>.from(item))
                  .toList()
            : [];
        _isLoadingFaceEvents = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _faceEventsError = error.toString();
        _isLoadingFaceEvents = false;
      });
    }
  }

  String _formatTime(dynamic value) {
    if (value == null) return 'No time';
    final raw = value.toString();

    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;

    return '${parsed.year}-${parsed.month.toString().padLeft(2, '0')}-${parsed.day.toString().padLeft(2, '0')} '
        '${parsed.hour.toString().padLeft(2, '0')}:${parsed.minute.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.cameraEvents),
          actions: [
            IconButton(
              onPressed: _loadFaceEvents,
              icon: const Icon(LucideIcons.refreshCcw),
            ),
          ],
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

    if (_isLoadingFaceEvents) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_faceEventsError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'Backend face events error: $_faceEventsError',
            style: const TextStyle(color: Colors.red),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (_faceEvents.isEmpty) {
      return RefreshIndicator(
        onRefresh: _loadFaceEvents,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: const [
            SizedBox(height: 120),
            Center(child: Text('No face events from backend yet')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadFaceEvents,
      child: ListView.separated(
        padding: const EdgeInsets.all(24),
        itemCount: _faceEvents.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final event = _faceEvents[index];
          final eventType = event['event_type']?.toString().toLowerCase() ?? '';
          final isKnown = eventType == 'known';
          final isUnknown = !isKnown;
          final name = event['name']?.toString();
          final displayName = name != null && name.isNotEmpty
              ? name
              : (isUnknown ? l10n.unknownPerson : l10n.greeting);

          final color = isKnown ? Colors.green : Colors.red;
          final icon = isKnown ? LucideIcons.userCheck : LucideIcons.userX;
          final source = event['source']?.toString() ?? l10n.frontDoorCamera;
          final score = event['score'];

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
                    color: color.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: color, size: 22),
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
                              displayName,
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
                          Expanded(
                            child: Text(
                              source,
                              style: Theme.of(context).textTheme.bodySmall,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            LucideIcons.clock,
                            size: 13,
                            color: isDark ? Colors.white38 : Colors.grey,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _formatTime(event['timestamp']),
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                      if (score != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Score: $score',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
