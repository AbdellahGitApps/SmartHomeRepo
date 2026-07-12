import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import 'welcome_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _adminNameController = TextEditingController();
  final _adminPasswordController = TextEditingController();
  final _doorPinController = TextEditingController();
  final _cameraPinController = TextEditingController();
  final _userAccountController = TextEditingController();
  final _userUsernameController = TextEditingController();
  final _aptController = TextEditingController(text: '');
  final _homeIdController = TextEditingController(text: '');
  final _homeCodeController = TextEditingController();

  bool _obscureAdminPhone = true;
  bool _obscureAdminPassword = true;
  bool _obscureDoorPin = true;
  bool _obscureCameraPin = true;
  bool _obscureUserAccount = true;
  bool _obscureUserPassword = true;
  bool _obscureHomeCode = true;

  bool _editAccount = false;
  bool _editSecurity = false;

  String _actualHomeCode = '';

  @override
  void initState() {
    super.initState();
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    _initializeControllers(appState);
  }

  void _initializeControllers(AppStateProvider appState) {
    _adminNameController.text = appState.adminName;
    _aptController.text = appState.apartmentNumber;
    _homeIdController.text = appState.homeId;
    _actualHomeCode = appState.homeCode;
    _homeCodeController.text = appState.isAdmin && !_obscureHomeCode
        ? _actualHomeCode
        : '********';
    _adminPasswordController.text = appState.password;
    _doorPinController.text = appState.doorPin;
    _cameraPinController.text = appState.cameraPin;
    _userAccountController.text = appState.userAccountPassword;
    _userUsernameController.text = appState.userAccountUsername;
    _aptController.text = appState.apartmentNumber;
    _homeIdController.text = appState.homeId;
    _actualHomeCode = appState.homeCode;
    _homeCodeController.text = appState.isAdmin && !_obscureHomeCode
        ? _actualHomeCode
        : '********';
  }

  @override
  void dispose() {
    _adminNameController.dispose();
    _adminPasswordController.dispose();
    _doorPinController.dispose();
    _cameraPinController.dispose();
    _userAccountController.dispose();
    _userUsernameController.dispose();
    _aptController.dispose();
    _homeIdController.dispose();
    _homeCodeController.dispose();
    super.dispose();
  }

  String _hiddenValue() => '*********';

  Future<void> _saveSettings(
    AppStateProvider appState,
    AppLocalizations l10n,
  ) async {
    if (appState.isAdmin) {
      if (_editSecurity) {
        final usernameOk = await appState.updateUserAccountUsername(
          _userUsernameController.text,
        );

        if (!usernameOk) {
          _userUsernameController.text = appState.userAccountUsername;
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                appState.lastAuthError ?? 'Could not update username.',
              ),
              backgroundColor: Colors.red,
              behavior: SnackBarBehavior.floating,
            ),
          );
          return;
        }
      }

      if (_editAccount) {
        appState.updateName(_adminNameController.text);
      }
    }

    setState(() {
      _editAccount = false;
      _editSecurity = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(l10n.saveSettings),
        backgroundColor: Theme.of(context).primaryColor,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _resetToDefaults(AppStateProvider appState, AppLocalizations l10n) {
    if (!appState.isAdmin) return;

    appState.resetToDefaults();
    _initializeControllers(appState);

    setState(() {
      _editAccount = false;
      _editSecurity = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(l10n.resetDefaults),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  void _showSimplePasswordDialog({
    required String title,
    required String label,
    required bool isDark,
    required void Function(String value) onSave,
  }) {
    final valueController = TextEditingController();
    final confirmController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: isDark ? const Color(0xFF1E293B) : Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          title: Text(
            title,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: isDark ? Colors.white : Colors.black,
            ),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: valueController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: label,
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: isDark
                      ? const Color(0xFF0F172A)
                      : Colors.grey.shade50,
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: confirmController,
                obscureText: true,
                decoration: InputDecoration(
                  labelText: 'Confirm',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  filled: true,
                  fillColor: isDark
                      ? const Color(0xFF0F172A)
                      : Colors.grey.shade50,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                if (valueController.text.trim().isEmpty ||
                    valueController.text != confirmController.text) {
                  return;
                }

                onSave(valueController.text.trim());
                Navigator.pop(context);

                ScaffoldMessenger.of(
                  context,
                ).showSnackBar(SnackBar(content: Text('$title updated')));
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).primaryColor,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final isAdmin = appState.isAdmin;

    _adminNameController.text = appState.adminName;
    _aptController.text = appState.apartmentNumber;
    _homeIdController.text = appState.homeId;
    _actualHomeCode = appState.homeCode;
    _homeCodeController.text = appState.isAdmin && !_obscureHomeCode
        ? _actualHomeCode
        : '********';
    _adminPasswordController.text = appState.password;
    _doorPinController.text = appState.doorPin;
    _cameraPinController.text = appState.cameraPin;
    _userAccountController.text = appState.userAccountPassword;
    _userUsernameController.text = appState.userAccountUsername;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.settings),
        elevation: 0,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        child: Column(
          children: [
            _buildSection(
              title: 'Home Info',
              icon: LucideIcons.home,
              isDark: isDark,
              showEditButton: false,
              children: [
                _buildTextField(
                  label: 'Apartment Number',
                  controller: _aptController,
                  icon: null,
                  isDark: isDark,
                  enabled: false,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: 'Home ID',
                  controller: _homeIdController,
                  icon: null,
                  isDark: isDark,
                  enabled: false,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: 'Home Code',
                  controller: _homeCodeController,
                  icon: null,
                  isDark: isDark,
                  enabled: true,
                  readOnly: true,
                  suffix:
                      (Provider.of<AppStateProvider>(
                            context,
                            listen: false,
                          ).userRole.toLowerCase() ==
                          'user')
                      ? null
                      : (appState.isAdmin
                            ? Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: Icon(
                                      _obscureHomeCode
                                          ? LucideIcons.eyeOff
                                          : LucideIcons.eye,
                                      size: 18,
                                    ),
                                    onPressed: () => setState(() {
                                      _obscureHomeCode = !_obscureHomeCode;
                                      _homeCodeController.text =
                                          _obscureHomeCode
                                          ? '********'
                                          : _actualHomeCode;
                                    }),
                                  ),
                                  IconButton(
                                    icon: const Icon(
                                      LucideIcons.copy,
                                      size: 18,
                                    ),
                                    onPressed: () {
                                      Clipboard.setData(
                                        ClipboardData(
                                          text: appState.isAdmin
                                              ? _actualHomeCode
                                              : '********',
                                        ),
                                      );
                                      ScaffoldMessenger.of(
                                        context,
                                      ).showSnackBar(
                                        const SnackBar(
                                          content: Text('Home Code copied'),
                                          duration: Duration(seconds: 1),
                                        ),
                                      );
                                    },
                                  ),
                                ],
                              )
                            : null),
                ),
              ],
            ),
            const SizedBox(height: 24),

            if (isAdmin) ...[
              _buildSection(
                title: 'Admin Account',
                icon: LucideIcons.user,
              isDark: isDark,
              isEditing: isAdmin && _editAccount,
              showEditButton: isAdmin,
              onEditToggle: isAdmin
                  ? () => setState(() => _editAccount = !_editAccount)
                  : null,
              children: [
                _buildTextField(
                  label: 'Phone Number',
                  controller: _adminNameController,
                  icon: LucideIcons.phone,
                  isDark: isDark,
                  obscureText: _obscureAdminPhone,
                  enabled: isAdmin,
                  readOnly: !isAdmin || !_editAccount,
                  suffix: isAdmin
                      ? IconButton(
                          icon: Icon(
                            _obscureAdminPhone
                                ? LucideIcons.eyeOff
                                : LucideIcons.eye,
                            size: 18,
                          ),
                          onPressed: () => setState(
                            () => _obscureAdminPhone = !_obscureAdminPhone,
                          ),
                        )
                      : null,
                ),
                if (isAdmin) ...[
                  const SizedBox(height: 12),
                  _buildTextField(
                    label: 'Password',
                    controller: _adminPasswordController,
                    icon: LucideIcons.lock,
                    isDark: isDark,
                    obscureText: _obscureAdminPassword,
                    enabled: true,
                    readOnly: true,
                    suffix: IconButton(
                      icon: Icon(
                        _obscureAdminPassword
                            ? LucideIcons.eyeOff
                            : LucideIcons.eye,
                        size: 18,
                      ),
                      onPressed: () => setState(
                        () => _obscureAdminPassword = !_obscureAdminPassword,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildSettingTile(
                    title: 'Change Password',
                    icon: LucideIcons.key,
                    isDark: isDark,
                    enabled: _editAccount,
                    onTap: _editAccount
                        ? () => _showSimplePasswordDialog(
                            title: 'Password',
                            label: 'New Password',
                            isDark: isDark,
                            onSave: (value) {
                              _adminPasswordController.text = value;
                              appState.updatePassword(value);
                            },
                          )
                        : null,
                  ),
                  const SizedBox(height: 12),
                  _buildTextField(
                    label: 'Door PIN',
                    controller: _doorPinController,
                    icon: LucideIcons.lock,
                    isDark: isDark,
                    obscureText: _obscureDoorPin,
                    enabled: true,
                    readOnly: true,
                    suffix: IconButton(
                      icon: Icon(
                        _obscureDoorPin ? LucideIcons.eyeOff : LucideIcons.eye,
                        size: 18,
                      ),
                      onPressed: () =>
                          setState(() => _obscureDoorPin = !_obscureDoorPin),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildSettingTile(
                    title: 'Change Door PIN',
                    icon: LucideIcons.key,
                    isDark: isDark,
                    enabled: _editAccount,
                    onTap: _editAccount
                        ? () => _showSimplePasswordDialog(
                            title: 'Door PIN',
                            label: 'New Door PIN',
                            isDark: isDark,
                            onSave: (value) {
                              _doorPinController.text = value;
                              appState.updateDoorPin(value);
                            },
                          )
                        : null,
                  ),
                ] else ...[
                  const SizedBox(height: 12),
                  _buildTextField(
                    label: 'Password',
                    controller: _adminPasswordController,
                    icon: LucideIcons.lock,
                    isDark: isDark,
                    obscureText: true,
                    enabled: false,
                    readOnly: true,
                  ),
                ],
              ],
            ),
            const SizedBox(height: 24),
            _buildSection(
              title: l10n.security,
              icon: LucideIcons.shield,
              isDark: isDark,
              isEditing: isAdmin && _editSecurity,
              showEditButton: isAdmin,
              onEditToggle: isAdmin
                  ? () => setState(() => _editSecurity = !_editSecurity)
                  : null,
              children: [
                _buildSwitchTile(
                  title: l10n.appLock,
                  value: appState.appLockEnabled,
                  onChanged: isAdmin && _editSecurity
                      ? (val) => appState.updateSecuritySettings(appLock: val)
                      : null,
                  isDark: isDark,
                ),
                const SizedBox(height: 12),
                _buildSwitchTile(
                  title: l10n.biometricAuth,
                  value: appState.biometricAuthEnabled,
                  onChanged: isAdmin && _editSecurity
                      ? (val) => appState.updateSecuritySettings(biometricAuth: val)
                      : null,
                  isDark: isDark,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: 'User Account',
                  controller: isAdmin
                      ? _userUsernameController
                      : TextEditingController(text: _hiddenValue()),
                  icon: LucideIcons.user,
                  isDark: isDark,
                  obscureText: isAdmin ? _obscureUserAccount : true,
                  enabled: isAdmin,
                  readOnly: !isAdmin || !_editSecurity,
                  suffix: isAdmin
                      ? IconButton(
                          icon: Icon(
                            _obscureUserAccount
                                ? LucideIcons.eyeOff
                                : LucideIcons.eye,
                            size: 18,
                          ),
                          onPressed: () => setState(
                            () => _obscureUserAccount = !_obscureUserAccount,
                          ),
                        )
                      : null,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: 'Password',
                  controller: isAdmin
                      ? _userAccountController
                      : TextEditingController(text: _hiddenValue()),
                  icon: LucideIcons.lock,
                  isDark: isDark,
                  obscureText: isAdmin ? _obscureUserPassword : true,
                  enabled: isAdmin,
                  readOnly: true,
                  suffix: isAdmin
                      ? IconButton(
                          icon: Icon(
                            _obscureUserPassword
                                ? LucideIcons.eyeOff
                                : LucideIcons.eye,
                            size: 18,
                          ),
                          onPressed: () => setState(
                            () => _obscureUserPassword = !_obscureUserPassword,
                          ),
                        )
                      : null,
                ),
                if (isAdmin) ...[
                  const SizedBox(height: 12),
                  _buildSettingTile(
                    title: 'Change Password',
                    icon: LucideIcons.key,
                    isDark: isDark,
                    enabled: _editSecurity,
                    onTap: _editSecurity
                        ? () => _showSimplePasswordDialog(
                            title: 'User Account',
                            label: 'New Password',
                            isDark: isDark,
                            onSave: (value) {
                              _userAccountController.text = value;
                              appState.updateUserAccountPassword(value);
                            },
                          )
                        : null,
                  ),
                ],
                const SizedBox(height: 12),
                _buildTextField(
                  label: 'Camera PIN',
                  controller: isAdmin
                      ? _cameraPinController
                      : TextEditingController(text: _hiddenValue()),
                  icon: LucideIcons.camera,
                  isDark: isDark,
                  obscureText: isAdmin ? _obscureCameraPin : true,
                  enabled: isAdmin,
                  readOnly: true,
                  suffix: isAdmin
                      ? IconButton(
                          icon: Icon(
                            _obscureCameraPin
                                ? LucideIcons.eyeOff
                                : LucideIcons.eye,
                            size: 18,
                          ),
                          onPressed: () => setState(
                            () => _obscureCameraPin = !_obscureCameraPin,
                          ),
                        )
                      : null,
                ),
                if (isAdmin) ...[
                  const SizedBox(height: 12),
                  _buildSettingTile(
                    title: 'Change Camera PIN',
                    icon: LucideIcons.key,
                    isDark: isDark,
                    enabled: _editSecurity,
                    onTap: _editSecurity
                        ? () => _showSimplePasswordDialog(
                            title: 'Camera PIN',
                            label: 'New Camera PIN',
                            isDark: isDark,
                            onSave: (value) {
                              _cameraPinController.text = value;
                              appState.updateCameraPin(value);
                            },
                          )
                        : null,
                  ),
                ],
              ],
            ),
            const SizedBox(height: 24),
            ],
            _buildSection(
              title: l10n.appearance,
              icon: LucideIcons.palette,
              isDark: isDark,
              showEditButton: false,
              isEditing: true,
              children: [
                _buildSettingTile(
                  title: l10n.theme,
                  icon: LucideIcons.moon,
                  isDark: isDark,
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        LucideIcons.sun,
                        size: 16,
                        color: appState.themeMode == ThemeMode.light
                            ? Theme.of(context).primaryColor
                            : Colors.grey,
                      ),
                      Switch(
                        value: appState.themeMode == ThemeMode.dark,
                        onChanged: (val) => appState.toggleTheme(val),
                        activeThumbColor: Theme.of(context).primaryColor,
                      ),
                      Icon(
                        LucideIcons.moon,
                        size: 16,
                        color: appState.themeMode == ThemeMode.dark
                            ? Theme.of(context).primaryColor
                            : Colors.grey,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                _buildSettingTile(
                  title: l10n.language,
                  icon: LucideIcons.languages,
                  isDark: isDark,
                  trailing: SegmentedButton<String>(
                    segments: const [
                      ButtonSegment<String>(value: 'en', label: Text('EN')),
                      ButtonSegment<String>(value: 'ar', label: Text('AR')),
                    ],
                    selected: {appState.locale.languageCode},
                    onSelectionChanged: (Set<String> newSelection) {
                      appState.switchLanguage(newSelection.first);
                    },
                    style: const ButtonStyle(
                      visualDensity: VisualDensity.compact,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),

            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _saveSettings(appState, l10n),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Theme.of(context).primaryColor,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      elevation: 0,
                    ),
                    child: Text(
                      l10n.saveSettings,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
                ),
              ],
            ),
            if (isAdmin) ...[
              const SizedBox(height: 12),
              TextButton.icon(
                onPressed: () => _resetToDefaults(appState, l10n),
                icon: const Icon(LucideIcons.rotateCcw, size: 16),
                label: Text(l10n.resetDefaults),
                style: TextButton.styleFrom(foregroundColor: Colors.grey),
              ),
            ],
            const SizedBox(height: 24),
            _buildLogoutButton(appState, l10n, isDark),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSection({
    required String title,
    required IconData icon,
    required bool isDark,
    required List<Widget> children,
    bool isEditing = false,
    VoidCallback? onEditToggle,
    bool showEditButton = true,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 12, right: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(icon, size: 18, color: Theme.of(context).primaryColor),
                  const SizedBox(width: 8),
                  Text(
                    title.toUpperCase(),
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w800,
                      color: Theme.of(context).primaryColor,
                      letterSpacing: 1.2,
                    ),
                  ),
                ],
              ),
              if (showEditButton)
                TextButton.icon(
                  onPressed: onEditToggle,
                  icon: Icon(
                    isEditing ? LucideIcons.x : LucideIcons.edit3,
                    size: 14,
                  ),
                  label: Text(
                    isEditing ? 'Cancel' : 'Edit',
                    style: const TextStyle(fontSize: 12),
                  ),
                  style: TextButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    foregroundColor: isEditing
                        ? Colors.red
                        : Theme.of(context).primaryColor,
                  ),
                ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E293B) : Colors.white,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: isEditing
                  ? Theme.of(context).primaryColor.withOpacity(0.5)
                  : (isDark ? const Color(0xFF334155) : Colors.transparent),
              width: 1.5,
            ),
            boxShadow: isDark
                ? []
                : [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.03),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
          ),
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildTextField({
    required String label,
    required TextEditingController controller,
    IconData? icon,
    required bool isDark,
    bool obscureText = false,
    Widget? suffix,
    bool enabled = true,
    bool readOnly = false,
  }) {
    final isVisuallyDisabled = !enabled || readOnly;

    final activeFillColor = isDark
        ? const Color(0xFF0F172A)
        : Colors.grey.shade50;

    final lockedFillColor = isDark
        ? const Color(0xFF1E293B)
        : Colors.grey.shade100;

    final activeBorderColor = isDark
        ? const Color(0xFF334155)
        : Colors.grey.shade300;

    final lockedBorderColor = isDark
        ? const Color(0xFF334155).withOpacity(0.5)
        : Colors.grey.shade200;

    final fieldFillColor = isVisuallyDisabled
        ? lockedFillColor
        : activeFillColor;

    final fieldBorderColor = isVisuallyDisabled
        ? lockedBorderColor
        : activeBorderColor;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: isDark ? Colors.grey.shade400 : Colors.grey.shade700,
            ),
          ),
        ),
        TextField(
          controller: controller,
          obscureText: obscureText,
          enabled: enabled,
          readOnly: readOnly,
          enableInteractiveSelection: !isVisuallyDisabled,
          mouseCursor: isVisuallyDisabled
              ? SystemMouseCursors.basic
              : SystemMouseCursors.text,
          decoration: InputDecoration(
            prefixIcon: icon != null ? Icon(icon, size: 20) : null,
            suffixIcon:
                (label == 'Home Code' &&
                    (Provider.of<AppStateProvider>(
                          context,
                          listen: false,
                        ).userRole.toLowerCase() ==
                        'user'))
                ? null
                : suffix,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
            disabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: fieldBorderColor),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: fieldBorderColor, width: 1),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(
                color: isVisuallyDisabled
                    ? fieldBorderColor
                    : Theme.of(context).primaryColor,
                width: isVisuallyDisabled ? 1 : 2,
              ),
            ),
            hoverColor: fieldFillColor,
            focusColor: fieldFillColor,
            filled: true,
            fillColor: fieldFillColor,
          ),
        ),
      ],
    );
  }

  Widget _buildSettingTile({
    required String title,
    required IconData icon,
    required bool isDark,
    Widget? trailing,
    VoidCallback? onTap,
    bool enabled = true,
  }) {
    return InkWell(
      onTap: enabled ? onTap : null,
      borderRadius: BorderRadius.circular(12),
      child: Opacity(
        opacity: enabled ? 1.0 : 0.5,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 8),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(
                  icon,
                  size: 18,
                  color: Theme.of(context).primaryColor,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.w500),
                ),
              ),
              if (trailing != null)
                trailing
              else
                const Icon(
                  LucideIcons.chevronRight,
                  size: 16,
                  color: Colors.grey,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSwitchTile({
    required String title,
    required bool value,
    required ValueChanged<bool>? onChanged,
    required bool isDark,
  }) {
    final enabled = onChanged != null;

    return Opacity(
      opacity: enabled ? 1.0 : 0.5,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  LucideIcons.shieldAlert,
                  size: 18,
                  color: Color(0xFFF9C846),
                ),
              ),
              const SizedBox(width: 16),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeThumbColor: Theme.of(context).primaryColor,
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutButton(
    AppStateProvider appState,
    AppLocalizations l10n,
    bool isDark,
  ) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () async {
          await appState.logout();
          if (context.mounted) {
            Navigator.of(context).pushAndRemoveUntil(
              PageRouteBuilder(
                transitionDuration: const Duration(milliseconds: 400),
                pageBuilder: (context, animation, secondaryAnimation) {
                  return FadeTransition(
                    opacity: animation,
                    child: const WelcomeScreen(),
                  );
                },
              ),
              (Route<dynamic> route) => false,
            );
          }
        },
        icon: const Icon(LucideIcons.logOut, size: 18),
        label: Text(
          l10n.logout,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.red,
          side: BorderSide(color: Colors.red.withOpacity(0.3)),
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
      ),
    );
  }
}
