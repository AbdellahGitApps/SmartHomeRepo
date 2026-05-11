class DoorEvent {
  final int? id;
  final String? type;
  final String? status;
  final String? source;
  final String? reason;
  final String? mqttTopic;
  final bool? mqttPublished;
  final String? mqttError;
  final String? createdAt;

  DoorEvent({
    this.id,
    this.type,
    this.status,
    this.source,
    this.reason,
    this.mqttTopic,
    this.mqttPublished,
    this.mqttError,
    this.createdAt,
  });

  factory DoorEvent.fromJson(Map<String, dynamic> json) {
    return DoorEvent(
      id: json['id'],
      type: json['type'],
      status: json['status'],
      source: json['source'],
      reason: json['reason'],
      mqttTopic: json['mqtt_topic'],
      mqttPublished: json['mqtt_published'],
      mqttError: json['mqtt_error'],
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'type': type,
      'status': status,
      'source': source,
      'reason': reason,
      'mqtt_topic': mqttTopic,
      'mqtt_published': mqttPublished,
      'mqtt_error': mqttError,
      'created_at': createdAt,
    };
  }
}