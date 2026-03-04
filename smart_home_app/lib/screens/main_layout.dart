import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../l10n/app_localizations.dart';
import 'home_dashboard.dart';
import 'doors_screen.dart';
import 'energy_screen.dart';
import 'alerts_screen.dart';
import 'camera_screen.dart';
import 'profile_screen.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const HomeDashboard(),
    const DoorsScreen(),
    const EnergyScreen(),
    const AlertsScreen(),
    const CameraScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 350),
        switchInCurve: Curves.easeOut,
        switchOutCurve: Curves.easeIn,
        transitionBuilder: (child, animation) {
          return FadeTransition(opacity: animation, child: child);
        },
        child: KeyedSubtree(
          key: ValueKey<int>(_currentIndex),
          child: _screens[_currentIndex],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: [
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.home),
            label: l10n.home,
          ),
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.doorClosed),
            label: l10n.doors,
          ),
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.zap),
            label: l10n.energy,
          ),
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.bellRing),
            label: l10n.alerts,
          ),
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.camera),
            label: l10n.camera,
          ),
          BottomNavigationBarItem(
            icon: const Icon(LucideIcons.user),
            label: l10n.settings,
          ),
        ],
      ),
    );
  }
}
