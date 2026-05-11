import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../services/direct_device_service.dart';
import '../widgets/result_view.dart';

class DoorScreen extends StatefulWidget {
  const DoorScreen({super.key});

  @override
  State<DoorScreen> createState() => _DoorScreenState();
}

class _DoorScreenState extends State<DoorScreen> {
  final ApiService _apiService = ApiService();
  final DirectDeviceService _directDeviceService = DirectDeviceService();

  final TextEditingController _doorEventIdController = TextEditingController();
  final TextEditingController _unknownPersonNameController =
      TextEditingController();

  bool _isLoading = false;
  dynamic _resultData;
  String? _errorMessage;
  Map<String, dynamic>? _pendingEvent;

  @override
  void dispose() {
    _doorEventIdController.dispose();
    _unknownPersonNameController.dispose();
    super.dispose();
  }

  Future<void> _runRequest(Future<dynamic> Function() request) async {
    setState(() {
      _isLoading = true;
      _resultData = null;
      _errorMessage = null;
    });

    try {
      final data = await request();

      setState(() {
        _resultData = data;
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _handlePendingAction(Future<dynamic> Function() action) async {
    await _runRequest(action);
    if (_errorMessage == null) {
      setState(() {
        _pendingEvent = null;
      });
    }
  }

  Future<void> _getPendingUnknownEvent() async {
    setState(() {
      _isLoading = true;
      _resultData = null;
      _errorMessage = null;
      _pendingEvent = null;
    });

    try {
      final data = await _apiService.getPendingDoorEvent();
      setState(() {
        _resultData = data;

        if (data.containsKey('event') && data['event'] is Map) {
          _pendingEvent = Map<String, dynamic>.from(data['event']);
        } else if (data.containsKey('id')) {
          _pendingEvent = Map<String, dynamic>.from(data);
        }

        if (_pendingEvent != null && _pendingEvent!.containsKey('id')) {
          _doorEventIdController.text = _pendingEvent!['id'].toString();
        }
      });
    } catch (error) {
      setState(() {
        _errorMessage = error.toString();
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  int _readDoorEventId() {
    final rawId = _doorEventIdController.text.trim();
    final eventId = int.tryParse(rawId);

    if (eventId == null) {
      throw Exception('Please enter a valid door event ID.');
    }

    return eventId;
  }

  Future<Map<String, dynamic>> _directOpenDoorAndLog() async {
    final directResult = await _directDeviceService.directOpenDoor();
    final logResult = await _apiService.logDirectDoorOpen();

    return {
      'direct_open_result': directResult,
      'server_log_result': logResult,
    };
  }

  Future<Map<String, dynamic>> _openPendingDoorEventFromInput() async {
    final eventId = _readDoorEventId();
    return _apiService.openPendingDoorEvent(eventId: eventId);
  }

  Future<Map<String, dynamic>> _denyPendingDoorEventFromInput() async {
    final eventId = _readDoorEventId();
    return _apiService.denyPendingDoorEvent(eventId: eventId);
  }

  Future<Map<String, dynamic>> _addPendingEventToFamilyFromInput() async {
    final eventId = _readDoorEventId();
    final name = _unknownPersonNameController.text.trim();

    if (name.isEmpty) {
      throw Exception('Please enter a name for the unknown person.');
    }

    final result = await _apiService.addPendingEventToFamily(
      eventId: eventId,
      name: name,
    );

    _unknownPersonNameController.clear();

    return result;
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
    bool isPendingAction = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _isLoading
              ? null
              : () => isPendingAction
                  ? _handlePendingAction(onPressed)
                  : _runRequest(onPressed),
          child: Text(label),
        ),
      ),
    );
  }

  Widget _buildPendingEventCard() {
    if (_pendingEvent == null) return const SizedBox.shrink();

    return Card(
      color: Colors.orange.shade50,
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Pending Unknown Person',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.orange,
              ),
            ),
            const SizedBox(height: 8),
            Text('Event ID: ${_pendingEvent!['id']}'),
            Text('Status: ${_pendingEvent!['status'] ?? 'Unknown'}'),
            Text('Source: ${_pendingEvent!['source'] ?? 'Unknown'}'),
            Text('Reason: ${_pendingEvent!['reason'] ?? 'Unknown'}'),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: _isLoading ? null : () => _handlePendingAction(_openPendingDoorEventFromInput),
                    child: const Text('Open'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                    onPressed: _isLoading ? null : () => _handlePendingAction(_denyPendingDoorEventFromInput),
                    child: const Text('Deny'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _unknownPersonNameController,
                    decoration: const InputDecoration(
                      labelText: 'New Family Member Name',
                      border: OutlineInputBorder(),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLoading ? null : () => _handlePendingAction(_addPendingEventToFamilyFromInput),
                  child: const Text('Add to Family'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildControls() {
    return SingleChildScrollView(
      child: Column(
        children: [
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

          _buildSectionTitle('Unknown Door Event'),
          _buildActionButton(
            label: 'Create Test Unknown Event',
            onPressed: _apiService.createTestUnknownDoorEvent,
          ),
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _getPendingUnknownEvent,
                child: const Text('Get Pending Unknown Event'),
              ),
            ),
          ),
          
          _buildPendingEventCard(),

          TextField(
            controller: _doorEventIdController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Door Event ID',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          _buildActionButton(
            label: 'Open Pending Event',
            onPressed: _openPendingDoorEventFromInput,
            isPendingAction: true,
          ),
          _buildActionButton(
            label: 'Deny Pending Event',
            onPressed: _denyPendingDoorEventFromInput,
            isPendingAction: true,
          ),
          TextField(
            controller: _unknownPersonNameController,
            decoration: const InputDecoration(
              labelText: 'Unknown Person Name',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          _buildActionButton(
            label: 'Add Pending Person to Family',
            onPressed: _addPendingEventToFamilyFromInput,
            isPendingAction: true,
          ),

          _buildSectionTitle('Face Verification'),
          _buildActionButton(
            label: 'Verify Test Known Face',
            onPressed: _apiService.verifyTestKnownFace,
          ),
          _buildActionButton(
            label: 'Verify Test Unknown Face',
            onPressed: _apiService.verifyTestUnknownFace,
          ),
        ],
      ),
    );
  }

  Widget _buildResultBox() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ResultView(
        data: _resultData,
        error: _errorMessage,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
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
    );
  }
}
