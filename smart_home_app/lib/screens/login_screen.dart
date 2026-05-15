import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../l10n/app_localizations.dart';
import 'package:lucide_icons/lucide_icons.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with TickerProviderStateMixin {
  // ── Animation controllers ──
  late AnimationController _entryController;
  late AnimationController _pulseController;
  late Animation<double> _logoFade;
  late Animation<Offset> _formSlide;
  late Animation<double> _formFade;
  late Animation<double> _pulseAnim;

  // ── Mode: 0 = Admin, 1 = User ──
  int _selectedMode = 0;

  // ── Admin sub-mode: 0 = Sign in (first login), 1 = Login ──
  int _adminSubMode = 0;

  // ── Admin Sign-In (first login) controllers ──
  final _signInUsernameOrEmailCtrl = TextEditingController();
  final _signInPasswordCtrl = TextEditingController();
  final _signInHomeCodeCtrl = TextEditingController();
  bool _obscureSignInPassword = true;

  // ── Admin Login controllers ──
  final _loginUsernameCtrl = TextEditingController();
  final _loginPasswordCtrl = TextEditingController();
  bool _obscureLoginPassword = true;

  // ── User controllers ──
  final _userPinCtrl = TextEditingController();
  bool _obscureUserPin = true;

  String? _errorMessage;

  @override
  void initState() {
    super.initState();

    _entryController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );

    _logoFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _entryController,
        curve: const Interval(0.0, 0.4, curve: Curves.easeOut),
      ),
    );
    _formSlide = Tween<Offset>(begin: const Offset(0, 0.3), end: Offset.zero)
        .animate(
          CurvedAnimation(
            parent: _entryController,
            curve: const Interval(0.3, 0.8, curve: Curves.easeOut),
          ),
        );
    _formFade = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(
        parent: _entryController,
        curve: const Interval(0.3, 0.8, curve: Curves.easeOut),
      ),
    );

    _entryController.forward();

    // Repeating pulse for header rings
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 3000),
    );
    _pulseAnim = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _pulseController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _entryController.dispose();
    _signInUsernameOrEmailCtrl.dispose();
    _signInPasswordCtrl.dispose();
    _signInHomeCodeCtrl.dispose();
    _loginUsernameCtrl.dispose();
    _loginPasswordCtrl.dispose();
    _userPinCtrl.dispose();
    super.dispose();
  }

  // ── Login logic ──
  void _attemptAdminSignIn() {
    final l10n = AppLocalizations.of(context)!;
    final usernameOrEmail = _signInUsernameOrEmailCtrl.text.trim();
    final password = _signInPasswordCtrl.text.trim();
    final homeCode = _signInHomeCodeCtrl.text.trim();
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    if ((usernameOrEmail == appState.userName || usernameOrEmail == 'admin' || usernameOrEmail == 'admin@home.com') &&
        password == appState.password &&
        homeCode == appState.homeCode) {
      setState(() => _errorMessage = null);
      appState.login(appState.userName, 'Admin');
    } else {
      setState(() => _errorMessage = l10n.loginError);
    }
  }

  void _attemptAdminLogin() {
    final l10n = AppLocalizations.of(context)!;
    final username = _loginUsernameCtrl.text.trim();
    final password = _loginPasswordCtrl.text.trim();
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    if ((username == appState.userName || username == 'admin') &&
        password == appState.password) {
      setState(() => _errorMessage = null);
      appState.login(appState.userName, 'Admin');
    } else {
      setState(() => _errorMessage = l10n.loginError);
    }
  }

  void _attemptUserLogin() {
    final l10n = AppLocalizations.of(context)!;
    final pin = _userPinCtrl.text.trim();
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    if (pin == appState.userPin) {
      setState(() => _errorMessage = null);
      appState.login('User Guest', 'User');
    } else {
      setState(() => _errorMessage = l10n.pinError);
    }
  }

  // ── Build helpers ──
  InputDecoration _inputDecoration({
    required String label,
    required IconData prefixIcon,
    Widget? suffixIcon,
  }) {
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(prefixIcon, size: 20),
      suffixIcon: suffixIcon,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    );
  }

  Widget _buildErrorMessage() {
    if (_errorMessage == null) return const SizedBox.shrink();
    return AnimatedOpacity(
      opacity: 1.0,
      duration: const Duration(milliseconds: 300),
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.red.withOpacity(0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            const Icon(LucideIcons.alertCircle, color: Colors.red, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                _errorMessage!,
                style: const TextStyle(color: Colors.red, fontSize: 13),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required String label,
    required VoidCallback onPressed,
  }) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: Theme.of(context).primaryColor,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 0,
        ),
        child: Text(
          label,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }

  // ── Admin Sign-In (First Login) form ──
  Widget _buildAdminSignInForm() {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      key: const ValueKey('admin_signin'),
      children: [
        TextField(
          controller: _signInUsernameOrEmailCtrl,
          decoration: _inputDecoration(
            label: l10n.usernameOrEmail,
            prefixIcon: LucideIcons.user,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _signInPasswordCtrl,
          obscureText: _obscureSignInPassword,
          decoration: _inputDecoration(
            label: l10n.password,
            prefixIcon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureSignInPassword ? LucideIcons.eyeOff : LucideIcons.eye,
                size: 20,
              ),
              onPressed: () => setState(
                () => _obscureSignInPassword = !_obscureSignInPassword,
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _signInHomeCodeCtrl,
          decoration: _inputDecoration(
            label: l10n.homeCode,
            prefixIcon: LucideIcons.home,
          ),
          onSubmitted: (_) => _attemptAdminSignIn(),
        ),
        const SizedBox(height: 20),
        _buildErrorMessage(),
        _buildActionButton(
          label: l10n.signInFirstLogin,
          onPressed: _attemptAdminSignIn,
        ),
      ],
    );
  }

  // ── Admin Login form ──
  Widget _buildAdminLoginForm() {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      key: const ValueKey('admin_login'),
      children: [
        TextField(
          controller: _loginUsernameCtrl,
          decoration: _inputDecoration(
            label: l10n.username,
            prefixIcon: LucideIcons.user,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _loginPasswordCtrl,
          obscureText: _obscureLoginPassword,
          decoration: _inputDecoration(
            label: l10n.password,
            prefixIcon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureLoginPassword ? LucideIcons.eyeOff : LucideIcons.eye,
                size: 20,
              ),
              onPressed: () => setState(
                () => _obscureLoginPassword = !_obscureLoginPassword,
              ),
            ),
          ),
          onSubmitted: (_) => _attemptAdminLogin(),
        ),
        const SizedBox(height: 20),
        _buildErrorMessage(),
        _buildActionButton(
          label: l10n.loginButton,
          onPressed: _attemptAdminLogin,
        ),
      ],
    );
  }

  // ── User PIN form ──
  Widget _buildUserForm() {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      key: const ValueKey('user_form'),
      children: [
        TextField(
          controller: _userPinCtrl,
          obscureText: _obscureUserPin,
          decoration: _inputDecoration(
            label: l10n.userPinOrPassword,
            prefixIcon: LucideIcons.keyRound,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureUserPin ? LucideIcons.eyeOff : LucideIcons.eye,
                size: 20,
              ),
              onPressed: () =>
                  setState(() => _obscureUserPin = !_obscureUserPin),
            ),
          ),
          onSubmitted: (_) => _attemptUserLogin(),
        ),
        const SizedBox(height: 20),
        _buildErrorMessage(),
        _buildActionButton(
          label: l10n.enterAsUser,
          onPressed: _attemptUserLogin,
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // ── Header Icon ──
                FadeTransition(
                  opacity: _logoFade,
                  child: Column(
                    children: [
                      // Layered glowing rings + icon (animated)
                      AnimatedBuilder(
                        animation: _pulseAnim,
                        builder: (context, child) {
                          final p = _pulseAnim.value;
                          return SizedBox(
                            width: 160,
                            height: 160,
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                // Outer glow ring — pulsing scale
                                Transform.scale(
                                  scale: 1.0 + (p * 0.15),
                                  child: Opacity(
                                    opacity: 0.10 + (1.0 - p) * 0.30,
                                    child: Container(
                                      width: 150,
                                      height: 150,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        border: Border.all(
                                          color: Theme.of(context).primaryColor,
                                          width: 2,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                                // Middle ring — counter-pulse
                                Transform.scale(
                                  scale: 1.0 + ((1.0 - p) * 0.10),
                                  child: Opacity(
                                    opacity: 0.15 + p * 0.25,
                                    child: Container(
                                      width: 115,
                                      height: 115,
                                      decoration: BoxDecoration(
                                        shape: BoxShape.circle,
                                        border: Border.all(
                                          color: Theme.of(context).primaryColor,
                                          width: 1.5,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                                // Core circle — glow pulse
                                Transform.scale(
                                  scale: 1.0 + (p * 0.05),
                                  child: Container(
                                    width: 80,
                                    height: 80,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      gradient: LinearGradient(
                                        begin: Alignment.topLeft,
                                        end: Alignment.bottomRight,
                                        colors: [
                                          Theme.of(context).primaryColor,
                                          const Color(0xFFE6A817),
                                        ],
                                      ),
                                      boxShadow: [
                                        BoxShadow(
                                          color: Theme.of(context)
                                              .primaryColor
                                              .withOpacity(0.20 + p * 0.35),
                                          blurRadius: 18 + (p * 20),
                                          spreadRadius: 1 + (p * 6),
                                        ),
                                      ],
                                    ),
                                    child: const Icon(
                                      LucideIcons.shieldCheck,
                                      size: 36,
                                      color: Colors.white,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 28),
                      // Gradient title
                      ShaderMask(
                        shaderCallback: (bounds) => LinearGradient(
                          colors: [
                            Theme.of(context).primaryColor,
                            const Color(0xFFE6A817),
                            Theme.of(context).primaryColor,
                          ],
                        ).createShader(bounds),
                        child: Text(
                          l10n.smartHome,
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                            letterSpacing: 1.2,
                          ),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        l10n.appTagline,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: isDark
                              ? const Color(0xFF94A3B8)
                              : const Color(0xFF757575),
                          letterSpacing: 1.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 36),

                // ── Form card ──
                SlideTransition(
                  position: _formSlide,
                  child: FadeTransition(
                    opacity: _formFade,
                    child: Container(
                      padding: const EdgeInsets.all(28),
                      decoration: BoxDecoration(
                        color: isDark
                            ? Theme.of(context).colorScheme.surface
                            : Colors.white,
                        borderRadius: BorderRadius.circular(28),
                        border: isDark
                            ? Border.all(
                                color: const Color(0xFF334155),
                                width: 1,
                              )
                            : null,
                        boxShadow: isDark
                            ? []
                            : [
                                BoxShadow(
                                  color: Colors.black.withOpacity(0.06),
                                  blurRadius: 20,
                                  offset: const Offset(0, 8),
                                ),
                              ],
                      ),
                      child: Column(
                        children: [
                          // ── Admin / User toggle ──
                          Container(
                            decoration: BoxDecoration(
                              color: isDark
                                  ? const Color(0xFF0F172A)
                                  : const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(16),
                            ),
                            padding: const EdgeInsets.all(4),
                            child: Row(
                              children: [
                                _buildToggleButton(
                                  label: l10n.admin,
                                  icon: LucideIcons.shield,
                                  isSelected: _selectedMode == 0,
                                  onTap: () {
                                    setState(() {
                                      _selectedMode = 0;
                                      _errorMessage = null;
                                    });
                                  },
                                  isDark: isDark,
                                ),
                                _buildToggleButton(
                                  label: l10n.user,
                                  icon: LucideIcons.user,
                                  isSelected: _selectedMode == 1,
                                  onTap: () {
                                    setState(() {
                                      _selectedMode = 1;
                                      _errorMessage = null;
                                    });
                                  },
                                  isDark: isDark,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),

                          // ── Content based on mode ──
                          AnimatedCrossFade(
                            duration: const Duration(milliseconds: 300),
                            sizeCurve: Curves.easeInOut,
                            firstCurve: Curves.easeOut,
                            secondCurve: Curves.easeOut,
                            crossFadeState: _selectedMode == 0
                                ? CrossFadeState.showFirst
                                : CrossFadeState.showSecond,
                            firstChild: _buildAdminSection(isDark),
                            secondChild: _buildUserForm(),
                          ),
                        ],
                      ),
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

  // ── Admin section with sub-tabs ──
  Widget _buildAdminSection(bool isDark) {
    final l10n = AppLocalizations.of(context)!;
    return Column(
      key: const ValueKey('admin_section'),
      children: [
        // Sub-mode toggle (Sign in / Login)
        Row(
          children: [
            Expanded(
              child: GestureDetector(
                onTap: () => setState(() {
                  _adminSubMode = 0;
                  _errorMessage = null;
                }),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: _adminSubMode == 0
                            ? Theme.of(context).primaryColor
                            : Colors.transparent,
                        width: 2.5,
                      ),
                    ),
                  ),
                  child: Text(
                    l10n.signInFirstLogin,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: _adminSubMode == 0
                          ? FontWeight.w700
                          : FontWeight.w500,
                      color: _adminSubMode == 0
                          ? Theme.of(context).primaryColor
                          : (isDark
                                ? const Color(0xFF94A3B8)
                                : const Color(0xFF757575)),
                    ),
                  ),
                ),
              ),
            ),
            Expanded(
              child: GestureDetector(
                onTap: () => setState(() {
                  _adminSubMode = 1;
                  _errorMessage = null;
                }),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    border: Border(
                      bottom: BorderSide(
                        color: _adminSubMode == 1
                            ? Theme.of(context).primaryColor
                            : Colors.transparent,
                        width: 2.5,
                      ),
                    ),
                  ),
                  child: Text(
                    l10n.login,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: _adminSubMode == 1
                          ? FontWeight.w700
                          : FontWeight.w500,
                      color: _adminSubMode == 1
                          ? Theme.of(context).primaryColor
                          : (isDark
                                ? const Color(0xFF94A3B8)
                                : const Color(0xFF757575)),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        // Sub-mode form
        AnimatedCrossFade(
          duration: const Duration(milliseconds: 250),
          sizeCurve: Curves.easeInOut,
          firstCurve: Curves.easeOut,
          secondCurve: Curves.easeOut,
          crossFadeState: _adminSubMode == 0
              ? CrossFadeState.showFirst
              : CrossFadeState.showSecond,
          firstChild: _buildAdminSignInForm(),
          secondChild: _buildAdminLoginForm(),
        ),
      ],
    );
  }

  // ── Reusable toggle button ──
  Widget _buildToggleButton({
    required String label,
    required IconData icon,
    required bool isSelected,
    required VoidCallback onTap,
    required bool isDark,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeInOut,
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected
                ? Theme.of(context).primaryColor
                : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
            boxShadow: isSelected
                ? [
                    BoxShadow(
                      color: Theme.of(context).primaryColor.withOpacity(0.3),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : [],
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: isSelected
                    ? Colors.white
                    : (isDark
                          ? const Color(0xFF94A3B8)
                          : const Color(0xFF757575)),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: isSelected
                      ? Colors.white
                      : (isDark
                            ? const Color(0xFF94A3B8)
                            : const Color(0xFF757575)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
