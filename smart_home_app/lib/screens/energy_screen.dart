import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/backend_api_service.dart';
import '../widgets/simple_energy_chart.dart';
import 'package:lucide_icons/lucide_icons.dart';

class EnergyScreen extends StatefulWidget {
  const EnergyScreen({super.key});

  @override
  State<EnergyScreen> createState() => _EnergyScreenState();
}

class _EnergyScreenState extends State<EnergyScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fade1;
  late Animation<Offset> _slide1;
  late Animation<double> _fade2;
  late Animation<Offset> _slide2;

  final BackendApiService _api = BackendApiService();

  bool _isLoadingEnergy = true;
  String? _energyError;
  Map<String, dynamic>? _latestEnergy;
  List<Map<String, dynamic>> _energyLogs = [];
  List<Map<String, dynamic>> _forecasts = [];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
    _fade1 = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.4, curve: Curves.easeOut),
      ),
    );
    _slide1 = Tween<Offset>(begin: const Offset(0, 0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.0, 0.4, curve: Curves.easeOut),
          ),
        );
    _fade2 = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.3, 0.7, curve: Curves.easeOut),
      ),
    );
    _slide2 = Tween<Offset>(begin: const Offset(0, 0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.3, 0.7, curve: Curves.easeOut),
          ),
        );
    _controller.forward();
    _loadEnergyData();
  }

  @override
  void dispose() {
    _api.close();
    _controller.dispose();
    super.dispose();
  }

  Future<void> _loadEnergyData() async {
    setState(() {
      _isLoadingEnergy = true;
      _energyError = null;
    });

    try {
      final latestResponse = await _api.getEnergyLatest();
      final logsResponse = await _api.getEnergyLogs(limit: 20);
      final forecastResponse = await _api.getEnergyForecastLatest(limit: 4);

      final latest = latestResponse['latest'];
      final logs = logsResponse['logs'];
      final forecasts = forecastResponse['forecasts'];

      if (!mounted) return;

      setState(() {
        _latestEnergy = latest is Map
            ? Map<String, dynamic>.from(latest)
            : null;
        _energyLogs = logs is List
            ? logs
                  .whereType<Map>()
                  .map((item) => Map<String, dynamic>.from(item))
                  .toList()
            : [];
        _forecasts = forecasts is List
            ? forecasts
                  .whereType<Map>()
                  .map((item) => Map<String, dynamic>.from(item))
                  .toList()
            : [];
        _isLoadingEnergy = false;
      });
    } catch (error) {
      if (!mounted) return;

      setState(() {
        _energyError = error.toString();
        _isLoadingEnergy = false;
      });
    }
  }

  double _num(dynamic value, [double fallback = 0.0]) {
    if (value == null) return fallback;
    if (value is num) return value.toDouble();
    return double.tryParse(value.toString()) ?? fallback;
  }

  String _fmt(dynamic value, {int digits = 1}) {
    return _num(value).toStringAsFixed(digits);
  }

  double get _latestVoltage => _num(_latestEnergy?['voltage'], 220.0);
  double get _latestCurrent => _num(_latestEnergy?['current'], 0.0);
  double get _latestWatts => _num(_latestEnergy?['watts'], 0.0);
  double get _latestKw => _latestWatts / 1000.0;
  double get _latestKwh => _num(
    _latestEnergy?['kwh_today'],
    _num(_latestEnergy?['consumption_kwh']),
  );

  double get _forecastTotal {
    return _forecasts.fold<double>(
      0,
      (sum, item) => sum + _num(item['predicted_kwh']),
    );
  }

  List<double> get _chartValues {
    final logs = _energyLogs.reversed.take(7).toList();

    if (logs.isEmpty) {
      return const [0.4, 0.7, 0.5, 0.9, 0.6, 0.8, 0.3];
    }

    return logs.map((item) {
      final kwh = _num(item['kwh_today'], _num(item['consumption_kwh']));
      if (kwh > 0) return kwh;

      final watts = _num(item['watts']);
      return watts > 0 ? watts / 1000.0 : 0.1;
    }).toList();
  }

  List<String> get _chartLabels {
    final logs = _energyLogs.reversed.take(7).toList();

    if (logs.isEmpty) {
      return const ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
    }

    return logs.map((item) {
      final raw =
          item['timestamp']?.toString() ?? item['reading_date']?.toString();
      if (raw == null || raw.isEmpty) return 'Now';

      final parsed = DateTime.tryParse(raw);
      if (parsed == null) return raw.length > 5 ? raw.substring(0, 5) : raw;

      final hour = parsed.hour.toString().padLeft(2, '0');
      final minute = parsed.minute.toString().padLeft(2, '0');
      return '$hour:$minute';
    }).toList();
  }

  String get _latestTimestamp {
    final raw = _latestEnergy?['timestamp']?.toString();
    if (raw == null || raw.isEmpty) return 'No backend reading yet';

    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return raw;

    return '${parsed.hour.toString().padLeft(2, '0')}:${parsed.minute.toString().padLeft(2, '0')}';
  }

  String get _mainDeviceId {
    return _latestEnergy?['device_id']?.toString() ?? 'No device yet';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.energy),
          actions: [
            IconButton(
              tooltip: 'Refresh backend data',
              onPressed: _loadEnergyData,
              icon: const Icon(LucideIcons.refreshCcw),
            ),
          ],
          bottom: TabBar(
            indicatorColor: Theme.of(context).primaryColor,
            labelColor: Theme.of(context).primaryColor,
            isScrollable: true,
            tabs: [
              Tab(text: l10n.realTimeReadings),
              Tab(text: l10n.energyReports),
              Tab(text: l10n.predictions),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _buildRealTimeTab(context, l10n, isDark),
            _buildReportsTab(context, l10n, isDark),
            _buildPredictionsTab(context, l10n, isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildBackendStatus(BuildContext context, bool isDark) {
    if (_isLoadingEnergy) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(context, isDark),
        child: const Row(
          children: [
            SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
            SizedBox(width: 12),
            Text('Loading backend energy data...'),
          ],
        ),
      );
    }

    if (_energyError != null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(context, isDark),
        child: Text(
          'Backend connection error: $_energyError',
          style: const TextStyle(color: Colors.red),
        ),
      );
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: _cardDecoration(context, isDark),
      child: Text(
        'Backend connected · $_mainDeviceId · Last reading $_latestTimestamp',
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    );
  }

  Widget _buildRealTimeTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    return RefreshIndicator(
      onRefresh: _loadEnergyData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildBackendStatus(context, isDark),
            const SizedBox(height: 24),

            SlideTransition(
              position: _slide1,
              child: FadeTransition(
                opacity: _fade1,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: _cardDecoration(context, isDark),
                  child: Column(
                    children: [
                      Text(
                        l10n.realTimeReadings,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _buildSensorGauge(
                            context,
                            l10n.voltage,
                            _fmt(_latestVoltage),
                            l10n.volts,
                            LucideIcons.activity,
                            Colors.blue,
                            isDark,
                          ),
                          _buildSensorGauge(
                            context,
                            l10n.current,
                            _fmt(_latestCurrent),
                            l10n.amps,
                            LucideIcons.zap,
                            Colors.orange,
                            isDark,
                          ),
                          _buildSensorGauge(
                            context,
                            l10n.power,
                            _fmt(_latestWatts, digits: 0),
                            l10n.watts,
                            LucideIcons.gauge,
                            Colors.green,
                            isDark,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),

            SlideTransition(
              position: _slide1,
              child: FadeTransition(
                opacity: _fade1,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: _cardDecoration(context, isDark),
                  child: Column(
                    children: [
                      Text(
                        l10n.energyConsumption,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const SizedBox(height: 16),
                      TweenAnimationBuilder<double>(
                        tween: Tween(begin: 0, end: _latestKw),
                        duration: const Duration(milliseconds: 1200),
                        curve: Curves.easeOutCubic,
                        builder: (context, value, child) {
                          return Text(
                            '${value.toStringAsFixed(1)} ${l10n.kW}',
                            style: Theme.of(context).textTheme.displayLarge!
                                .copyWith(
                                  color: Theme.of(context).primaryColor,
                                ),
                          );
                        },
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _latestEnergy == null
                            ? 'Waiting for backend reading'
                            : '${_fmt(_latestKwh)} ${l10n.kWh} today',
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 32),

            FadeTransition(
              opacity: _fade2,
              child: Text(
                l10n.weeklyOverview,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: 24),
            SlideTransition(
              position: _slide2,
              child: FadeTransition(
                opacity: _fade2,
                child: Container(
                  height: 300,
                  padding: const EdgeInsets.all(24),
                  decoration: _cardDecoration(context, isDark),
                  child: SimpleEnergyChart(
                    values: _chartValues,
                    labels: _chartLabels,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReportsTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    final logsTotal = _energyLogs.fold<double>(
      0,
      (sum, item) =>
          sum + _num(item['kwh_today'], _num(item['consumption_kwh'])),
    );

    final reports = [
      {
        'period': l10n.daily,
        'total': _fmt(_latestKwh),
        'avg': _fmt(_latestKw),
        'peak': _fmt(_latestKw),
      },
      {
        'period': l10n.weekly,
        'total': _fmt(logsTotal),
        'avg': _fmt(_energyLogs.isEmpty ? 0 : logsTotal / _energyLogs.length),
        'peak': _fmt(
          _energyLogs.fold<double>(0, (max, item) {
            final kw = _num(item['watts']) / 1000.0;
            return kw > max ? kw : max;
          }),
        ),
      },
      {
        'period': l10n.monthly,
        'total': _fmt(_forecastTotal),
        'avg': _fmt(
          _forecasts.isEmpty ? 0 : _forecastTotal / _forecasts.length,
        ),
        'peak': _fmt(_forecastTotal),
      },
    ];

    return RefreshIndicator(
      onRefresh: _loadEnergyData,
      child: ListView.separated(
        padding: const EdgeInsets.all(24),
        itemCount: reports.length + 1,
        separatorBuilder: (_, __) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          if (index == 0) {
            return _buildBackendStatus(context, isDark);
          }

          final r = reports[index - 1];
          return Container(
            padding: const EdgeInsets.all(24),
            decoration: _cardDecoration(context, isDark),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      r['period']!,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: Theme.of(context).primaryColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${r['total']} ${l10n.kWh}',
                        style: TextStyle(
                          color: Theme.of(context).primaryColor,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    _buildReportStat(
                      context,
                      l10n.totalConsumption,
                      '${r['total']} ${l10n.kWh}',
                      LucideIcons.barChart3,
                      isDark,
                    ),
                    const SizedBox(width: 16),
                    _buildReportStat(
                      context,
                      l10n.averageUsage,
                      '${r['avg']} ${l10n.kW}',
                      LucideIcons.trendingUp,
                      isDark,
                    ),
                    const SizedBox(width: 16),
                    _buildReportStat(
                      context,
                      l10n.peakUsage,
                      '${r['peak']} ${l10n.kW}',
                      LucideIcons.arrowUpCircle,
                      isDark,
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildPredictionsTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    final firstForecast = _forecasts.isNotEmpty
        ? _num(_forecasts.first['predicted_kwh'])
        : 0.0;

    final predictions = [
      {
        'period': l10n.nextDay,
        'value': _latestKwh > 0 ? _latestKwh * 1.05 : firstForecast / 7.0,
        'icon': LucideIcons.clock,
        'comparison': 'Estimated from backend reading',
        'isIncrease': true,
      },
      {
        'period': l10n.nextWeek,
        'value': firstForecast,
        'icon': LucideIcons.calendar,
        'comparison': 'Latest backend forecast',
        'isIncrease': firstForecast >= _latestKwh,
      },
      {
        'period': l10n.nextMonth,
        'value': _forecastTotal,
        'icon': LucideIcons.calendarDays,
        'comparison': 'Sum of backend forecast weeks',
        'isIncrease': true,
      },
    ];

    return RefreshIndicator(
      onRefresh: _loadEnergyData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildBackendStatus(context, isDark),
            const SizedBox(height: 24),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor.withOpacity(0.08),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: Theme.of(context).primaryColor.withOpacity(0.2),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    LucideIcons.brain,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _forecasts.isEmpty
                          ? 'No backend forecast yet. Run the forecast API first.'
                          : l10n.basedOnHistory,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            ...predictions.map(
              (p) => Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Container(
                  padding: const EdgeInsets.all(24),
                  decoration: _cardDecoration(context, isDark),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Theme.of(
                            context,
                          ).primaryColor.withOpacity(0.15),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          p['icon'] as IconData,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                      const SizedBox(width: 20),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              p['period'] as String,
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              l10n.predictedUsage,
                              style: Theme.of(context).textTheme.bodyMedium,
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Icon(
                                  (p['isIncrease'] as bool)
                                      ? LucideIcons.trendingUp
                                      : LucideIcons.trendingDown,
                                  size: 14,
                                  color: (p['isIncrease'] as bool)
                                      ? Colors.red
                                      : Colors.green,
                                ),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    p['comparison'] as String,
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: (p['isIncrease'] as bool)
                                          ? Colors.red
                                          : Colors.green,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      TweenAnimationBuilder<double>(
                        tween: Tween(begin: 0, end: p['value'] as double),
                        duration: const Duration(milliseconds: 1200),
                        curve: Curves.easeOutCubic,
                        builder: (context, value, _) {
                          return Text(
                            '${value.toStringAsFixed(1)} ${l10n.kWh}',
                            style: Theme.of(context).textTheme.headlineSmall!
                                .copyWith(
                                  color: Theme.of(context).primaryColor,
                                  fontWeight: FontWeight.bold,
                                ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSensorGauge(
    BuildContext context,
    String label,
    String value,
    String unit,
    IconData icon,
    Color color,
    bool isDark,
  ) {
    final parsedValue = double.tryParse(value) ?? 0.0;

    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        const SizedBox(height: 10),
        TweenAnimationBuilder<double>(
          tween: Tween(begin: 0, end: parsedValue),
          duration: const Duration(milliseconds: 1200),
          curve: Curves.easeOutCubic,
          builder: (context, v, _) {
            return Text(
              v.toStringAsFixed(value.contains('.') ? 1 : 0),
              style: Theme.of(context).textTheme.titleLarge!.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            );
          },
        ),
        Text(unit, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 4),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }

  Widget _buildReportStat(
    BuildContext context,
    String label,
    String value,
    IconData icon,
    bool isDark,
  ) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, size: 18, color: Theme.of(context).primaryColor),
          const SizedBox(height: 6),
          Text(
            value,
            style: Theme.of(
              context,
            ).textTheme.titleMedium!.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  BoxDecoration _cardDecoration(BuildContext context, bool isDark) {
    return BoxDecoration(
      color: isDark
          ? Theme.of(context).colorScheme.surface
          : Theme.of(context).cardColor,
      borderRadius: BorderRadius.circular(24),
      border: isDark
          ? Border.all(color: const Color(0xFF334155), width: 1)
          : null,
      boxShadow: isDark
          ? []
          : [
              BoxShadow(
                color: Colors.black.withOpacity(0.04),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
    );
  }
}
