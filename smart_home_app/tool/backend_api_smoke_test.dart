import 'package:smart_home_app/services/backend_api_service.dart';

Future<void> main() async {
  final api = BackendApiService();

  try {
    final energyStatus = await api.getEnergyStatus();
    print('ENERGY STATUS: $energyStatus');

    final energyLatest = await api.getEnergyLatest();
    print('ENERGY LATEST: $energyLatest');

    final energyLogs = await api.getEnergyLogs(limit: 5);
    print('ENERGY LOGS: $energyLogs');

    final forecastLatest = await api.getEnergyForecastLatest();
    print('FORECAST LATEST: $forecastLatest');

    final faceStatus = await api.getFaceStatus();
    print('FACE STATUS: $faceStatus');

    final faceEvents = await api.getFaceEvents(limit: 5);
    print('FACE EVENTS: $faceEvents');
  } finally {
    api.close();
  }
}
