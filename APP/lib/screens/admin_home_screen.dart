import 'dart:convert';

import 'package:flutter/material.dart';

import '../models/door_event.dart';
import '../models/energy_forecast.dart';
import '../models/energy_reading.dart';
import '../models/family_member.dart';
import '../services/api_service.dart';
import '../services/direct_device_service.dart';

class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({super.key});

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  final ApiService _apiService = ApiService();
  final DirectDeviceService _directDeviceService = DirectDeviceService();
  final TextEditingController _familyNameController = TextEditingController();

  bool _isLoading = false;
  String _result = 'No request yet.';

  @override
  void dispose() {
    _familyNameController.dispose();
    super.dispose();
  }

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

  Future<Map<String, dynamic>> _directOpenDoorAndLog() async {
    final directResult = await _directDeviceService.directOpenDoor();
    final logResult = await _apiService.logDirectDoorOpen();

    return {
      'direct_open_result': directResult,
      'server_log_result': logResult,
    };
  }

  Future<Map<String, dynamic>> _addFamilyMemberFromInput() async {
    final name = _familyNameController.text.trim();

    if (name.isEmpty) {
      throw Exception('Please enter a family member name.');
    }

    final result = await _apiService.addFamilyMember(name: name);

    _familyNameController.clear();

    return result;
  }

  String _formatResult(dynamic data) {
    if (data == null) {
      return 'No data found.';
    }

    if (data is DoorEvent) {
      return _toPrettyJson(data.toJson());
    }

    if (data is EnergyReading) {
      return _toPrettyJson(data.toJson());
    }

    if (data is EnergyForecast) {
      return _toPrettyJson(data.toJson());
    }

    if (data is FamilyMember) {
      return _toPrettyJson(data.toJson());
    }

    if (data is List<DoorEvent>) {
      return _toPrettyJson(data.map((event) => event.toJson()).toList());
    }

    if (data is List<FamilyMember>) {
      return _toPrettyJson(data.map((member) => member.toJson()).toList());
    }

    return _toPrettyJson(data);
  }

  String _toPrettyJson(dynamic data) {
    try {
      const encoder = JsonEncoder.withIndent('  ');
      return encoder.convert(data);
    } catch (_) {
      return data.toString();
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

  Widget _buildActionButton({
    required String label,
    required Future<dynamic> Function() onPressed,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _isLoading ? null : () => _runRequest(onPressed),
          child: Text(label),
        ),
      ),
    );
  }

  Widget _buildControls() {
    return SingleChildScrollView(
      child: Column(
        children: [
          _buildSectionTitle('Server'),
          _buildActionButton(
            label: 'Check Server',
            onPressed: _apiService.healthCheck,
          ),
          _buildSectionTitle('Door Control'),
          _buildActionButton(
            label: 'Open Door Through Server',
            onPressed: _apiService.openDoor,
          ),
          _buildActionButton(
            label: 'Direct Open Door',
            onPressed: _directOpenDoorAndLog,
          ),
          _buildActionButton(
            label: 'Latest Door Event',
            onPressed: _apiService.getLatestDoorEvent,
          ),
          _buildActionButton(
            label: 'Door Logs',
            onPressed: _apiService.getDoorLogs,
          ),
          _buildSectionTitle('Family Members'),
          TextField(
            controller: _familyNameController,
            decoration: const InputDecoration(
              labelText: 'Family Member Name',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          _buildActionButton(
            label: 'Add Family Member',
            onPressed: _addFamilyMemberFromInput,
          ),
          _buildActionButton(
            label: 'Add Test Family Member',
            onPressed: _apiService.addTestFamilyMember,
          ),
          _buildActionButton(
            label: 'Family Members List',
            onPressed: _apiService.getFamilyMembers,
          ),
          _buildSectionTitle('Energy'),
          _buildActionButton(
            label: 'Latest Energy Reading',
            onPressed: _apiService.getLatestEnergyReading,
          ),
          _buildActionButton(
            label: 'Latest Energy Forecast',
            onPressed: _apiService.getLatestEnergyForecast,
          ),
        ],
      ),
    );
  }

  Widget _buildResultBox() {
    return Container(
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
            Expanded(
              flex: 3,
              child: _buildControls(),
            ),
            const SizedBox(height: 12),
            _buildSectionTitle('Result'),
            Expanded(
              flex: 2,
              child: _buildResultBox(),
            ),
          ],
        ),
      ),
    );
  }
}