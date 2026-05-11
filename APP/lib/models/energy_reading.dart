class EnergyReading {
  final double? voltage;
  final double? current;
  final double? power;
  final double? energyKwh;
  final String? createdAt;

  EnergyReading({
    this.voltage,
    this.current,
    this.power,
    this.energyKwh,
    this.createdAt,
  });

  factory EnergyReading.fromJson(Map<String, dynamic> json) {
    return EnergyReading(
      voltage: (json['voltage'] as num?)?.toDouble(),
      current: (json['current'] as num?)?.toDouble(),
      power: (json['power'] as num?)?.toDouble(),
      energyKwh: (json['energy_kwh'] as num?)?.toDouble(),
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'voltage': voltage,
      'current': current,
      'power': power,
      'energy_kwh': energyKwh,
      'created_at': createdAt,
    };
  }
}