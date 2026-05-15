import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _nameController = TextEditingController();
  final _serverIpController = TextEditingController();
  final _cameraUrlController = TextEditingController();
  final _homeCodeController = TextEditingController();
  final _pinController = TextEditingController();

  bool _obscureHomeCode = true;
  bool _obscurePin = true;
  bool _isTestingConnection = false;

  // Edit states for sections
  bool _editAccount = false;
  bool _editSecurity = false;
  bool _editNetwork = false;

  @override
  void initState() {
    super.initState();
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    _initializeControllers(appState);
  }

  void _initializeControllers(AppStateProvider appState) {
    _nameController.text = appState.userName;
    _serverIpController.text = appState.serverIp;
    _cameraUrlController.text = appState.cameraUrl;
    _homeCodeController.text = appState.homeCode;
    _pinController.text = appState.userPin;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _serverIpController.dispose();
    _cameraUrlController.dispose();
    _homeCodeController.dispose();
    _pinController.dispose();
    super.dispose();
  }

  Future<void> _testConnection(AppLocalizations l10n) async {
    setState(() => _isTestingConnection = true);
    await Future.delayed(const Duration(seconds: 2));
    if (mounted) {
      setState(() => _isTestingConnection = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(l10n.connectionSuccess),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  void _saveSettings(AppStateProvider appState, AppLocalizations l10n) {
    appState.updateName(_nameController.text);
    appState.updateNetworkSettings(
      serverIp: _serverIpController.text,
      cameraUrl: _cameraUrlController.text,
      homeCode: _homeCodeController.text,
    );
    appState.updateSecuritySettings(
      pin: _pinController.text,
    );
    
    setState(() {
      _editAccount = false;
      _editSecurity = false;
      _editNetwork = false;
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
    appState.resetToDefaults();
    _initializeControllers(appState);
    
    setState(() {
      _editAccount = false;
      _editSecurity = false;
      _editNetwork = false;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(l10n.resetDefaults),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;

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
            // --- 1. ACCOUNT SECTION ---
            _buildSection(
              title: l10n.account,
              icon: LucideIcons.user,
              isDark: isDark,
              isEditing: _editAccount,
              onEditToggle: () => setState(() => _editAccount = !_editAccount),
              children: [
                _buildTextField(
                  label: l10n.adminName,
                  controller: _nameController,
                  icon: LucideIcons.userCircle,
                  isDark: isDark,
                  enabled: _editAccount,
                ),
                const SizedBox(height: 12),
                _buildSettingTile(
                  title: l10n.changePassword,
                  icon: LucideIcons.key,
                  isDark: isDark,
                  onTap: _editAccount ? () {} : null,
                  enabled: _editAccount,
                ),
              ],
            ),

            const SizedBox(height: 24),

            // --- 2. SECURITY SECTION ---
            _buildSection(
              title: l10n.security,
              icon: LucideIcons.shield,
              isDark: isDark,
              isEditing: _editSecurity,
              onEditToggle: () => setState(() => _editSecurity = !_editSecurity),
              children: [
                _buildSwitchTile(
                  title: l10n.appLock,
                  value: appState.appLockEnabled,
                  onChanged: _editSecurity ? (val) => appState.updateSecuritySettings(appLock: val) : null,
                  isDark: isDark,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: l10n.pinCode,
                  controller: _pinController,
                  icon: LucideIcons.lock,
                  isDark: isDark,
                  obscureText: _obscurePin,
                  enabled: _editSecurity,
                  suffix: IconButton(
                    icon: Icon(_obscurePin ? LucideIcons.eyeOff : LucideIcons.eye, size: 18),
                    onPressed: () => setState(() => _obscurePin = !_obscurePin),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // --- 3. LOCAL NETWORK SECTION ---
            _buildSection(
              title: l10n.localNetwork,
              icon: LucideIcons.network,
              isDark: isDark,
              isEditing: _editNetwork,
              onEditToggle: () => setState(() => _editNetwork = !_editNetwork),
              children: [
                _buildTextField(
                  label: l10n.serverIp,
                  controller: _serverIpController,
                  icon: LucideIcons.server,
                  isDark: isDark,
                  enabled: _editNetwork,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: l10n.cameraStreamUrl,
                  controller: _cameraUrlController,
                  icon: LucideIcons.video,
                  isDark: isDark,
                  enabled: _editNetwork,
                ),
                const SizedBox(height: 12),
                _buildTextField(
                  label: l10n.homeCodeLabel,
                  controller: _homeCodeController,
                  icon: LucideIcons.hash,
                  isDark: isDark,
                  obscureText: _obscureHomeCode,
                  enabled: _editNetwork,
                  suffix: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: Icon(_obscureHomeCode ? LucideIcons.eyeOff : LucideIcons.eye, size: 18),
                        onPressed: () => setState(() => _obscureHomeCode = !_obscureHomeCode),
                      ),
                      IconButton(
                        icon: const Icon(LucideIcons.copy, size: 18),
                        onPressed: () {
                          Clipboard.setData(ClipboardData(text: _homeCodeController.text));
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(l10n.copiedToClipboard), duration: const Duration(seconds: 1)),
                          );
                        },
                      ),
                    ],
                  ),
                ),
                if (_editNetwork) ...[
                  const SizedBox(height: 20),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _isTestingConnection ? null : () => _testConnection(l10n),
                          icon: _isTestingConnection 
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                            : const Icon(LucideIcons.radio, size: 18),
                          label: Text(l10n.testConnection),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 12),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),

            const SizedBox(height: 24),

            // --- 4. APPEARANCE SECTION ---
            _buildSection(
              title: l10n.appearance,
              icon: LucideIcons.palette,
              isDark: isDark,
              isEditing: true, // Appearance is always "editable" since it's just toggles/segments
              showEditButton: false,
              children: [
                _buildSettingTile(
                  title: l10n.theme,
                  icon: LucideIcons.moon,
                  isDark: isDark,
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(LucideIcons.sun, size: 16, color: appState.themeMode == ThemeMode.light ? Theme.of(context).primaryColor : Colors.grey),
                      Switch(
                        value: appState.themeMode == ThemeMode.dark,
                        onChanged: (val) => appState.toggleTheme(val),
                        activeColor: Theme.of(context).primaryColor,
                      ),
                      Icon(LucideIcons.moon, size: 16, color: appState.themeMode == ThemeMode.dark ? Theme.of(context).primaryColor : Colors.grey),
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
                    style: const ButtonStyle(visualDensity: VisualDensity.compact),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 32),

            // --- PRIMARY ACTIONS (Visible only if something is being edited) ---
            if (_editAccount || _editSecurity || _editNetwork) ...[
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => _saveSettings(appState, l10n),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Theme.of(context).primaryColor,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0,
                      ),
                      child: Text(l10n.saveSettings, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextButton.icon(
                onPressed: () => _resetToDefaults(appState, l10n),
                icon: const Icon(LucideIcons.rotateCcw, size: 16),
                label: Text(l10n.resetDefaults),
                style: TextButton.styleFrom(foregroundColor: Colors.grey),
              ),
              const SizedBox(height: 24),
            ],
            
            // --- LOGOUT (PINNED TO BOTTOM-ISH) ---
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
                  icon: Icon(isEditing ? LucideIcons.x : LucideIcons.edit3, size: 14),
                  label: Text(isEditing ? "Cancel" : "Edit", style: const TextStyle(fontSize: 12)),
                  style: TextButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    foregroundColor: isEditing ? Colors.red : Theme.of(context).primaryColor,
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
            boxShadow: isDark ? [] : [
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
    required IconData icon,
    required bool isDark,
    bool obscureText = false,
    Widget? suffix,
    bool enabled = true,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscureText,
      enabled: enabled,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 20),
        suffixIcon: suffix,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
        disabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: isDark ? const Color(0xFF334155).withOpacity(0.5) : Colors.grey.shade200),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: isDark ? const Color(0xFF334155) : Colors.grey.shade300),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide(color: Theme.of(context).primaryColor, width: 2),
        ),
        filled: true,
        fillColor: enabled 
          ? (isDark ? const Color(0xFF0F172A) : Colors.grey.shade50)
          : (isDark ? const Color(0xFF1E293B) : Colors.grey.shade100),
      ),
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
      onTap: onTap,
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
                child: Icon(icon, size: 18, color: Theme.of(context).primaryColor),
              ),
              const SizedBox(width: 16),
              Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w500))),
              if (trailing != null) trailing else const Icon(LucideIcons.chevronRight, size: 16, color: Colors.grey),
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
    bool enabled = onChanged != null;
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
                child: const Icon(LucideIcons.shieldAlert, size: 18, color: Color(0xFFF9C846)),
              ),
              const SizedBox(width: 16),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w500)),
            ],
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: Theme.of(context).primaryColor,
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutButton(AppStateProvider appState, AppLocalizations l10n, bool isDark) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () => appState.logout(),
        icon: const Icon(LucideIcons.logOut, size: 18),
        label: Text(l10n.logout, style: const TextStyle(fontWeight: FontWeight.bold)),
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.red,
          side: BorderSide(color: Colors.red.withOpacity(0.3)),
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }
}
