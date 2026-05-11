import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/result_view.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  dynamic _resultData;
  String? _errorMessage;

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

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 16, bottom: 8),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
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
          Expanded(flex: 3, child: _buildControls()),
          const SizedBox(height: 12),
          _buildSectionTitle('Result'),
          Expanded(flex: 2, child: _buildResultBox()),
        ],
      ),
    );
  }
}
