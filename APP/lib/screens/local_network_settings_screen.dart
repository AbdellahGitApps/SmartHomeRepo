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
  final AppSettingsService _appSettingsService = AppSettingsService();
  final TextEditingController _apiBaseUrlController = TextEditingController();
  final TextEditingController _esp32BaseUrlController = TextEditingController();

  bool _isLoading = true;
  String? _message;
  bool _isError = false;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() {
      _isLoading = true;
      _message = null;
    });

    try {
      final apiBaseUrl = await _appSettingsService.getApiBaseUrl();
      final esp32BaseUrl = await _appSettingsService.getEsp32BaseUrl();

      _apiBaseUrlController.text = apiBaseUrl;
      _esp32BaseUrlController.text = esp32BaseUrl;
    } catch (e) {
      setState(() {
        _message = 'Failed to load settings: $e';
        _isError = true;
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
      _message = null;
    });

    try {
      await _appSettingsService.saveApiBaseUrl(_apiBaseUrlController.text.trim());
      await _appSettingsService.saveEsp32BaseUrl(_esp32BaseUrlController.text.trim());

      setState(() {
        _message = 'Settings saved successfully.';
        _isError = false;
      });
    } catch (e) {
      setState(() {
        _message = 'Failed to save settings: $e';
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _resetToDefaults() async {
    setState(() {
      _isLoading = true;
      _message = null;
    });

    try {
      await _appSettingsService.resetToDefaults();
      await _loadSettings();
      setState(() {
        _message = 'Settings reset to defaults.';
        _isError = false;
      });
    } catch (e) {
      setState(() {
        _message = 'Failed to reset settings: $e';
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _apiBaseUrlController.dispose();
    _esp32BaseUrlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Local Network Settings'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_message != null)
                    Container(
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 16),
                      color: _isError ? Colors.red.shade50 : Colors.green.shade50,
                      child: Text(
                        _message!,
                        style: TextStyle(
                          color: _isError ? Colors.red : Colors.green,
                        ),
                      ),
                    ),
                  TextField(
                    controller: _apiBaseUrlController,
                    decoration: const InputDecoration(
                      labelText: 'FastAPI Server URL',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _esp32BaseUrlController,
                    decoration: const InputDecoration(
                      labelText: 'ESP32 Direct URL',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _saveSettings,
                    child: const Text('Save Settings'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: _resetToDefaults,
                    child: const Text('Reset Defaults'),
                  ),
                ],
              ),
            ),
    );
  }
}
