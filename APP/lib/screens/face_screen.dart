import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/app_settings_service.dart';
import '../widgets/result_view.dart';

class FaceScreen extends StatefulWidget {
  const FaceScreen({super.key});

  @override
  State<FaceScreen> createState() => _FaceScreenState();
}

class _FaceScreenState extends State<FaceScreen> {
  final ApiService _apiService = ApiService();
  final AppSettingsService _settingsService = AppSettingsService();

  bool _isLoading = false;
  dynamic _resultData;

  List<double>? _selectedEmbedding;
  String _selectedEmbeddingLabel = 'No embedding selected';
  String _cameraStreamUrl = '';

  @override
  void initState() {
    super.initState();
    _loadCameraStreamUrl();
  }

  Future<void> _loadCameraStreamUrl() async {
    final url = await _settingsService.getCameraStreamUrl();

    if (!mounted) {
      return;
    }

    setState(() {
      _cameraStreamUrl = url;
    });
  }

  void _useMockKnownFace() {
    setState(() {
      _selectedEmbedding = [
        0.11,
        0.22,
        0.33,
        0.44,
        0.55,
        0.66,
        0.77,
        0.88,
      ];

      _selectedEmbeddingLabel = 'Mock Known Face';

      _resultData = {
        'selected_embedding': _selectedEmbeddingLabel,
        'note': 'Developer test embedding selected.',
      };
    });
  }

  void _useMockUnknownFace() {
    setState(() {
      _selectedEmbedding = [
        -0.11,
        -0.22,
        -0.33,
        -0.44,
        -0.55,
        -0.66,
        -0.77,
        -0.88,
      ];

      _selectedEmbeddingLabel = 'Mock Unknown Face';

      _resultData = {
        'selected_embedding': _selectedEmbeddingLabel,
        'note': 'Developer test embedding selected.',
      };
    });
  }

  Future<void> _verifySelectedFace() async {
    if (_selectedEmbedding == null) {
      setState(() {
        _resultData = {
          'success': false,
          'message': 'Please select a mock embedding first.',
        };
      });

      return;
    }

    setState(() {
      _isLoading = true;
      _resultData = {
        'message': 'Verifying selected face embedding...',
      };
    });

    try {
      final result = await _apiService.verifyFaceEmbedding(
        faceEmbedding: _selectedEmbedding!,
        source: 'flutter_face_engine',
        threshold: 0.75,
      );

      setState(() {
        _resultData = result;
      });
    } catch (error) {
      setState(() {
        _resultData = {
          'success': false,
          'error': error.toString(),
        };
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 8),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard({
    required String title,
    required String body,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(body),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required String label,
    required VoidCallback? onPressed,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _isLoading ? null : onPressed,
          child: Text(label),
        ),
      ),
    );
  }

  Widget _buildDeveloperTestSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Developer Test Embeddings',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'This section is for development only. Later, these mock buttons can be hidden or removed when real camera and face embedding extraction are connected.',
            ),
            const SizedBox(height: 12),
            Text('Selected: $_selectedEmbeddingLabel'),
            const SizedBox(height: 12),
            _buildActionButton(
              label: 'Use Mock Known Face',
              onPressed: _useMockKnownFace,
            ),
            _buildActionButton(
              label: 'Use Mock Unknown Face',
              onPressed: _useMockUnknownFace,
            ),
            _buildActionButton(
              label: 'Verify Selected Face',
              onPressed: _verifySelectedFace,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultSection() {
    if (_isLoading) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    return ResultView(data: _resultData);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSectionTitle('Privacy-Safe Face Flow'),
        _buildInfoCard(
          title: 'How the real flow should work',
          body: 'ESP32-CAM / Camera\n'
              '→ Flutter local face processing\n'
              '→ Send embedding only to FastAPI\n'
              '→ Known opens automatically\n'
              '→ Unknown waits for admin decision\n\n'
              'The backend should never receive or store face images.',
        ),
        _buildSectionTitle('Hardware Camera Integration'),
        _buildInfoCard(
          title: 'Camera Stream URL',
          body: _cameraStreamUrl.isEmpty
              ? 'No camera stream URL loaded.'
              : _cameraStreamUrl,
        ),
        _buildInfoCard(
          title: 'Future real camera features',
          body: 'Open ESP32-CAM stream\n'
              'Capture frame\n'
              'Extract real face embedding locally in Flutter\n'
              'Send embedding only to /face/verify\n\n'
              'These features are prepared conceptually but not implemented yet.',
        ),
        _buildSectionTitle('Developer Test'),
        _buildDeveloperTestSection(),
        _buildSectionTitle('Result'),
        _buildResultSection(),
      ],
    );
  }
}