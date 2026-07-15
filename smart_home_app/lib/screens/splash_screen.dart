import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';
import 'dart:async';

import '../providers/app_state_provider.dart';
import 'main_layout.dart';
import 'welcome_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late AnimationController _mainController;
  late AnimationController _pulseController;
  
  late Animation<double> _glowExpandAnim;
  late Animation<double> _textFadeAnim;
  late Animation<double> _textScaleAnim;

  @override
  void initState() {
    super.initState();

    _mainController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3200),
    );

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    );

    // Initial ambient glow expansion
    _glowExpandAnim = CurvedAnimation(
      parent: _mainController,
      curve: const Interval(0.1, 0.7, curve: Curves.easeOutCubic),
    );

    // Text gracefully fades in
    _textFadeAnim = CurvedAnimation(
      parent: _mainController,
      curve: const Interval(0.3, 0.8, curve: Curves.easeIn),
    );

    // Text scales up very gently for a cinematic feel
    _textScaleAnim = Tween<double>(begin: 0.9, end: 1.0).animate(
      CurvedAnimation(
        parent: _mainController,
        curve: const Interval(0.3, 1.0, curve: Curves.easeOutCubic),
      ),
    );

    _mainController.forward();
    _pulseController.repeat(reverse: true);
    
    _navigateToNext();
  }

  Future<void> _navigateToNext() async {
    // Wait for the full animation to breathe, then transition
    await Future.delayed(const Duration(milliseconds: 4000));
    if (!mounted) return;
    
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        transitionDuration: const Duration(milliseconds: 800),
        pageBuilder: (context, animation, secondaryAnimation) {
          return FadeTransition(
            opacity: animation,
            child: appState.isLoggedIn ? const MainLayout() : const WelcomeScreen(),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    _mainController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F1A2C), // Perfect match with native splash
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Hardware-accelerated ambient glowing background
          AnimatedBuilder(
            animation: Listenable.merge([_mainController, _pulseController]),
            builder: (context, child) {
              return Center(
                child: Container(
                  width: 300,
                  height: 300,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: const Color(0xFF00E5FF).withOpacity(
                          (_glowExpandAnim.value * 0.15) + (_pulseController.value * 0.05),
                        ),
                        blurRadius: 100,
                        spreadRadius: 60 * _glowExpandAnim.value,
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
          
          // Hardware-accelerated typography reveal
          Center(
            child: AnimatedBuilder(
              animation: _mainController,
              builder: (context, child) {
                return Transform.scale(
                  scale: _textScaleAnim.value,
                  child: Opacity(
                    opacity: _textFadeAnim.value,
                    child: Text(
                      'Edge',
                      style: GoogleFonts.montserrat(
                        fontSize: 56,
                        fontWeight: FontWeight.w300, // Elegant lightweight font
                        letterSpacing: 16.0,
                        color: Colors.white,
                        shadows: [
                          Shadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.8),
                            blurRadius: 20,
                          ),
                          Shadow(
                            color: const Color(0xFF00E5FF).withOpacity(0.4),
                            blurRadius: 40,
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
