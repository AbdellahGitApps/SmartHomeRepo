import 'package:flutter/material.dart';
import '../models/device_model.dart';

class DeviceCard extends StatefulWidget {
  final DeviceModel device;
  final String localizedTitle;
  final String localizedStatus;
  final VoidCallback onTap;

  const DeviceCard({
    super.key,
    required this.device,
    required this.localizedTitle,
    required this.localizedStatus,
    required this.onTap,
  });

  @override
  State<DeviceCard> createState() => _DeviceCardState();
}

class _DeviceCardState extends State<DeviceCard>
    with SingleTickerProviderStateMixin {
  double _scale = 1.0;

  void _onTapDown(TapDownDetails details) {
    setState(() => _scale = 0.95);
  }

  void _onTapUp(TapUpDetails details) {
    setState(() => _scale = 1.0);
    widget.onTap();
  }

  void _onTapCancel() {
    setState(() => _scale = 1.0);
  }

  @override
  Widget build(BuildContext context) {
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return GestureDetector(
      onTapDown: _onTapDown,
      onTapUp: _onTapUp,
      onTapCancel: _onTapCancel,
      child: AnimatedScale(
        scale: _scale,
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeInOut,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeInOut,
          decoration: BoxDecoration(
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
                      color: widget.device.isActive
                          ? Theme.of(context).primaryColor.withOpacity(0.15)
                          : Colors.black.withOpacity(0.04),
                      blurRadius: widget.device.isActive ? 20 : 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
          ),
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 400),
                    curve: Curves.easeInOut,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: widget.device.isActive
                          ? Theme.of(context).primaryColor.withOpacity(0.2)
                          : (isDark
                                ? const Color(0xFF334155)
                                : Colors.grey[100]),
                      shape: BoxShape.circle,
                    ),
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 300),
                      transitionBuilder: (child, animation) {
                        return ScaleTransition(scale: animation, child: child);
                      },
                      child: Icon(
                        widget.device.icon,
                        key: ValueKey(widget.device.isActive),
                        color: widget.device.isActive
                            ? Theme.of(context).primaryColor
                            : Theme.of(context).iconTheme.color,
                      ),
                    ),
                  ),
                  // Animated status indicator with pulsing glow
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 500),
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: widget.device.isActive
                          ? Colors.green
                          : Colors.grey,
                      boxShadow: widget.device.isActive
                          ? [
                              BoxShadow(
                                color: Colors.green.withOpacity(0.5),
                                blurRadius: 8,
                                spreadRadius: 2,
                              ),
                            ]
                          : [],
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.localizedTitle,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.localizedStatus,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
