import 'package:intl/intl.dart';

class DateFormatter {
  static final DateFormat _dateTimeFormat = DateFormat('yyyy-MM-dd hh:mm:ss a');
  static final DateFormat _familyDateFormat = DateFormat('yyyy-MM-dd, h:mm:ss a');

  /// Formats a [DateTime] value as 'yyyy-MM-dd hh:mm:ss a'
  static String format(DateTime value) {
    return _dateTimeFormat.format(value);
  }

  /// Formats a raw ISO date string to local time in 'yyyy-MM-dd hh:mm:ss a' format
  static String formatRawLocal(String? raw) {
    if (raw == null || raw.trim().isEmpty) return '';
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;
    return format(parsed.toLocal());
  }

  /// Formats a raw ISO date string (without toLocal transition) to 'yyyy-MM-dd hh:mm:ss a' format
  static String formatRaw(String? raw) {
    if (raw == null || raw.trim().isEmpty) return '';
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;
    return format(parsed);
  }

  /// Formats a raw date string to 'yyyy-MM-dd, h:mm:ss a'
  static String formatFamilyDate(String? raw) {
    if (raw == null || raw.trim().isEmpty) return 'Not available';
    final parsed = DateTime.tryParse(raw.trim().replaceFirst(' ', 'T'));
    if (parsed == null) return raw;
    return _familyDateFormat.format(parsed);
  }

  static final DateFormat _doorsDateFormat = DateFormat('yyyy-MM-dd, hh:mm:ss a');
  static final DateFormat _timeOnlyFormat = DateFormat('hh:mm:ss a');

  /// Formats a raw date to local 'yyyy-MM-dd, hh:mm:ss a'
  static String formatDoorsDate(String? raw) {
    if (raw == null || raw.trim().isEmpty) return '';
    final cleaned = raw.trim();
    DateTime? parsed = DateTime.tryParse(cleaned);
    if (parsed == null && cleaned.contains(' ')) {
      parsed = DateTime.tryParse(cleaned.replaceFirst(' ', 'T'));
    }
    if (parsed == null) return raw;
    return _doorsDateFormat.format(parsed.toLocal());
  }

  /// Formats a raw date string to local 'hh:mm:ss a'
  static String formatTimeOnly(String? raw) {
    if (raw == null || raw.trim().isEmpty) return 'No backend reading yet';
    final cleaned = raw.trim();
    DateTime? parsed = DateTime.tryParse(cleaned);
    if (parsed == null && cleaned.contains(' ')) {
      parsed = DateTime.tryParse(cleaned.replaceFirst(' ', 'T'));
    }
    if (parsed == null) return raw;
    return _timeOnlyFormat.format(parsed.toLocal());
  }

  /// Formats a [DateTime] value as 'yyyy-MM-dd, hh:mm:ss a'
  static String formatWithComma(DateTime value) {
    return _doorsDateFormat.format(value);
  }
}
