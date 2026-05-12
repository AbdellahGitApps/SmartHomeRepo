import 'package:flutter/material.dart';

import '../services/app_settings_service.dart';

class LocalNetworkSettingsScreen extends StatefulWidget {
  const LocalNetworkSettingsScreen({super.key});

  @override
  State<LocalNetworkSettingsScreen> createState() =>
      _LocalNetworkSettingsScreenState();
}

class _LocalNetworkSettingsScreenState
    extends State<LocalNetworkSettingsScreen> {
  final AppSettingsService _settingsService = AppSettingsService();

  final TextEditingController _apiBaseUrlController = TextEditingController();
  final TextEditingController _esp32BaseUrlController = TextEditingController();
  final TextEditingController _cameraStreamUrlController =
      TextEditingController();

  bool _isLoading = false;
  String _message = '';

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  @override
  void dispose() {
    _apiBaseUrlController.dispose();
    _esp32BaseUrlController.dispose();
    _cameraStreamUrlController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      final apiBaseUrl = await _settingsService.getApiBaseUrl();
      final esp32BaseUrl = await _settingsService.getEsp32BaseUrl();
      final cameraStreamUrl = await _settingsService.getCameraStreamUrl();

      setState(() {
        _apiBaseUrlController.text = apiBaseUrl;
        _esp32BaseUrlController.text = esp32BaseUrl;
        _cameraStreamUrlController.text = cameraStreamUrl;
      });
    } catch (error) {
      setState(() {
        _message = 'Error loading settings:\n$error';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _saveSettings() async {
    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      await _settingsService.saveApiBaseUrl(_apiBaseUrlController.text);
      await _settingsService.saveEsp32BaseUrl(_esp32BaseUrlController.text);
      await _settingsService.saveCameraStreamUrl(
        _cameraStreamUrlController.text,
      );

      setState(() {
        _message = 'Settings saved successfully.';
      });
    } catch (error) {
      setState(() {
        _message = 'Error saving settings:\n$error';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _resetDefaults() async {
    setState(() {
      _isLoading = true;
      _message = '';
    });

    try {
      await _settingsService.resetToDefaults();
      await _loadSettings();

      setState(() {
        _message = 'Settings reset to defaults.';
      });
    } catch (error) {
      setState(() {
        _message = 'Error resetting settings:\n$error';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Widget _buildInfoCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Text(
          'Use these settings when devices are on the same local Wi-Fi network.\n\n'
          'FastAPI Server URL: laptop/server address.\n'
          'ESP32 Direct URL: ESP32 door device address.\n'
          'Camera Stream URL: ESP32-CAM stream address.\n\n'
          'Example:\n'
          'http://192.168.1.10:8000\n'
          'http://192.168.1.55\n'
          'http://192.168.1.55:81/stream',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required String hint,
    required TextEditingController controller,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          hintText: hint,
          border: const OutlineInputBorder(),
        ),
      ),
    );
  }

  Widget _buildMessage() {
    if (_message.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(_message),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Local Network Settings'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                children: [
                  _buildInfoCard(),
                  const SizedBox(height: 16),
                  _buildTextField(
                    label: 'FastAPI Server URL',
                    hint: AppSettingsService.defaultApiBaseUrl,
                    controller: _apiBaseUrlController,
                  ),
                  _buildTextField(
                    label: 'ESP32 Direct URL',
                    hint: AppSettingsService.defaultEsp32BaseUrl,
                    controller: _esp32BaseUrlController,
                  ),
                  _buildTextField(
                    label: 'Camera Stream URL',
                    hint: AppSettingsService.defaultCameraStreamUrl,
                    controller: _cameraStreamUrlController,
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _saveSettings,
                      child: const Text('Save Settings'),
                    ),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: _resetDefaults,
                      child: const Text('Reset Defaults'),
                    ),
                  ),
                  _buildMessage(),
                ],
              ),
      ),
    );
  }
}