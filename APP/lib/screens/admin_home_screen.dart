import 'dart:convert';

import 'package:flutter/material.dart';

import '../services/api_service.dart';

class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({super.key});

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  final ApiService _apiService = ApiService();

  bool _isLoading = false;
  String _result = 'No request yet.';

  Future<void> _runRequest(Future<dynamic> Function() request) async {
    setState(() {
      _isLoading = true;
      _result = 'Loading...';
    });

    try {
      final data = await request();

      setState(() {
        _result = _formatResult(data);
      });
    } catch (error) {
      setState(() {
        _result = 'Error:\n$error';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  String _formatResult(dynamic data) {
    try {
      const encoder = JsonEncoder.withIndent('  ');
      return encoder.convert(data);
    } catch (_) {
      return data.toString();
    }
  }

  Widget _buildActionButton({
    required String label,
    required Future<dynamic> Function() onPressed,
  }) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _isLoading ? null : () => _runRequest(onPressed),
        child: Text(label),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Smart Home Admin'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildActionButton(
              label: 'Check Server',
              onPressed: _apiService.healthCheck,
            ),
            _buildActionButton(
              label: 'Open Door',
              onPressed: _apiService.openDoor,
            ),
            _buildActionButton(
              label: 'Latest Door Event',
              onPressed: _apiService.getLatestDoorEvent,
            ),
            _buildActionButton(
              label: 'Door Logs',
              onPressed: _apiService.getDoorLogs,
            ),
            _buildActionButton(
              label: 'Latest Energy Reading',
              onPressed: _apiService.getLatestEnergyReading,
            ),
            _buildActionButton(
              label: 'Latest Energy Forecast',
              onPressed: _apiService.getLatestEnergyForecast,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SingleChildScrollView(
                  child: Text(
                    _result,
                    style: const TextStyle(fontFamily: 'monospace'),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}