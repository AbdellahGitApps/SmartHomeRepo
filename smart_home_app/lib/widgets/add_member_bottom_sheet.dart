import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import '../services/permission_service.dart';

class AddMemberBottomSheet {
  static void show(
    BuildContext context, {
    required AppLocalizations l10n,
    required AppStateProvider appState,
    required bool isDark,
    VoidCallback? onAdded,
  }) {
    final nameCtrl = TextEditingController();
    String selectedRole = 'Family';
    bool faceEnrolled = false;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => Container(
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF0F172A) : Colors.white,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
          ),
          padding: EdgeInsets.only(
            top: 24,
            left: 24,
            right: 24,
            bottom: MediaQuery.of(context).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.grey.withOpacity(0.3),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                l10n.addMember,
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: nameCtrl,
                decoration: InputDecoration(
                  labelText: l10n.memberName,
                  prefixIcon: const Icon(LucideIcons.user),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                ),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: selectedRole,
                decoration: InputDecoration(
                  labelText: l10n.memberRole,
                  prefixIcon: const Icon(LucideIcons.shield),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
                ),
                items: ['Admin', 'Family', 'Guest']
                    .map((role) => DropdownMenuItem(value: role, child: Text(role)))
                    .toList(),
                onChanged: (val) => setModalState(() => selectedRole = val!),
              ),
              const SizedBox(height: 24),
              Text(l10n.enrollFace, style: const TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _buildEnrollButton(
                      icon: LucideIcons.camera,
                      label: l10n.captureFromCamera,
                      onTap: () async {
                        bool granted = await PermissionService.requestCameraPermission();
                        if (granted) {
                          setModalState(() => faceEnrolled = true);
                        } else {
                          if (context.mounted) _showPermissionDeniedDialog(context, l10n);
                        }
                      },
                      isActive: faceEnrolled,
                      isDark: isDark,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildEnrollButton(
                      icon: LucideIcons.image,
                      label: l10n.pickFromGallery,
                      onTap: () async {
                        bool granted = await PermissionService.requestGalleryPermission();
                        if (granted) {
                          setModalState(() => faceEnrolled = true);
                        } else {
                          if (context.mounted) _showPermissionDeniedDialog(context, l10n);
                        }
                      },
                      isActive: faceEnrolled,
                      isDark: isDark,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () {
                    if (nameCtrl.text.isNotEmpty) {
                      appState.addFamilyMember(nameCtrl.text, selectedRole, faceEnrolled);
                      if (onAdded != null) onAdded();
                      Navigator.pop(context);
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Theme.of(context).primaryColor,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: Text(
                    l10n.saveMember,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  static void _showPermissionDeniedDialog(BuildContext context, AppLocalizations l10n) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l10n.permissionDenied),
        content: Text(l10n.permissionDeniedPermanently),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.cancel)),
          TextButton(
            onPressed: () {
              PermissionService.openSettings();
              Navigator.pop(ctx);
            },
            child: Text(l10n.openSettings),
          ),
        ],
      ),
    );
  }

  static Widget _buildEnrollButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    required bool isActive,
    required bool isDark,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isActive
              ? const Color(0xFF22C55E).withOpacity(0.1)
              : (isDark ? const Color(0xFF1E293B) : Colors.grey.shade50),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isActive
                ? const Color(0xFF22C55E)
                : (isDark ? const Color(0xFF334155) : Colors.grey.shade200),
          ),
        ),
        child: Column(
          children: [
            Icon(icon, color: isActive ? const Color(0xFF22C55E) : Colors.grey, size: 24),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: isActive ? const Color(0xFF22C55E) : Colors.grey,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
