import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../widgets/result_view.dart';

class FamilyScreen extends StatefulWidget {
  const FamilyScreen({super.key});

  @override
  State<FamilyScreen> createState() => _FamilyScreenState();
}

class _FamilyScreenState extends State<FamilyScreen> {
  final ApiService _apiService = ApiService();

  final TextEditingController _familyNameController = TextEditingController();
  final TextEditingController _familyMemberIdController = TextEditingController();

  bool _isLoading = false;
  dynamic _resultData;
  String? _errorMessage;

  @override
  void dispose() {
    _familyNameController.dispose();
    _familyMemberIdController.dispose();
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

  Future<Map<String, dynamic>> _addFamilyMemberFromInput() async {
    final name = _familyNameController.text.trim();

    if (name.isEmpty) {
      throw Exception('Please enter a family member name.');
    }

    final result = await _apiService.addFamilyMember(name: name);

    _familyNameController.clear();

    return result;
  }

  Future<Map<String, dynamic>> _attachTestFaceEmbeddingFromInput() async {
    final rawId = _familyMemberIdController.text.trim();
    final memberId = int.tryParse(rawId);

    if (memberId == null) {
      throw Exception('Please enter a valid family member ID.');
    }

    return _apiService.attachTestFaceEmbedding(memberId: memberId);
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
          const SizedBox(height: 8),
          TextField(
            controller: _familyMemberIdController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Family Member ID',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 8),
          _buildActionButton(
            label: 'Attach Test Face Embedding',
            onPressed: _attachTestFaceEmbeddingFromInput,
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
