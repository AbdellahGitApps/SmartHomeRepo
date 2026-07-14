import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'dart:io'; // For SocketException

import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';
import 'package:smart_home_app/l10n/app_localizations.dart';
import 'package:smart_home_app/providers/app_state_provider.dart';
import 'package:smart_home_app/services/backend_api_service.dart';
import '../utils/date_formatter.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen>
    with SingleTickerProviderStateMixin {
  final BackendApiService _api = BackendApiService();

  late final TabController _tabController;
  final _cameraPinController = TextEditingController();

  bool _cameraPinUnlocked = false;
  bool _obscureCameraPinGate = true;
  String? _cameraPinGateError;

  Timer? _fakePreviewTimer;
  int _previewTick = 0;

  bool _loadingCameras = false;
  bool _loadingFaceEvents = false;
  String? _cameraError;
  String? _faceEventsError;

  List<Map<String, dynamic>> _cameras = [];
  List<Map<String, dynamic>> _faceEvents = [];

  @override
  void initState() {
    super.initState();

    _tabController = TabController(length: 2, vsync: this);

    _fakePreviewTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted) return;
      setState(() {
        _previewTick++;
      });
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadCameraPage();
    });
  }

  @override
  void dispose() {
    _fakePreviewTimer?.cancel();
    _cameraPinController.dispose();
    _tabController.dispose();
    _api.close();
    super.dispose();
  }

  Future<void> _loadCameraPage() async {
    await Future.wait([_loadCameras(), _loadFaceEvents()]);
  }

  Future<void> _loadCameras() async {
    if (!mounted) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    setState(() {
      _loadingCameras = true;
      _cameraError = null;
    });

    try {
      final response = await _api.getAppCameras(
        homeId: appState.homeDbId.isNotEmpty
            ? appState.homeDbId
            : appState.homeId,
        homeCode: appState.homeCode,
        apartmentNumber: appState.apartmentNumber,
        adminLogin: appState.adminName,
      );

      final raw = response['cameras'];

      final items = raw is List
          ? raw
                .whereType<Map>()
                .map((e) => Map<String, dynamic>.from(e))
                .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        _cameras = items;
      });
    } catch (e) {
      if (!mounted) return;

      debugPrint('Camera load error: $e'); // Detailed log for debugging
      final friendly = _friendlyErrorMessage(e);
      setState(() {
        _cameraError = friendly;
      });
    } finally {
      if (!mounted) return;

      setState(() {
        _loadingCameras = false;
      });
    }
  }

  Future<void> _loadFaceEvents() async {
    if (!mounted) return;

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    setState(() {
      _loadingFaceEvents = true;
      _faceEventsError = null;
    });

    try {
      final response = await _api.getAppCameraFaceEvents(
        homeId: appState.homeDbId.isNotEmpty
            ? appState.homeDbId
            : appState.homeId,
        homeCode: appState.homeCode,
        apartmentNumber: appState.apartmentNumber,
        adminLogin: appState.adminName,
        limit: 80,
      );

      final raw = response['events'];

      final items = raw is List
          ? raw
                .whereType<Map>()
                .map((e) => Map<String, dynamic>.from(e))
                .toList()
          : <Map<String, dynamic>>[];

      if (!mounted) return;

      setState(() {
        _faceEvents = items;
      });
    } catch (e) {
      if (!mounted) return;

      debugPrint('Face events load error: $e'); // Detailed log for debugging
      final friendly = _friendlyErrorMessage(e);
      setState(() {
        _faceEventsError = friendly;
      });
    } finally {
      if (!mounted) return;

      setState(() {
        _loadingFaceEvents = false;
      });
    }
  }

  bool _readBool(
    Map<String, dynamic> data,
    List<String> keys, {
    bool fallback = false,
  }) {
    for (final key in keys) {
      final value = data[key];

      if (value is bool) return value;
      if (value is num) return value != 0;

      final text = value?.toString().toLowerCase().trim();

      if (text == 'true' || text == '1' || text == 'yes' || text == 'online') {
        return true;
      }

      if (text == 'false' ||
          text == '0' ||
          text == 'no' ||
          text == 'offline' ||
          text == 'disabled') {
        return false;
      }
    }

    return fallback;
  }

  String _text(dynamic value, {String fallback = ''}) {
    final raw = value?.toString().trim() ?? '';
    return raw.isEmpty ? fallback : raw;
  }

  String _formatTime(dynamic value) {
    return DateFormatter.formatFamilyDate(_text(value));
  }

  String _imageUrl(String rawUrl, bool isFake) {
    if (rawUrl.isEmpty) return '';

    String url = rawUrl;

    if (url.startsWith('/')) {
      url = '${_api.baseUrl}$url';
    }

    if (!isFake) return url;

    final separator = url.contains('?') ? '&' : '?';
    return '$url${separator}t=$_previewTick';
  }

  BoxDecoration _cardDecoration(BuildContext context, bool isDark) {
    return BoxDecoration(
      color: isDark ? Theme.of(context).colorScheme.surface : Colors.white,
      borderRadius: BorderRadius.circular(24),
      border: isDark ? Border.all(color: const Color(0xFF334155)) : null,
      boxShadow: isDark
          ? []
          : [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
    );
  }

  Color _eventColor(String severity, String status) {
    final s = '${severity.toLowerCase()} ${status.toLowerCase()}';

    if (s.contains('denied') || s.contains('critical')) return Colors.red;
    if (s.contains('pending') || s.contains('warning')) return Colors.orange;

    return Colors.green;
  }

  IconData _eventIcon(String title, bool known) {
    final lower = title.toLowerCase();

    if (lower.contains('unknown')) return LucideIcons.userX;
    if (known || lower.contains('family')) return LucideIcons.userCheck;

    return LucideIcons.scanFace;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      appBar: AppBar(
        title: Text(l10n.cameraEvents),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(LucideIcons.refreshCw),
            onPressed: _loadCameraPage,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
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
        controller: _tabController,
        children: [_buildCamerasTab(context), _buildFaceEventsTab(context)],
      ),
    );
  }

  Widget _buildCamerasTab(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final appState = Provider.of<AppStateProvider>(context);

    if (appState.isUser && !_cameraPinUnlocked) {
      return _buildCameraPinGate(context, appState, isDark);
    }

    if (_loadingCameras) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_cameraError != null) {
      return _errorBox(_cameraError ?? '');
    }

    if (_cameras.isEmpty) {
      return const Center(
        child: Text('No cameras registered for this apartment.'),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadCameras,
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        itemCount: _cameras.length,
        separatorBuilder: (_, __) => const SizedBox(height: 18),
        itemBuilder: (context, index) {
          final camera = _cameras[index];

          final name = _text(
            camera['name'] ?? camera['device_name'],
            fallback: 'Smart Door Camera',
          );

          final online = _readBool(camera, ['online'], fallback: false);
          final enabled = _readBool(camera, ['enabled'], fallback: true);
          final live = _readBool(camera, ['live'], fallback: online && enabled);
          final isFake = _readBool(camera, ['is_fake_stream'], fallback: false);
          final streamUrl = _text(camera['stream_url']);
          final imageUrl = _imageUrl(streamUrl, isFake);
          final lastSeen = _formatTime(camera['last_seen']);
          final apartment = _text(camera['apartment_number'], fallback: '--');

          final previewHeight = (MediaQuery.of(context).size.height * 0.48)
              .clamp(340.0, 560.0)
              .toDouble();

          return Container(
            padding: const EdgeInsets.all(20),
            decoration: _cardDecoration(context, isDark),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: live
                            ? Colors.green.withOpacity(0.12)
                            : Colors.red.withOpacity(0.10),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        LucideIcons.camera,
                        color: live ? Colors.green : Colors.red,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: Theme.of(context).textTheme.titleMedium
                                ?.copyWith(fontWeight: FontWeight.w700),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            online ? 'Online' : 'Offline',
                            style: TextStyle(
                              color: online ? Colors.green : Colors.red,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: live
                            ? Colors.green.withOpacity(0.12)
                            : Colors.red.withOpacity(0.10),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        live ? 'Live' : 'Offline',
                        style: TextStyle(
                          color: live ? Colors.green : Colors.red,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  height: previewHeight,
                  decoration: BoxDecoration(
                    color: isDark
                        ? const Color(0xFF0F172A)
                        : const Color(0xFFF1F5F9),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                      color: isDark
                          ? const Color(0xFF334155)
                          : const Color(0xFFE5E7EB),
                    ),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: live && imageUrl.isNotEmpty
                      ? Stack(
                          fit: StackFit.expand,
                          children: [
                            Image.network(
                              imageUrl,
                              fit: BoxFit.cover,
                              gaplessPlayback: true,
                              errorBuilder: (_, __, ___) {
                                return _streamFallback(
                                  isDark,
                                  'Stream Not Available',
                                );
                              },
                            ),
                            if (isFake)
                              Positioned(
                                left: 16,
                                top: 16,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 12,
                                    vertical: 6,
                                  ),
                                  decoration: BoxDecoration(
                                    color: Colors.black.withOpacity(0.45),
                                    borderRadius: BorderRadius.circular(18),
                                  ),
                                  child: const Text(
                                    'Fake Preview',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        )
                      : _streamFallback(isDark, 'Stream Not Available'),
                ),
                const SizedBox(height: 14),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    _infoChip(
                      icon: LucideIcons.home,
                      label: 'Apartment $apartment',
                      color: Colors.blue,
                    ),
                    _infoChip(
                      icon: LucideIcons.clock,
                      label: 'Last seen: $lastSeen',
                      color: Colors.orange,
                    ),
                    _infoChip(
                      icon: enabled
                          ? LucideIcons.checkCircle
                          : LucideIcons.xCircle,
                      label: enabled ? 'Enabled' : 'Disabled',
                      color: enabled ? Colors.green : Colors.red,
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _unlockCameraWithPin(AppStateProvider appState) {
    final expectedPin = appState.cameraPin.trim();
    final enteredPin = _cameraPinController.text.trim();

    if (expectedPin.isEmpty) {
      setState(() {
        _cameraPinGateError = 'Camera PIN is not set by Admin yet.';
      });
      return;
    }

    if (enteredPin != expectedPin) {
      setState(() {
        _cameraPinGateError = 'Invalid Camera PIN.';
      });
      return;
    }

    setState(() {
      _cameraPinUnlocked = true;
      _cameraPinGateError = null;
      _cameraPinController.clear();
    });
  }

  Widget _buildCameraPinGate(
    BuildContext context,
    AppStateProvider appState,
    bool isDark,
  ) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 460),
          padding: const EdgeInsets.all(24),
          decoration: _cardDecoration(context, isDark),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 72,
                height: 72,
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  LucideIcons.lock,
                  color: Theme.of(context).primaryColor,
                  size: 34,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Camera Locked',
                style: Theme.of(
                  context,
                ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              Text(
                'Enter the Camera PIN to view the live camera stream.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: isDark ? Colors.white70 : Colors.black54,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 20),
              TextField(
                controller: _cameraPinController,
                obscureText: _obscureCameraPinGate,
                keyboardType: TextInputType.number,
                onSubmitted: (_) => _unlockCameraWithPin(appState),
                decoration: InputDecoration(
                  labelText: 'Camera PIN',
                  prefixIcon: const Icon(LucideIcons.keyRound),
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureCameraPinGate
                          ? LucideIcons.eyeOff
                          : LucideIcons.eye,
                    ),
                    onPressed: () => setState(
                      () => _obscureCameraPinGate = !_obscureCameraPinGate,
                    ),
                  ),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  filled: true,
                  fillColor: isDark
                      ? const Color(0xFF0F172A)
                      : Colors.grey.shade50,
                ),
              ),
              if (_cameraPinGateError != null) ...[
                const SizedBox(height: 12),
                Text(
                  _cameraPinGateError!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.red,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.lock_open),
                  label: const Text('Unlock Camera'),
                  onPressed: () => _unlockCameraWithPin(appState),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _streamFallback(bool isDark, String text) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          LucideIcons.videoOff,
          size: 42,
          color: isDark ? Colors.white54 : Colors.black38,
        ),
        const SizedBox(height: 10),
        Text(
          text,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: isDark ? Colors.white54 : Colors.black54,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  Widget _buildFaceEventsTab(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    if (_loadingFaceEvents) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_faceEventsError != null) {
      return _errorBox(_faceEventsError ?? '');
    }

    if (_faceEvents.isEmpty) {
      return const Center(child: Text('No face events from backend yet.'));
    }

    return RefreshIndicator(
      onRefresh: _loadFaceEvents,
      child: ListView.separated(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        itemCount: _faceEvents.length,
        separatorBuilder: (_, __) => const SizedBox(height: 14),
        itemBuilder: (context, index) {
          final event = _faceEvents[index];

          String title = _text(event['title'], fallback: 'Face Event');
          final status = _text(event['status'], fallback: 'Event');
          final severity = _text(event['severity'], fallback: 'info');
          final camera = _text(event['camera'], fallback: 'Smart Door');
          String details = _text(event['details']);
          final memberName = _text(event['member_name']);
          final known = _readBool(event, ['known'], fallback: false);
          
          String? snapshotPath;

          try {
            final parsed = jsonDecode(details);
            if (parsed is Map) {
              final reason = parsed['reason']?.toString() ?? '';
              final cmd = parsed['command']?.toString() ?? '';
              snapshotPath = parsed['snapshot_file']?.toString() ?? parsed['snapshot_path']?.toString();

              if (reason == 'unknown_face') {
                title = 'Unknown Person Detected';
                details = 'An unrecognized person was detected near your entrance.';
              } else if (reason == 'recognized_face' || reason == 'known_face') {
                title = 'Family Member Detected';
                details = memberName.isNotEmpty 
                    ? '$memberName was recognized successfully.' 
                    : 'A family member was recognized successfully.';
              } else if (reason == 'door_unlocked' || cmd == 'open' || reason.contains('manual_open')) {
                title = 'Door Unlocked';
                details = 'Your smart door was unlocked successfully.';
              } else if (reason == 'door_locked' || cmd == 'lock' || reason.contains('manual_lock')) {
                title = 'Door Locked';
                details = 'Your smart door has been locked.';
              } else if (reason == 'access_denied') {
                title = 'Access Denied';
                details = 'An unauthorized access attempt was blocked.';
              } else {
                details = 'System event logged.';
              }
            }
          } catch (_) {
            final lower = details.toLowerCase();
            final lowerTitle = title.toLowerCase();
            
            if (lower.contains('reason: unknown_face') || lowerTitle.contains('unknown')) {
              title = 'Unknown Person Detected';
              details = 'An unrecognized person was detected near your entrance.';
            } else if (lower.contains('reason: recognized_face') || lower.contains('reason: known_face') || lowerTitle.contains('family')) {
              title = 'Family Member Detected';
              details = memberName.isNotEmpty 
                  ? '$memberName was recognized successfully.' 
                  : 'A family member was recognized successfully.';
            } else if (lower.contains('unlocked') || lower.contains('manual_open')) {
              title = 'Door Unlocked';
              details = 'Your smart door was unlocked successfully.';
            } else if (lower.contains('locked') || lower.contains('manual_lock')) {
              title = 'Door Locked';
              details = 'Your smart door has been locked.';
            } else if (lower.contains('denied') || lower.contains('unauthorized')) {
              title = 'Access Denied';
              details = 'An unauthorized access attempt was blocked.';
            }

            final snapMatch = RegExp(r"snapshot_file[^\w]+([\w/.-]+)").firstMatch(details);
            if (snapMatch != null) {
              snapshotPath = snapMatch.group(1);
            } else {
              // Hide raw JSON if it starts with {
              if (details.trim().startsWith('{')) {
                details = 'System event logged.';
              }
            }
          }

          final color = _eventColor(severity, status);

          return Container(
            padding: const EdgeInsets.all(18),
            decoration: _cardDecoration(context, isDark),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(_eventIcon(title, known), color: color),
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
                              title,
                              style: Theme.of(context).textTheme.titleMedium
                                  ?.copyWith(fontWeight: FontWeight.w700),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              status,
                              style: TextStyle(
                                color: color,
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      if (memberName.isNotEmpty) ...[
                        Text(
                          'Name: $memberName',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 4),
                      ],
                      if (details.isNotEmpty) ...[
                        Text(
                          details,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 8),
                      ],
                      if (snapshotPath != null && snapshotPath.isNotEmpty) ...[
                        OutlinedButton.icon(
                          onPressed: () {
                            showDialog(
                              context: context,
                              builder: (ctx) => Dialog(
                                clipBehavior: Clip.antiAlias,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: Image.network(
                                  _imageUrl(snapshotPath!, false),
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
                        const SizedBox(height: 12),
                      ],
                      Row(
                        children: [
                          Icon(
                            LucideIcons.camera,
                            size: 14,
                            color: isDark ? Colors.white38 : Colors.black45,
                          ),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              camera,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            LucideIcons.clock,
                            size: 14,
                            color: isDark ? Colors.white38 : Colors.black45,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            _formatTime(event['timestamp']),
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
      ),
    );
  }

  Widget _infoChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  /// Returns a user-friendly error message for various exception types.
  String _friendlyErrorMessage(Object e) {
    const genericMessage = "Server is currently unavailable. Please make sure the Smart Home server is running and try again.";
    if (e is BackendApiException) {
      // For HTTP errors or backend messages, hide details.
      return genericMessage;
    }
    if (e is SocketException) {
      return genericMessage;
    }
    if (e is TimeoutException) {
      return genericMessage;
    }
    // Fallback for unexpected errors.
    return "An unexpected error occurred. Please try again later.";
  }

  Widget _errorBox(String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(
          message,
          textAlign: TextAlign.center,
          style: const TextStyle(color: Colors.red),
        ),
      ),
    );
  }
}
