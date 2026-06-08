import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import 'package:flutter/services.dart';
import 'package:local_auth/local_auth.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  int _selectedMode = 0;
  int _adminSubMode = 0;
  int _failedAdminAttempts = 0;

  final _signInLoginCtrl = TextEditingController();
  final _signInPasswordCtrl = TextEditingController();
  final _signInHomeCodeCtrl = TextEditingController();

  final _loginCtrl = TextEditingController();
  final _loginPasswordCtrl = TextEditingController();

  final _userLoginCtrl = TextEditingController();
  final _userPasswordCtrl = TextEditingController();

  bool _obscureSignInPassword = true;
  bool _obscureLoginPassword = true;
  bool _obscureUserPassword = true;
  final bool _obscureSignInPhone = true;
  final bool _obscureSignInHomeCode = true;
  final bool _obscureLoginPhone = true;
  final bool _obscureUserLogin = true;

  String? _errorMessage;
  bool _isLoading = false;

  late final AnimationController _logoPulseController;

  @override
  void initState() {
    super.initState();
    _logoPulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkBiometricAutoLogin();
    });
  }

  Future<void> _checkBiometricAutoLogin({bool manual = false}) async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    // Only block auto-login if disabled. If manual, let them use it.
    if (!manual && !appState.biometricAuthEnabled) {
      return;
    }

    if ((_selectedMode == 0 && appState.password.isEmpty) || 
        (_selectedMode == 1 && appState.userAccountPassword.isEmpty)) {
      if (manual && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(
            appState.locale.languageCode == 'ar'
                ? 'يرجى تسجيل الدخول بكلمة المرور أولاً'
                : 'Please login with password first.'
          )),
        );
      }
      return;
    }

    final success = await _authenticateWithBiometrics();
    if (success && mounted) {
      if (manual && !appState.biometricAuthEnabled) {
         appState.updateSecuritySettings(biometricAuth: true);
      }
      if (_selectedMode == 0) {
        _loginCtrl.text = appState.adminName;
        _loginPasswordCtrl.text = appState.password;
        _attemptAdminLogin();
      } else {
        _userLoginCtrl.text = appState.userAccountUsername;
        _userPasswordCtrl.text = appState.userAccountPassword;
        _attemptUserLogin();
      }
    }
  }

  Future<bool> _authenticateWithBiometrics() async {
    final LocalAuthentication auth = LocalAuthentication();
    try {
      final bool canAuthenticateWithBiometrics = await auth.canCheckBiometrics;
      final bool canAuthenticate =
          canAuthenticateWithBiometrics || await auth.isDeviceSupported();

      if (!canAuthenticate) return false;

      return await auth.authenticate(
        localizedReason: 'Please authenticate to log in',
        biometricOnly: true,
      );
    } on PlatformException catch (_) {
      return false;
    } catch (_) {
      return false;
    }
  }

  @override
  void dispose() {
    _signInLoginCtrl.dispose();
    _signInPasswordCtrl.dispose();
    _signInHomeCodeCtrl.dispose();
    _loginCtrl.dispose();
    _loginPasswordCtrl.dispose();
    _userLoginCtrl.dispose();
    _userPasswordCtrl.dispose();
    _logoPulseController.dispose();
    super.dispose();
  }

  InputDecoration _decoration({
    required String label,
    required IconData icon,
    Widget? suffixIcon,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final color = isDark ? Colors.white70 : Colors.black87;
    final hintColor = isDark ? Colors.white54 : Colors.black54;
    final borderColor = isDark ? Colors.white24 : Colors.black12;

    return InputDecoration(
      labelText: label,
      labelStyle: TextStyle(color: hintColor),
      floatingLabelStyle: const TextStyle(color: Color(0xFFF2BE2E)),
      prefixIcon: Icon(icon, color: hintColor),
      suffixIcon: suffixIcon,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: borderColor),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: BorderSide(color: borderColor),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(16),
        borderSide: const BorderSide(color: Color(0xFFF2BE2E), width: 2),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    );
  }

  Widget _errorBox() {
    if (_errorMessage == null) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.10),
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
    );
  }

  Widget _button(String text, VoidCallback? onPressed) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: _isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFF2BE2E),
          foregroundColor: Colors.white,
          disabledBackgroundColor: const Color(0xFFF2BE2E).withOpacity(0.6),
          disabledForegroundColor: Colors.white70,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 0,
        ),
        child: _isLoading
            ? const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                text,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
              ),
      ),
    );
  }

  Future<void> _attemptAdminSignIn() async {
    if (_isLoading) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final login = _signInLoginCtrl.text.trim();
    final password = _signInPasswordCtrl.text.trim();
    final homeCode = _signInHomeCodeCtrl.text.trim();

    final ok = await appState.signInAdminWithHomeCode(
      username: login,
      password: password,
      homeCode: homeCode,
    );

    if (!mounted) return;

    if (!ok) {
      setState(() {
        _isLoading = false;
        _errorMessage = appState.lastAuthError ?? 'Could not register this account.';
      });
      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Account registered successfully')),
    );

    await Future.delayed(const Duration(milliseconds: 900));

    if (!mounted) return;

    final loginOk = await appState.loginAdminWithServer(login: login, password: password);

    if (mounted) {
      setState(() {
        _isLoading = false;
        if (!loginOk) {
          _errorMessage = appState.lastAuthError ?? 'Login failed after registration.';
        } else {
          _errorMessage = null;
        }
      });
    }
  }

  Future<void> _attemptAdminLogin() async {
    if (_isLoading) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final ok = await appState.loginAdminWithServer(
      login: _loginCtrl.text.trim(),
      password: _loginPasswordCtrl.text.trim(),
    );

    if (!mounted) return;

    setState(() {
      _isLoading = false;
      if (!ok) {
        _failedAdminAttempts++;
        _errorMessage = appState.lastAuthError ?? 'Invalid username or password.';
      } else {
        _failedAdminAttempts = 0;
        _errorMessage = null;
      }
    });
  }

  Future<void> _attemptUserLogin() async {
    if (_isLoading) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final ok = await appState.loginUserWithServer(
      adminLogin: _userLoginCtrl.text.trim(),
      userPassword: _userPasswordCtrl.text.trim(),
    );

    if (!mounted) return;

    setState(() {
      _isLoading = false;
      if (!ok) {
        _errorMessage = appState.lastAuthError ?? 'Invalid user password.';
      } else {
        _errorMessage = null;
      }
    });
  }

  Future<void> _showForgotPasswordDialog() async {
    await showDialog<void>(
      context: context,
      builder: (context) => const _ForgotPasswordDialog(),
    );
  }

  void _showServerIpDialog() {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final ipCtrl = TextEditingController(text: appState.serverIp);

    showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Server Settings'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                'Enter the IP address of the backend server:',
                style: TextStyle(fontSize: 13, color: Colors.grey),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: ipCtrl,
                style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
                decoration: const InputDecoration(
                  labelText: 'Server IP',
                  hintText: 'e.g., 10.0.2.2 or 192.168.1.x',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () async {
                final newIp = ipCtrl.text.trim();
                if (newIp.isNotEmpty) {
                  appState.updateNetworkSettings(serverIp: newIp);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Server IP updated to: $newIp')),
                    );
                  }
                }
                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop();
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  Widget _toggleButton({
    required String label,
    required IconData icon,
    required bool selected,
    required VoidCallback onTap,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected
                ? const Color(0xFFF2BE2E)
                : (isDark ? const Color(0xFF334155) : const Color(0xFFF1F5F9)),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: selected
                    ? Colors.white
                    : (isDark ? Colors.white70 : Colors.grey[700]),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: selected
                      ? Colors.white
                      : (isDark ? Colors.white70 : Colors.grey[700]),
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _adminSignInForm() {
    return Column(
      key: const ValueKey('admin_sign_in_form'),
      children: [
        TextField(
          controller: _signInLoginCtrl,
          obscureText: false,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Phone Number',
            icon: LucideIcons.user,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _signInPasswordCtrl,
          obscureText: _obscureSignInPassword,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Password',
            icon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureSignInPassword ? LucideIcons.eyeOff : LucideIcons.eye,
                color: Colors.black54,
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
          obscureText: false,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Home Code',
            icon: LucideIcons.home,
          ),
          onSubmitted: (_) => _attemptAdminSignIn(),
        ),
        const SizedBox(height: 20),
        _errorBox(),
        _button('Sign in (First login)', _attemptAdminSignIn),
      ],
    );
  }

  Widget _adminLoginForm() {
    return Column(
      key: const ValueKey('admin_login_form'),
      children: [
        TextField(
          controller: _loginCtrl,
          obscureText: false,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Phone Number',
            icon: LucideIcons.user,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _loginPasswordCtrl,
          obscureText: _obscureLoginPassword,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Password',
            icon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureLoginPassword ? LucideIcons.eyeOff : LucideIcons.eye,
                color: Colors.black54,
              ),
              onPressed: () => setState(
                () => _obscureLoginPassword = !_obscureLoginPassword,
              ),
            ),
          ),
          onSubmitted: (_) => _attemptAdminLogin(),
        ),
        if (_failedAdminAttempts >= 3)
          Align(
            alignment: Alignment.centerRight,
            child: TextButton(
              onPressed: _showForgotPasswordDialog,
              child: const Text('Forgot Password?'),
            ),
          ),
        const SizedBox(height: 20),
        _errorBox(),
        _button(AppLocalizations.of(context)!.loginButton, _attemptAdminLogin),
        const SizedBox(height: 16),
        IconButton(
          icon: const Icon(Icons.fingerprint, size: 48, color: Color(0xFFF2BE2E)),
          onPressed: () => _checkBiometricAutoLogin(manual: true),
          tooltip: 'Login with Biometrics',
        ),
      ],
    );
  }

  Widget _userForm() {
    return Column(
      key: const ValueKey('user_form'),
      children: [
        TextField(
          controller: _userLoginCtrl,
          obscureText: false,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'Username',
            icon: LucideIcons.user,
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _userPasswordCtrl,
          obscureText: _obscureUserPassword,
          style: TextStyle(color: Theme.of(context).brightness == Brightness.dark ? Colors.white : Colors.black87),
          decoration: _decoration(
            label: 'User Password',
            icon: LucideIcons.keyRound,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureUserPassword ? LucideIcons.eyeOff : LucideIcons.eye,
                color: Colors.black54,
              ),
              onPressed: () =>
                  setState(() => _obscureUserPassword = !_obscureUserPassword),
            ),
          ),
          onSubmitted: (_) => _attemptUserLogin(),
        ),
        const SizedBox(height: 20),
        _errorBox(),
        _button(AppLocalizations.of(context)!.enterAsUser, _attemptUserLogin),
        const SizedBox(height: 16),
        IconButton(
          icon: const Icon(Icons.fingerprint, size: 48, color: Color(0xFFF2BE2E)),
          onPressed: () => _checkBiometricAutoLogin(manual: true),
          tooltip: 'Login with Biometrics',
        ),
      ],
    );
  }

  // Admin Section removed as per new authentication flow

  void _clearAuthFields() {
    _signInLoginCtrl.clear();
    _signInPasswordCtrl.clear();
    _signInHomeCodeCtrl.clear();
    _loginCtrl.clear();
    _loginPasswordCtrl.clear();
    _userLoginCtrl.clear();
    _userPasswordCtrl.clear();
    _errorMessage = null;
  }

  void _setSelectedMode(int mode) {
    setState(() {
      _selectedMode = mode;
      _adminSubMode = 0;
      _failedAdminAttempts = 0;
      _clearAuthFields();
    });
  }

  void _setAdminSubMode(int mode) {
    setState(() {
      _adminSubMode = mode;
      _failedAdminAttempts = 0;
      _clearAuthFields();
    });
  }

  Widget _buildLoginHeader() {
    const gold = Color(0xFFF2BE2E);

    return Column(
      children: [
        SizedBox(
          width: 118,
          height: 118,
          child: AnimatedBuilder(
            animation: _logoPulseController,
            builder: (context, child) {
              final pulse = _logoPulseController.value;

              return Stack(
                alignment: Alignment.center,
                children: [
                  Container(
                    width: 94 + (pulse * 22),
                    height: 94 + (pulse * 22),
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: gold.withOpacity(0.06 + (pulse * 0.03)),
                      border: Border.all(
                        color: gold.withOpacity(0.20 - (pulse * 0.07)),
                        width: 2,
                      ),
                    ),
                  ),
                  Container(
                    width: 92,
                    height: 92,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: gold,
                      boxShadow: [
                        BoxShadow(
                          color: gold.withOpacity(0.30),
                          blurRadius: 24,
                          spreadRadius: 2,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(
                      LucideIcons.shieldCheck,
                      color: Colors.white,
                      size: 40,
                    ),
                  ),
                ],
              );
            },
          ),
        ),
        const SizedBox(height: 18),
        const Text(
          'Smart Home',
          style: TextStyle(
            color: gold,
            fontSize: 31,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.4,
          ),
        ),
        const SizedBox(height: 6),
        const Text(
          'Secure \u2022 Connected \u2022 Intelligent',
          style: TextStyle(
            color: Colors.grey,
            fontSize: 13,
            fontWeight: FontWeight.w500,
            letterSpacing: 1.6,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context);
    final isDark = appState.themeMode == ThemeMode.dark;

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
          IconButton(
            icon: Icon(LucideIcons.settings,
                color: isDark ? Colors.white70 : Colors.grey),
            onPressed: _showServerIpDialog,
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Column(
              children: [
                _buildLoginHeader(),
                const SizedBox(height: 34),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(28),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0F172A) : Colors.white,
                    borderRadius: BorderRadius.circular(28),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.06),
                        blurRadius: 20,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      if (!appState.isDeviceLinked) ...[
                        const Text(
                          'First Login (New Device)',
                          style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                              color: Color(0xFFF2BE2E)),
                        ),
                        const SizedBox(height: 16),
                        _adminSignInForm(),
                      ] else ...[
                        Row(
                          children: [
                            _toggleButton(
                              label: 'Admin',
                              icon: LucideIcons.shield,
                              selected: _selectedMode == 0,
                              onTap: () => _setSelectedMode(0),
                            ),
                            const SizedBox(width: 8),
                            _toggleButton(
                              label: 'User',
                              icon: LucideIcons.user,
                              selected: _selectedMode == 1,
                              onTap: () => _setSelectedMode(1),
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 220),
                          child: _selectedMode == 0
                              ? KeyedSubtree(
                                  key: const ValueKey('admin_login_subtree'),
                                  child: _adminLoginForm(),
                                )
                              : KeyedSubtree(
                                  key: const ValueKey('user_form_subtree'),
                                  child: _userForm(),
                                ),
                        ),
                      ],
                    ],
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

class _ForgotPasswordDialog extends StatefulWidget {
  const _ForgotPasswordDialog();

  @override
  State<_ForgotPasswordDialog> createState() => _ForgotPasswordDialogState();
}

class _ForgotPasswordDialogState extends State<_ForgotPasswordDialog> {
  late final TextEditingController phoneCtrl;
  late final TextEditingController otpCtrl;
  late final TextEditingController newPasswordCtrl;
  late final TextEditingController confirmPasswordCtrl;

  bool otpRequested = false;
  String? dialogError;
  String? dialogInfo;
  bool _obscureRecoveryNewPassword = true;
  bool _obscureRecoveryConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    phoneCtrl = TextEditingController();
    otpCtrl = TextEditingController();
    newPasswordCtrl = TextEditingController();
    confirmPasswordCtrl = TextEditingController();
  }

  @override
  void dispose() {
    phoneCtrl.dispose();
    otpCtrl.dispose();
    newPasswordCtrl.dispose();
    confirmPasswordCtrl.dispose();
    super.dispose();
  }

  Future<void> requestCode() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final ok = await appState.requestPasswordRecoveryCode(
      phoneCtrl.text.trim(),
    );

    if (!mounted) return;

    if (!ok) {
      setState(() {
        dialogError = appState.lastAuthError ?? 'Could not generate recovery code.';
        dialogInfo = null;
      });
      return;
    }

    setState(() {
      otpRequested = true;
      dialogError = null;
      dialogInfo = 'Recovery code generated in Security Logs.';
    });
  }

  Future<void> resetPassword() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    if (newPasswordCtrl.text.trim() != confirmPasswordCtrl.text.trim()) {
      setState(() {
        dialogError = 'Password confirmation does not match.';
        dialogInfo = null;
      });
      return;
    }

    final ok = await appState.resetPasswordWithRecoveryCode(
      phone: phoneCtrl.text.trim(),
      otp: otpCtrl.text.trim(),
      newPassword: newPasswordCtrl.text.trim(),
    );

    if (!mounted) return;

    if (!ok) {
      setState(() {
        dialogError = appState.lastAuthError ?? 'Could not reset password.';
        dialogInfo = null;
      });
      return;
    }

    final scaffoldMessenger = ScaffoldMessenger.of(context);
    Navigator.of(context).pop();
    scaffoldMessenger.showSnackBar(
      const SnackBar(content: Text('Password reset successfully')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Forgot Password'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (dialogError != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  dialogError!,
                  style: const TextStyle(color: Colors.red),
                ),
              ),
            if (dialogInfo != null)
              Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.green.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  dialogInfo!,
                  style: const TextStyle(color: Colors.green),
                ),
              ),
            TextField(
              controller: phoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Owner Phone',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
            ),
            if (otpRequested) ...[
              const SizedBox(height: 12),
              TextField(
                controller: otpCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Recovery Code',
                  prefixIcon: Icon(Icons.password_outlined),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: newPasswordCtrl,
                obscureText: _obscureRecoveryNewPassword,
                decoration: InputDecoration(
                  labelText: 'New Password',
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureRecoveryNewPassword
                          ? LucideIcons.eyeOff
                          : LucideIcons.eye,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscureRecoveryNewPassword = !_obscureRecoveryNewPassword;
                      });
                    },
                  ),
                  prefixIcon: const Icon(Icons.lock_outline),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: confirmPasswordCtrl,
                obscureText: _obscureRecoveryConfirmPassword,
                decoration: InputDecoration(
                  labelText: 'Confirm Password',
                  suffixIcon: IconButton(
                    icon: Icon(
                      _obscureRecoveryConfirmPassword
                          ? LucideIcons.eyeOff
                          : LucideIcons.eye,
                    ),
                    onPressed: () {
                      setState(() {
                        _obscureRecoveryConfirmPassword = !_obscureRecoveryConfirmPassword;
                      });
                    },
                  ),
                  prefixIcon: const Icon(Icons.lock_reset_outlined),
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: otpRequested ? resetPassword : requestCode,
          child: Text(
            otpRequested ? 'Reset Password' : 'Generate Code',
          ),
        ),
      ],
    );
  }
}
