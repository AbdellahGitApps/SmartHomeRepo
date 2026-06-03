import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
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
  bool _obscureSignInPhone = true;
  bool _obscureSignInHomeCode = true;
  bool _obscureLoginPhone = true;
  bool _obscureUserLogin = true;

  bool _obscureRecoveryNewPassword = true;
  bool _obscureRecoveryConfirmPassword = true;
  String? _errorMessage;

  late final AnimationController _logoPulseController;

  @override
  void initState() {
    super.initState();
    _logoPulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
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
    return InputDecoration(
      labelText: label,
      prefixIcon: Icon(icon),
      suffixIcon: suffixIcon,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
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

  Widget _button(String text, VoidCallback onPressed) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFF2BE2E),
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 0,
        ),
        child: Text(
          text,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
        ),
      ),
    );
  }

  Future<void> _attemptAdminSignIn() async {
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
      setState(
        () => _errorMessage =
            appState.lastAuthError ?? 'Could not register this account.',
      );
      return;
    }

    setState(() => _errorMessage = null);

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Account registered successfully')),
    );

    await Future.delayed(const Duration(milliseconds: 900));

    if (!mounted) return;

    await appState.loginAdminWithServer(login: login, password: password);
  }

  Future<void> _attemptAdminLogin() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final ok = await appState.loginAdminWithServer(
      login: _loginCtrl.text.trim(),
      password: _loginPasswordCtrl.text.trim(),
    );

    if (!mounted) return;

    if (!ok) {
      setState(() {
        _failedAdminAttempts++;
        _errorMessage =
            appState.lastAuthError ?? 'Invalid username or password.';
      });
      return;
    }

    setState(() {
      _failedAdminAttempts = 0;
      _errorMessage = null;
    });
  }

  Future<void> _attemptUserLogin() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final ok = await appState.loginUserWithServer(
      adminLogin: _userLoginCtrl.text.trim(),
      userPassword: _userPasswordCtrl.text.trim(),
    );

    if (!mounted) return;

    if (!ok) {
      setState(
        () =>
            _errorMessage = appState.lastAuthError ?? 'Invalid user password.',
      );
      return;
    }

    setState(() => _errorMessage = null);
  }

  Future<void> _showForgotPasswordDialog() async {
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    final phoneCtrl = TextEditingController();
    final otpCtrl = TextEditingController();
    final newPasswordCtrl = TextEditingController();
    final confirmPasswordCtrl = TextEditingController();

    bool otpRequested = false;
    String? dialogError;
    String? dialogInfo;

    await showDialog<void>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            Future<void> requestCode() async {
              final ok = await appState.requestPasswordRecoveryCode(
                phoneCtrl.text.trim(),
              );

              if (!context.mounted) return;

              if (!ok) {
                setDialogState(() {
                  dialogError =
                      appState.lastAuthError ??
                      'Could not generate recovery code.';
                  dialogInfo = null;
                });
                return;
              }

              setDialogState(() {
                otpRequested = true;
                dialogError = null;
                dialogInfo = 'Recovery code generated in Security Logs.';
              });
            }

            Future<void> resetPassword() async {
              if (newPasswordCtrl.text.trim() !=
                  confirmPasswordCtrl.text.trim()) {
                setDialogState(() {
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

              if (!context.mounted) return;

              if (!ok) {
                setDialogState(() {
                  dialogError =
                      appState.lastAuthError ?? 'Could not reset password.';
                  dialogInfo = null;
                });
                return;
              }

              Navigator.of(dialogContext).pop();

              if (!mounted) return;

              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Password reset successfully')),
              );
            }

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
                              setDialogState(() {
                                _obscureRecoveryNewPassword =
                                    !_obscureRecoveryNewPassword;
                              });
                            },
                          ),
                          prefixIcon: Icon(Icons.lock_outline),
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
                              setDialogState(() {
                                _obscureRecoveryConfirmPassword =
                                    !_obscureRecoveryConfirmPassword;
                              });
                            },
                          ),
                          prefixIcon: Icon(Icons.lock_reset_outlined),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
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
          },
        );
      },
    );

    phoneCtrl.dispose();
    otpCtrl.dispose();
    newPasswordCtrl.dispose();
    confirmPasswordCtrl.dispose();
  }

  Widget _toggleButton({
    required String label,
    required IconData icon,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected ? const Color(0xFFF2BE2E) : const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                icon,
                size: 18,
                color: selected ? Colors.white : Colors.grey[700],
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: TextStyle(
                  color: selected ? Colors.white : Colors.grey[700],
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
      children: [
        TextField(
          controller: _signInLoginCtrl,
          obscureText: _obscureSignInPhone,
          decoration: _decoration(
            label: 'Phone Number',
            icon: LucideIcons.user,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureSignInPhone ? LucideIcons.eyeOff : LucideIcons.eye,
              ),
              onPressed: () =>
                  setState(() => _obscureSignInPhone = !_obscureSignInPhone),
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _signInPasswordCtrl,
          obscureText: _obscureSignInPassword,
          decoration: _decoration(
            label: 'Password',
            icon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureSignInPassword ? LucideIcons.eyeOff : LucideIcons.eye,
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
          obscureText: _obscureSignInHomeCode,
          decoration: _decoration(
            label: 'Home Code',
            icon: LucideIcons.home,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureSignInHomeCode ? LucideIcons.eyeOff : LucideIcons.eye,
              ),
              onPressed: () => setState(
                () => _obscureSignInHomeCode = !_obscureSignInHomeCode,
              ),
            ),
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
      children: [
        TextField(
          controller: _loginCtrl,
          obscureText: _obscureLoginPhone,
          decoration: _decoration(
            label: 'Phone Number',
            icon: LucideIcons.user,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureLoginPhone ? LucideIcons.eyeOff : LucideIcons.eye,
              ),
              onPressed: () =>
                  setState(() => _obscureLoginPhone = !_obscureLoginPhone),
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _loginPasswordCtrl,
          obscureText: _obscureLoginPassword,
          decoration: _decoration(
            label: 'Password',
            icon: LucideIcons.lock,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureLoginPassword ? LucideIcons.eyeOff : LucideIcons.eye,
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
        _button('Sign In', _attemptAdminLogin),
      ],
    );
  }

  Widget _userForm() {
    return Column(
      children: [
        TextField(
          controller: _userLoginCtrl,
          obscureText: _obscureUserLogin,
          decoration: _decoration(
            label: 'Username',
            icon: LucideIcons.user,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureUserLogin ? LucideIcons.eyeOff : LucideIcons.eye,
              ),
              onPressed: () =>
                  setState(() => _obscureUserLogin = !_obscureUserLogin),
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _userPasswordCtrl,
          obscureText: _obscureUserPassword,
          decoration: _decoration(
            label: 'User Password',
            icon: LucideIcons.keyRound,
            suffixIcon: IconButton(
              icon: Icon(
                _obscureUserPassword ? LucideIcons.eyeOff : LucideIcons.eye,
              ),
              onPressed: () =>
                  setState(() => _obscureUserPassword = !_obscureUserPassword),
            ),
          ),
          onSubmitted: (_) => _attemptUserLogin(),
        ),
        const SizedBox(height: 20),
        _errorBox(),
        _button('Enter as A User', _attemptUserLogin),
      ],
    );
  }

  Widget _adminSection() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextButton(
                onPressed: () => _setAdminSubMode(0),
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  child: Text(
                    'Sign in (First login)',
                    maxLines: 1,
                    softWrap: false,
                    style: TextStyle(
                      color: _adminSubMode == 0
                          ? const Color(0xFFF2BE2E)
                          : Colors.grey,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
            ),
            Expanded(
              child: TextButton(
                onPressed: () => _setAdminSubMode(1),
                child: Text(
                  'Login',
                  style: TextStyle(
                    color: _adminSubMode == 1
                        ? const Color(0xFFF2BE2E)
                        : Colors.grey,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ),
          ],
        ),
        Container(
          height: 2,
          alignment: _adminSubMode == 0
              ? Alignment.centerLeft
              : Alignment.centerRight,
          child: FractionallySizedBox(
            widthFactor: 0.5,
            child: Container(color: const Color(0xFFF2BE2E)),
          ),
        ),
        const SizedBox(height: 20),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 200),
          child: _adminSubMode == 0 ? _adminSignInForm() : _adminLoginForm(),
        ),
      ],
    );
  }

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
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
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
                    color: Colors.white,
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
                            ? _adminSection()
                            : _userForm(),
                      ),
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
