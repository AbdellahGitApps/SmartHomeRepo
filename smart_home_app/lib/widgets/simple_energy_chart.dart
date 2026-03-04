import 'package:flutter/material.dart';

class SimpleEnergyChart extends StatefulWidget {
  const SimpleEnergyChart({super.key});

  @override
  State<SimpleEnergyChart> createState() => _SimpleEnergyChartState();
}

class _SimpleEnergyChartState extends State<SimpleEnergyChart>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  final List<double> values = [0.4, 0.7, 0.5, 0.9, 0.6, 0.8, 0.3];
  final List<String> days = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];

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
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return SizedBox(
      height: 200,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: List.generate(values.length, (index) {
          // Stagger each bar's animation
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

          return AnimatedBuilder(
            animation: barAnimation,
            builder: (context, child) {
              return Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Container(
                    width: 28,
                    height: 150 * values[index] * barAnimation.value,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          Theme.of(context).primaryColor,
                          Theme.of(context).primaryColor.withOpacity(0.6),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(10),
                      ),
                      boxShadow: isDark
                          ? [
                              BoxShadow(
                                color: Theme.of(context).primaryColor
                                    .withOpacity(0.3 * barAnimation.value),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ]
                          : [],
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    days[index],
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              );
            },
          );
        }),
      ),
    );
  }
}
