import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import 'home_dashboard.dart';
import 'doors_screen.dart';
import 'energy_screen.dart';
import 'alerts_screen.dart';
import 'camera_screen.dart';
import 'family_screen.dart';
import 'profile_screen.dart';

class MainLayout extends StatefulWidget {
  const MainLayout({super.key});

  @override
  State<MainLayout> createState() => _MainLayoutState();
}

class _MainLayoutState extends State<MainLayout> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);

    final screens = <Widget>[
      const HomeDashboard(),
      if (appState.canViewDoors) const DoorsScreen(),
      const EnergyScreen(),
      const AlertsScreen(),
      const CameraScreen(),
      if (appState.canViewFamily) const FamilyScreen(),
      const ProfileScreen(),
    ];

    final items = <BottomNavigationBarItem>[
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.home, size: 20),
        label: l10n.home,
      ),
      if (appState.canViewDoors)
        BottomNavigationBarItem(
          icon: const Icon(LucideIcons.doorClosed, size: 20),
          label: l10n.doors,
        ),
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.zap, size: 20),
        label: l10n.energy,
      ),
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.bellRing, size: 20),
        label: l10n.alerts,
      ),
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.camera, size: 20),
        label: l10n.camera,
      ),
      if (appState.canViewFamily)
        BottomNavigationBarItem(
          icon: const Icon(LucideIcons.users, size: 20),
          label: l10n.family,
        ),
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.user, size: 20),
        label: l10n.settings,
      ),
    ];

    if (_currentIndex >= screens.length) {
      _currentIndex = 0;
    }

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
          child: screens[_currentIndex],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        currentIndex: _currentIndex,
        selectedFontSize: 10,
        unselectedFontSize: 10,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        items: items,
      ),
    );
  }
}
