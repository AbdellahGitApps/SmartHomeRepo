import 'package:flutter/material.dart';

class ResultView extends StatelessWidget {
  final dynamic data;
  final String? error;

  const ResultView({
    super.key,
    this.data,
    this.error,
  });

  @override
  Widget build(BuildContext context) {
    if (error != null && error!.trim().isNotEmpty) {
      return _buildScrollableCard(
        context,
        child: _buildErrorContent(context, error!),
      );
    }

    final normalizedData = _normalizeValue(data);

    if (normalizedData == null) {
      return _buildScrollableCard(
        context,
        child: Text(
          'No data found.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      );
    }

    return _buildScrollableCard(
      context,
      child: _buildReadableValue(context, normalizedData),
    );
  }

  dynamic _normalizeValue(dynamic value) {
    if (value == null) {
      return null;
    }

    if (value is String || value is num || value is bool) {
      return value;
    }

    if (value is Map) {
      return value.map(
        (key, item) => MapEntry(key.toString(), _normalizeValue(item)),
      );
    }

    if (value is Iterable) {
      return value.map(_normalizeValue).toList();
    }

    try {
      final dynamic jsonValue = value.toJson();
      return _normalizeValue(jsonValue);
    } catch (_) {
      return value.toString();
    }
  }

  Widget _buildScrollableCard(
    BuildContext context, {
    required Widget child,
  }) {
    return Card(
      child: ConstrainedBox(
        constraints: const BoxConstraints(
          maxHeight: 360,
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(14),
          child: child,
        ),
      ),
    );
  }

  Widget _buildErrorContent(BuildContext context, String message) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Icon(Icons.error_outline),
        const SizedBox(width: 10),
        Expanded(
          child: SelectableText(
            message,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ),
      ],
    );
  }

  Widget _buildReadableValue(BuildContext context, dynamic value) {
    if (value == null) {
      return const Text('No data');
    }

    if (value is Map) {
      return _buildMap(
        context,
        Map<String, dynamic>.from(value),
      );
    }

    if (value is List) {
      return _buildList(context, value);
    }

    return SelectableText(_formatSimpleValue(value));
  }

  Widget _buildMap(
    BuildContext context,
    Map<String, dynamic> map, {
    int level = 0,
  }) {
    if (map.isEmpty) {
      return const Text('No data');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: map.entries.map((entry) {
        return _buildEntry(
          context,
          entry.key,
          entry.value,
          level: level,
        );
      }).toList(),
    );
  }

  Widget _buildEntry(
    BuildContext context,
    String key,
    dynamic value, {
    required int level,
  }) {
    final leftPadding = level * 12.0;

    if (value is Map) {
      return Padding(
        padding: EdgeInsets.only(
          left: leftPadding,
          bottom: 10,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _formatKey(key),
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                border: Border.all(
                  color: Theme.of(context).dividerColor,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: _buildMap(
                context,
                Map<String, dynamic>.from(value),
                level: level + 1,
              ),
            ),
          ],
        ),
      );
    }

    if (value is List) {
      return Padding(
        padding: EdgeInsets.only(
          left: leftPadding,
          bottom: 10,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _formatKey(key),
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
            ),
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                border: Border.all(
                  color: Theme.of(context).dividerColor,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: _buildList(context, value, level: level + 1),
            ),
          ],
        ),
      );
    }

    return Padding(
      padding: EdgeInsets.only(
        left: leftPadding,
        bottom: 8,
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 180,
            child: Text(
              '${_formatKey(key)}:',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          Expanded(
            child: SelectableText(
              _formatSimpleValue(value),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildList(
    BuildContext context,
    List list, {
    int level = 0,
  }) {
    if (list.isEmpty) {
      return const Text('No data');
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: List.generate(list.length, (index) {
        final item = list[index];

        if (item is Map) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                border: Border.all(
                  color: Theme.of(context).dividerColor,
                ),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Item ${index + 1}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 6),
                  _buildMap(
                    context,
                    Map<String, dynamic>.from(item),
                    level: level + 1,
                  ),
                ],
              ),
            ),
          );
        }

        if (item is List) {
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: _buildList(
              context,
              item,
              level: level + 1,
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: SelectableText(
            '${index + 1}. ${_formatSimpleValue(item)}',
          ),
        );
      }),
    );
  }

  String _formatKey(String key) {
    final words = key
        .replaceAll('_', ' ')
        .replaceAll('-', ' ')
        .split(' ')
        .where((word) => word.trim().isNotEmpty)
        .toList();

    if (words.isEmpty) {
      return key;
    }

    return words.map((word) {
      return word[0].toUpperCase() + word.substring(1);
    }).join(' ');
  }

  String _formatSimpleValue(dynamic value) {
    if (value == null) {
      return 'No data';
    }

    if (value is bool) {
      return value ? 'Yes' : 'No';
    }

    return value.toString();
  }
}