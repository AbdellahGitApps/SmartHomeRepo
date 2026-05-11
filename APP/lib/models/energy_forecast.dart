class EnergyForecast {
  final double? predictedKwh;
  final double? predictedBill;
  final String? modelUsed;
  final String? createdAt;

  EnergyForecast({
    this.predictedKwh,
    this.predictedBill,
    this.modelUsed,
    this.createdAt,
  });

  factory EnergyForecast.fromJson(Map<String, dynamic> json) {
    return EnergyForecast(
      predictedKwh: (json['predicted_kwh'] as num?)?.toDouble(),
      predictedBill: (json['predicted_bill'] as num?)?.toDouble(),
      modelUsed: json['model_used'],
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'predicted_kwh': predictedKwh,
      'predicted_bill': predictedBill,
      'model_used': modelUsed,
      'created_at': createdAt,
    };
  }
}