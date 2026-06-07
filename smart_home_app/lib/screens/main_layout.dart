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

  // Cache screens to avoid recreating them on every build
  late final Widget _homeDashboard;
  late final Widget _doorsScreen;
  late final Widget _energyScreen;
  late final Widget _alertsScreen;
  late final Widget _cameraScreen;
  late final Widget _familyScreen;
  late final Widget _profileScreen;

  @override
  void initState() {
    super.initState();
    _homeDashboard = const HomeDashboard();
    _doorsScreen = const DoorsScreen();
    _energyScreen = const EnergyScreen();
    _alertsScreen = const AlertsScreen();
    _cameraScreen = const CameraScreen();
    _familyScreen = const FamilyScreen();
    _profileScreen = const ProfileScreen();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    
    // Select only the properties we care about to prevent unnecessary rebuilds
    final canViewDoors = context.select<AppStateProvider, bool>((p) => p.canViewDoors);
    final canViewFamily = context.select<AppStateProvider, bool>((p) => p.canViewFamily);

    final screens = <Widget>[
      _homeDashboard,
      if (canViewDoors) _doorsScreen,
      _energyScreen,
      _alertsScreen,
      _cameraScreen,
      if (canViewFamily) _familyScreen,
      _profileScreen,
    ];

    final items = <BottomNavigationBarItem>[
      BottomNavigationBarItem(
        icon: const Icon(LucideIcons.home, size: 20),
        label: l10n.home,
      ),
      if (canViewDoors)
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
      if (canViewFamily)
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
