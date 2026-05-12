import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
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
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
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
            // Tab 1: Real-Time + Chart
            _buildRealTimeTab(context, l10n, isDark),
            // Tab 2: Reports
            _buildReportsTab(context, l10n, isDark),
            // Tab 3: Predictions
            _buildPredictionsTab(context, l10n, isDark),
          ],
        ),
      ),
    );
  }

  Widget _buildRealTimeTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Real-time sensor details
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
                          '220.5',
                          l10n.volts,
                          LucideIcons.activity,
                          Colors.blue,
                          isDark,
                        ),
                        _buildSensorGauge(
                          context,
                          l10n.current,
                          '10.9',
                          l10n.amps,
                          LucideIcons.zap,
                          Colors.orange,
                          isDark,
                        ),
                        _buildSensorGauge(
                          context,
                          l10n.power,
                          '2403',
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

          // Current kW
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
                      tween: Tween(begin: 0, end: 2.4),
                      duration: const Duration(milliseconds: 1200),
                      curve: Curves.easeOutCubic,
                      builder: (context, value, child) {
                        return Text(
                          '${value.toStringAsFixed(1)} ${l10n.kW}',
                          style: Theme.of(context).textTheme.displayLarge!
                              .copyWith(color: Theme.of(context).primaryColor),
                        );
                      },
                    ),
                    const SizedBox(height: 8),
                    Text(
                      l10n.statusNormal,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 32),

          // Weekly chart
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
                child: const SimpleEnergyChart(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReportsTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    final reports = [
      {'period': l10n.daily, 'total': '8.2', 'avg': '0.34', 'peak': '1.8'},
      {'period': l10n.weekly, 'total': '56.4', 'avg': '2.35', 'peak': '3.1'},
      {'period': l10n.monthly, 'total': '235.7', 'avg': '7.86', 'peak': '4.2'},
    ];

    return ListView.separated(
      padding: const EdgeInsets.all(24),
      itemCount: reports.length,
      separatorBuilder: (_, __) => const SizedBox(height: 16),
      itemBuilder: (context, index) {
        final r = reports[index];
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
    );
  }

  Widget _buildPredictionsTab(
    BuildContext context,
    AppLocalizations l10n,
    bool isDark,
  ) {
    final predictions = [
      {'period': l10n.nextDay, 'value': '9.1', 'icon': LucideIcons.clock},
      {'period': l10n.nextWeek, 'value': '61.3', 'icon': LucideIcons.calendar},
      {
        'period': l10n.nextMonth,
        'value': '248.5',
        'icon': LucideIcons.calendarDays,
      },
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
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
                Icon(LucideIcons.brain, color: Theme.of(context).primaryColor),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    l10n.basedOnHistory,
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
                        color: Theme.of(context).primaryColor.withOpacity(0.15),
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
                        ],
                      ),
                    ),
                    TweenAnimationBuilder<double>(
                      tween: Tween(
                        begin: 0,
                        end: double.parse(p['value'] as String),
                      ),
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
          tween: Tween(begin: 0, end: double.parse(value)),
          duration: const Duration(milliseconds: 1200),
          curve: Curves.easeOutCubic,
          builder: (context, v, _) {
            return Text(
              v.toStringAsFixed(1),
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
