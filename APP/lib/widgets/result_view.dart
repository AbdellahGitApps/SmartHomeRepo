import 'dart:convert';
import 'package:flutter/material.dart';

import '../models/door_event.dart';
import '../models/energy_forecast.dart';
import '../models/energy_reading.dart';
import '../models/family_member.dart';

class ResultView extends StatelessWidget {
  final dynamic data;
  final String? error;

  const ResultView({super.key, this.data, this.error});

  @override
  Widget build(BuildContext context) {
    if (error != null) {
      return Card(
        color: Colors.red.shade50,
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            error!,
            style: const TextStyle(color: Colors.red),
          ),
        ),
      );
    }

    if (data == null) {
      return const Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text('No data found.', style: TextStyle(color: Colors.grey)),
        ),
      );
    }

    dynamic resolvedData = _resolveData(data);

    if (resolvedData is List) {
      if (resolvedData.isEmpty) {
        return const Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: EdgeInsets.all(16.0),
            child: Text('List is empty.', style: TextStyle(color: Colors.grey)),
          ),
        );
      }
      return ListView.builder(
        itemCount: resolvedData.length,
        itemBuilder: (context, index) {
          return _buildMapCard(resolvedData[index]);
        },
      );
    }

    if (resolvedData is Map) {
      return SingleChildScrollView(
        child: _buildMapCard(resolvedData),
      );
    }

    return SingleChildScrollView(
      child: Card(
        margin: EdgeInsets.zero,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(resolvedData.toString()),
        ),
      ),
    );
  }

  dynamic _resolveData(dynamic data) {
    if (data is DoorEvent) return data.toJson();
    if (data is EnergyReading) return data.toJson();
    if (data is EnergyForecast) return data.toJson();
    if (data is FamilyMember) return data.toJson();
    
    if (data is List) {
      return data.map((e) => _resolveData(e)).toList();
    }
    
    return data;
  }

  Widget _buildMapCard(dynamic item) {
    if (item is! Map) {
      return Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Text(item.toString()),
        ),
      );
    }

    final map = item;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: map.entries.map<Widget>((entry) {
            final key = entry.key.toString();
            final value = entry.value;
            
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 2,
                    child: Text(
                      '$key:',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  Expanded(
                    flex: 3,
                    child: _buildValueText(value),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildValueText(dynamic value) {
    if (value == null) {
      return const Text('null', style: TextStyle(color: Colors.grey));
    }
    if (value is Map || value is List) {
      return Text(
        const JsonEncoder.withIndent('  ').convert(value),
        style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
      );
    }
    return Text(value.toString());
  }
}
