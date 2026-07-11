import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
import '../services/backend_api_service.dart';
import '../utils/date_formatter.dart';
import '../providers/app_state_provider.dart';
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

  // Home-change detection
  String? _lastHomeId;
  bool _homeIdInitialized = false;

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
  void didChangeDependencies() {
    super.didChangeDependencies();

    // Subscribe to AppStateProvider to detect home switches.
    // Provider.of with listen:true registers this widget as a dependent.
    final appState = Provider.of<AppStateProvider>(context);
    final currentHomeId =
        appState.homeDbId.isNotEmpty ? appState.homeDbId : appState.homeId;

    if (!_homeIdInitialized) {
      // First call (right after initState). initState already called
      // _loadEnergyData(), so just record the current homeId.
      _homeIdInitialized = true;
      _lastHomeId = currentHomeId;
      return;
    }

    if (currentHomeId != _lastHomeId) {
      _lastHomeId = currentHomeId;
      // Reload in the next frame so we don't call setState mid-build.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _loadEnergyData();
      });
    }
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
      // Always read homeId fresh at call time so we use the current home,
      // not whatever was cached when the widget was first built.
      final appState = Provider.of<AppStateProvider>(context, listen: false);
      final homeId =
          appState.homeDbId.isNotEmpty ? appState.homeDbId : appState.homeId;

      final latestRes = await _api.getEnergyLatest();
      final logsRes = await _api.getEnergyLogs();
      var forecastRes = await _api.getEnergyForecastLatest(homeId: homeId);

      if (!mounted) return;

      final latestData = latestRes['latest'] as Map<String, dynamic>?;
      final logsData = (logsRes['logs'] as List?)?.cast<Map<String, dynamic>>() ?? [];
      var forecastData = (forecastRes['forecasts'] as List?)?.cast<Map<String, dynamic>>() ?? [];

      if (forecastData.isEmpty && latestData != null) {
        try {
          final runRes = await _api.runEnergyForecast(homeId: homeId);
          if (runRes['success'] == true) {
            final newForecastRes = await _api.getEnergyForecastLatest(homeId: homeId);
            forecastData = (newForecastRes['forecasts'] as List?)?.cast<Map<String, dynamic>>() ?? [];
          }
        } catch (e) {
          // Keep empty if forecast run fails (e.g. not enough data)
        }
      }

      if (latestData == null) {
        setState(() {
          _latestEnergy = null;
          _energyLogs = [];
          _forecasts = [];
          _isLoadingEnergy = false;
        });
        return;
      }

      setState(() {
        _latestEnergy = latestData;
        _energyLogs = logsData;
        _forecasts = forecastData;
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

  int _predictionRisk(double predicted, double baseline) {
    if (baseline <= 0) return 0;

    final ratio = predicted / baseline;

    if (ratio > 1.8) return 3;
    if (ratio > 1.5) return 2;
    if (ratio > 1.3) return 1;

    return 0;
  }

  String _predictionWarning(double predicted, double baseline, String period) {
    final risk = _predictionRisk(predicted, baseline);

    if (risk == 0) return 'Normal expected usage';
    if (risk == 1) return 'Slightly higher than usual';
    if (risk == 2) return 'High usage expected';

    return 'Critical usage warning';
  }

  String _formatEnergyClock(dynamic value) {
    return DateFormatter.formatTimeOnly(value?.toString());
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
      return const [];
    }

    return logs.map((item) {
      final kwh = _num(item['kwh_today'], _num(item['consumption_kwh']));
      if (kwh > 0) return kwh;

      final watts = _num(item['watts']);
      return watts > 0 ? watts / 1000.0 : 0.1;
    }).toList();
  }

  List<String> get _chartLabels {
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    final count = _chartValues.length;

    if (count <= 0) {
      return labels;
    }

    if (count >= labels.length) {
      return labels;
    }

    return labels.sublist(labels.length - count);
  }

  String get _latestTimestamp {
    return _formatEnergyClock(_latestEnergy?['timestamp']);
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
              tooltip: 'Refresh',
              onPressed: _isLoadingEnergy ? null : _loadEnergyData,
              icon: _isLoadingEnergy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh, size: 20),
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

    if (_latestEnergy == null) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(14),
        decoration: _cardDecoration(context, isDark),
        child: Text(
          'No energy readings available',
          style: Theme.of(context).textTheme.bodyMedium,
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
                            ? 'No energy readings available'
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
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final compact = constraints.maxWidth < 430;

                    if (_latestEnergy == null || _energyLogs.isEmpty) {
                      return Container(
                        height: 300,
                        padding: EdgeInsets.all(compact ? 8 : 24),
                        decoration: _cardDecoration(context, isDark),
                        alignment: Alignment.center,
                        child: Text(
                          'No energy readings available',
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                      );
                    }

                    return Container(
                      height: 300,
                      padding: EdgeInsets.all(compact ? 8 : 24),
                      decoration: _cardDecoration(context, isDark),
                      child: SimpleEnergyChart(
                        values: _chartValues,
                        labels: _chartLabels,
                      ),
                    );
                  },
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

    final weeklyAverageKwh = _energyLogs.isEmpty
        ? 0.0
        : logsTotal / _energyLogs.length;

    final weeklyPeakKwh = _energyLogs.fold<double>(0, (max, item) {
      final kwh = _num(item['kwh_today'], _num(item['consumption_kwh']));
      return kwh > max ? kwh : max;
    });

    final monthlyTotalKwh = weeklyAverageKwh * 30.0;

    final reports = <Map<String, String>>[
      {
        'period': l10n.daily,
        'total': _fmt(_latestKwh),
        'avg': _fmt(_latestKw),
        'avgUnit': l10n.kW,
        'peak': _fmt(_latestKw),
        'peakUnit': l10n.kW,
      },
      {
        'period': l10n.weekly,
        'total': _fmt(logsTotal),
        'avg': _fmt(weeklyAverageKwh),
        'avgUnit': '${l10n.kWh}/day',
        'peak': _fmt(weeklyPeakKwh),
        'peakUnit': '${l10n.kWh}/day',
      },
      {
        'period': l10n.monthly,
        'total': _fmt(monthlyTotalKwh),
        'avg': _fmt(weeklyAverageKwh),
        'avgUnit': '${l10n.kWh}/day',
        'peak': _fmt(weeklyPeakKwh),
        'peakUnit': '${l10n.kWh}/day',
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
                      '${r['avg']} ${r['avgUnit']}',
                      LucideIcons.trendingUp,
                      isDark,
                    ),
                    const SizedBox(width: 16),
                    _buildReportStat(
                      context,
                      l10n.peakUsage,
                      '${r['peak']} ${r['peakUnit']}',
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
    final sorted = List<Map<String, dynamic>>.from(_forecasts);
    sorted.sort((a, b) => (a['forecast_date'] as String? ?? '').compareTo(b['forecast_date'] as String? ?? ''));

    final week1 = sorted.isNotEmpty ? _num(sorted[0]['predicted_kwh']) : 0.0;
    final week2 = sorted.length > 1 ? _num(sorted[1]['predicted_kwh']) : 0.0;
    
    final firstItem = sorted.isNotEmpty ? sorted[0] : <String, dynamic>{};
    final monthlyTotal = (firstItem.containsKey('predicted_month_total_kwh') && firstItem['predicted_month_total_kwh'] != null)
        ? _num(firstItem['predicted_month_total_kwh'])
        : sorted.fold<double>(0.0, (sum, item) => sum + _num(item['predicted_kwh']));

    final predictions = [
      {
        'period': l10n.nextWeek,
        'value': week1,
        'icon': LucideIcons.calendar,
        'comparison': _predictionWarning(week1, 0.0, 'week'),
        'isIncrease': _predictionRisk(week1, 0.0) > 0,
      },
      if (sorted.length > 1)
        {
          'period': Localizations.localeOf(context).languageCode == 'ar' ? 'الأسبوع الذي يليه' : 'Following Week',
          'value': week2,
          'icon': LucideIcons.calendar,
          'comparison': _predictionWarning(week2, 0.0, 'week'),
          'isIncrease': _predictionRisk(week2, 0.0) > 0,
        },
      {
        'period': l10n.nextMonth,
        'value': monthlyTotal,
        'icon': LucideIcons.calendarDays,
        'comparison': _predictionWarning(
          monthlyTotal,
          0.0,
          'month',
        ),
        'isIncrease': _predictionRisk(monthlyTotal, 0.0) > 0,
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
                          : 'AI Model Forecast (HistGBR)',
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
                child: LayoutBuilder(
                  builder: (context, constraints) {
                    final compact = constraints.maxWidth < 430;

                    return Container(
                      padding: EdgeInsets.all(compact ? 18 : 24),
                      decoration: _cardDecoration(context, isDark),
                      child: Row(
                        children: [
                          Container(
                            padding: EdgeInsets.all(compact ? 11 : 14),
                            decoration: BoxDecoration(
                              color: Theme.of(
                                context,
                              ).primaryColor.withOpacity(0.15),
                              shape: BoxShape.circle,
                            ),
                            child: Icon(
                              p['icon'] as IconData,
                              color: Theme.of(context).primaryColor,
                              size: compact ? 21 : 24,
                            ),
                          ),
                          SizedBox(width: compact ? 12 : 18),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  p['period'] as String,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.titleLarge,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  l10n.predictedUsage,
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context).textTheme.bodyMedium,
                                ),
                                const SizedBox(height: 8),
                                Transform.translate(
                                  offset: Offset(compact ? -18 : -8, 0),
                                  child: Row(
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
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: TextStyle(
                                            fontSize: compact ? 11.5 : 12,
                                            color: (p['isIncrease'] as bool)
                                                ? Colors.red
                                                : Colors.green,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          SizedBox(width: compact ? 14 : 24),
                          Transform.translate(
                            offset: Offset(compact ? 18 : 8, 0),
                            child: SizedBox(
                              width: compact ? 128 : 160,
                              child: TweenAnimationBuilder<double>(
                                tween: Tween(
                                  begin: 0,
                                  end: p['value'] as double,
                                ),
                                duration: const Duration(milliseconds: 1200),
                                curve: Curves.easeOutCubic,
                                builder: (context, value, _) {
                                  return FittedBox(
                                    fit: BoxFit.scaleDown,
                                    alignment: Alignment.centerRight,
                                    child: Text(
                                      '${value.toStringAsFixed(1)} ${l10n.kWh}',
                                      maxLines: 1,
                                      softWrap: false,
                                      textAlign: TextAlign.right,
                                      style: Theme.of(context)
                                          .textTheme
                                          .headlineSmall!
                                          .copyWith(
                                            color: Theme.of(
                                              context,
                                            ).primaryColor,
                                            fontWeight: FontWeight.bold,
                                          ),
                                    ),
                                  );
                                },
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
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
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 105;

          return Column(
            children: [
              Icon(
                icon,
                size: compact ? 16 : 18,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 6),
              FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  value,
                  maxLines: 1,
                  style: Theme.of(context).textTheme.titleMedium!.copyWith(
                    fontWeight: FontWeight.bold,
                    fontSize: compact ? 14 : null,
                  ),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                label,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(
                  context,
                ).textTheme.bodySmall?.copyWith(fontSize: compact ? 11 : null),
                textAlign: TextAlign.center,
              ),
            ],
          );
        },
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
