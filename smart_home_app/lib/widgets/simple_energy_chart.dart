import 'package:flutter/material.dart';

class SimpleEnergyChart extends StatefulWidget {
  const SimpleEnergyChart({super.key, this.values, this.labels});

  final List<double>? values;
  final List<String>? labels;

  @override
  State<SimpleEnergyChart> createState() => _SimpleEnergyChartState();
}

class _SimpleEnergyChartState extends State<SimpleEnergyChart>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  static const List<double> _fallbackValues = [
    0.4,
    0.7,
    0.5,
    0.9,
    0.6,
    0.8,
    0.3,
  ];
  static const List<String> _fallbackLabels = [
    'Mo',
    'Tu',
    'We',
    'Th',
    'Fr',
    'Sa',
    'Su',
  ];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );
    _controller.forward();
  }

  @override
  void didUpdateWidget(covariant SimpleEnergyChart oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.values != widget.values ||
        oldWidget.labels != widget.labels) {
      _controller
        ..reset()
        ..forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  List<double> get _values {
    final incoming = widget.values;
    if (incoming == null || incoming.isEmpty) return _fallbackValues;
    return incoming.map((v) => v <= 0 ? 0.05 : v).toList();
  }

  List<String> get _labels {
    final incoming = widget.labels;
    if (incoming == null || incoming.isEmpty) return _fallbackLabels;
    return incoming;
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final values = _values;
    final labels = _labels;
    final maxValue = values.reduce((a, b) => a > b ? a : b);
    final safeMax = maxValue <= 0 ? 1.0 : maxValue;

    return LayoutBuilder(
      builder: (context, constraints) {
        final isCompact = constraints.maxWidth < 390;
        final barWidth = isCompact ? 22.0 : 24.0;
        final valueFontSize = isCompact ? 10.2 : 11.5;
        final labelFontSize = isCompact ? 12.0 : 13.0;
        final chartHeight = isCompact ? 190.0 : 200.0;
        final maxBarHeight = isCompact ? 126.0 : 142.0;

        return SizedBox(
          height: chartHeight,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: List.generate(values.length, (index) {
              final begin = index / (values.length + 2);
              final end = (index + 3) / (values.length + 2);
              final barAnimation = Tween<double>(begin: 0, end: 1).animate(
                CurvedAnimation(
                  parent: _controller,
                  curve: Interval(
                    begin.clamp(0.0, 1.0),
                    end.clamp(0.0, 1.0),
                    curve: Curves.easeOutCubic,
                  ),
                ),
              );

              final normalizedHeight = (values[index] / safeMax).clamp(
                0.05,
                1.0,
              );
              final label = index < labels.length ? labels[index] : '';

              return Expanded(
                child: Padding(
                  padding: EdgeInsets.symmetric(
                    horizontal: isCompact ? 1.0 : 2.0,
                  ),
                  child: AnimatedBuilder(
                    animation: barAnimation,
                    builder: (context, child) {
                      return Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          SizedBox(
                            height: 18,
                            child: FittedBox(
                              fit: BoxFit.scaleDown,
                              child: Text(
                                '${values[index].toStringAsFixed(1)} kWh',
                                maxLines: 1,
                                softWrap: false,
                                style: Theme.of(context).textTheme.bodySmall
                                    ?.copyWith(
                                      fontSize: valueFontSize,
                                      fontWeight: FontWeight.w600,
                                    ),
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Container(
                            width: barWidth,
                            height:
                                maxBarHeight *
                                normalizedHeight *
                                barAnimation.value,
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  Theme.of(context).primaryColor,
                                  Theme.of(
                                    context,
                                  ).primaryColor.withValues(alpha: 0.6),
                                ],
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                              ),
                              borderRadius: const BorderRadius.vertical(
                                top: Radius.circular(9),
                              ),
                              boxShadow: isDark
                                  ? [
                                      BoxShadow(
                                        color: Theme.of(context).primaryColor
                                            .withValues(alpha: 
                                              0.3 * barAnimation.value,
                                            ),
                                        blurRadius: 12,
                                        offset: const Offset(0, 4),
                                      ),
                                    ]
                                  : [],
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            label,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context).textTheme.bodyMedium
                                ?.copyWith(fontSize: labelFontSize),
                          ),
                        ],
                      );
                    },
                  ),
                ),
              );
            }),
          ),
        );
      },
    );
  }
}
