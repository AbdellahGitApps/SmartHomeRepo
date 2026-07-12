import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import 'login_screen.dart';

/// Welcome screen shown after the splash to let users choose between
/// "I'm New" (first-time registration) and "I Already Have an Account" (login).
class WelcomeScreen extends StatefulWidget {
  const WelcomeScreen({super.key});

  @override
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimationTop;
  late Animation<Offset> _slideAnimationBottom;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1000),
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.6, curve: Curves.easeOut),
      ),
    );

    _slideAnimationTop = Tween<Offset>(
      begin: const Offset(0, -0.15),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.0, 0.7, curve: Curves.easeOutCubic),
      ),
    );

    _slideAnimationBottom = Tween<Offset>(
      begin: const Offset(0, 0.25),
      end: Offset.zero,
    ).animate(
      CurvedAnimation(
        parent: _controller,
        curve: const Interval(0.2, 0.9, curve: Curves.easeOutCubic),
      ),
    );

    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _navigateToLogin({required bool isNewUser}) {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        transitionDuration: const Duration(milliseconds: 500),
        pageBuilder: (context, animation, secondaryAnimation) {
          return FadeTransition(
            opacity: animation,
            child: LoginScreen(initialMode: isNewUser ? LoginMode.newUser : LoginMode.existingUser),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context);
    final isDark = appState.themeMode == ThemeMode.dark;
    final l10n = AppLocalizations.of(context)!;

    const gold = Color(0xFFF2BE2E);
    final cardColor = isDark ? const Color(0xFF0F172A) : Colors.white;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF1E293B) : const Color(0xFFF8FAFC),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        actions: [
          IconButton(
            icon: Icon(isDark ? LucideIcons.sun : LucideIcons.moon,
                color: isDark ? Colors.white70 : Colors.grey),
            onPressed: () => appState.toggleTheme(!isDark),
          ),
          TextButton(
            onPressed: () {
              appState.switchLanguage(
                  appState.locale.languageCode == 'en' ? 'ar' : 'en');
            },
            child: Text(
              appState.locale.languageCode.toUpperCase(),
              style: TextStyle(
                color: isDark ? Colors.white70 : Colors.grey,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
            child: Column(
              children: [
                // ─── Header with logo and tagline ───
                SlideTransition(
                  position: _slideAnimationTop,
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: Column(
                      children: [
                        // Logo icon with gold glow
                        Container(
                          width: 110,
                          height: 110,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: gold,
                            boxShadow: [
                              BoxShadow(
                                color: gold.withValues(alpha: 0.30),
                                blurRadius: 28,
                                spreadRadius: 2,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: const Icon(
                            LucideIcons.shieldCheck,
                            color: Colors.white,
                            size: 46,
                          ),
                        ),
                        const SizedBox(height: 22),
                        Text(
                          l10n.smartHome,
                          style: const TextStyle(
                            color: gold,
                            fontSize: 31,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.4,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          l10n.appTagline,
                          style: const TextStyle(
                            color: Colors.grey,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            letterSpacing: 1.6,
                          ),
                        ),
                        const SizedBox(height: 36),
                        Text(
                          l10n.welcomeChooseOption,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: isDark ? Colors.white70 : Colors.black54,
                            fontSize: 15,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 32),
                // ─── Option cards ───
                SlideTransition(
                  position: _slideAnimationBottom,
                  child: FadeTransition(
                    opacity: _fadeAnimation,
                    child: Column(
                      children: [
                        // "I'm New" card
                        _WelcomeOptionCard(
                          icon: LucideIcons.userPlus,
                          title: l10n.welcomeImNew,
                          subtitle: l10n.welcomeImNewSubtitle,
                          cardColor: cardColor,
                          isDark: isDark,
                          onTap: () => _navigateToLogin(isNewUser: true),
                        ),
                        const SizedBox(height: 16),
                        // "I Already Have an Account" card
                        _WelcomeOptionCard(
                          icon: LucideIcons.logIn,
                          title: l10n.welcomeHaveAccount,
                          subtitle: l10n.welcomeHaveAccountSubtitle,
                          cardColor: cardColor,
                          isDark: isDark,
                          onTap: () => _navigateToLogin(isNewUser: false),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// A reusable card widget for each welcome option.
class _WelcomeOptionCard extends StatefulWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color cardColor;
  final bool isDark;
  final VoidCallback onTap;

  const _WelcomeOptionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.cardColor,
    required this.isDark,
    required this.onTap,
  });

  @override
  State<_WelcomeOptionCard> createState() => _WelcomeOptionCardState();
}

class _WelcomeOptionCardState extends State<_WelcomeOptionCard> {
  bool _isPressed = false;

  @override
  Widget build(BuildContext context) {
    const gold = Color(0xFFF2BE2E);

    return GestureDetector(
      onTapDown: (_) => setState(() => _isPressed = true),
      onTapUp: (_) {
        setState(() => _isPressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _isPressed = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOut,
        transform: Matrix4.diagonal3Values(
          _isPressed ? 0.97 : 1.0,
          _isPressed ? 0.97 : 1.0,
          1.0,
        ),
          width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: widget.cardColor,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(
            color: _isPressed
                ? gold.withValues(alpha: 0.6)
                : (widget.isDark ? Colors.white10 : Colors.black.withValues(alpha: 0.06)),
            width: _isPressed ? 2 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: _isPressed
                  ? gold.withValues(alpha: 0.12)
                  : Colors.black.withValues(alpha: 0.05),
              blurRadius: _isPressed ? 18 : 14,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 52,
              height: 52,
              decoration: BoxDecoration(
                color: gold.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(widget.icon, color: gold, size: 26),
            ),
            const SizedBox(width: 18),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.title,
                    style: TextStyle(
                      color: widget.isDark ? Colors.white : Colors.black87,
                      fontSize: 17,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.subtitle,
                    style: TextStyle(
                      color: widget.isDark ? Colors.white54 : Colors.black45,
                      fontSize: 13,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              LucideIcons.chevronRight,
              color: widget.isDark ? Colors.white30 : Colors.black26,
              size: 22,
            ),
          ],
        ),
      ),
    );
  }
}
