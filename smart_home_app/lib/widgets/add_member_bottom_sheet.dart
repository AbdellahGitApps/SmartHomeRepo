
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';

class AddMemberBottomSheet {
  static final ImagePicker _picker = ImagePicker();

  static void show(
    BuildContext context, {
    required AppLocalizations l10n,
    required AppStateProvider appState,
    required bool isDark,
    FamilyMember? memberToEdit,
    Future<void> Function(String name, String role, bool faceEnrolled)?
    onSaveOverride,
    String? fixedRole,
  }) {
    final nameController = TextEditingController(text: memberToEdit?.name ?? '');
    bool faceEnrolled = memberToEdit?.faceEnrolled ?? false;
    bool saving = false;

    Future<void> pickFace(
      BuildContext sheetContext,
      void Function(void Function()) setModalState,
      ImageSource source,
    ) async {
      try {
        if (source == ImageSource.camera) {
          final captured = await _openCameraCaptureDialog(context, isDark);

          if (captured) {
            setModalState(() => faceEnrolled = true);

            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Camera image captured. Face marked as enrolled.'),
              ),
            );
          }

          return;
        }

        final image = await _picker.pickImage(
          source: ImageSource.gallery,
          imageQuality: 75,
          maxWidth: 1280,
        );

        if (image != null) {
          setModalState(() => faceEnrolled = true);

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Gallery image selected. Face marked as enrolled.'),
            ),
          );
        }
      } catch (error) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Face image selection failed: $error')),
        );
      }
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(context).viewInsets.bottom,
              ),
              child: Container(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.86,
                ),
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 24),
                decoration: BoxDecoration(
                  color: isDark ? const Color(0xFF1E293B) : Colors.white,
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(28),
                  ),
                ),
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Center(
                        child: Container(
                          width: 42,
                          height: 4,
                          margin: const EdgeInsets.only(bottom: 26),
                          decoration: BoxDecoration(
                            color: Colors.grey.withOpacity(0.3),
                            borderRadius: BorderRadius.circular(20),
                          ),
                        ),
                      ),
                      Text(
                        memberToEdit == null ? l10n.addMember : l10n.editMember,
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 24),
                      TextField(
                        controller: nameController,
                        decoration: InputDecoration(
                          labelText: l10n.memberName,
                          prefixIcon: const Icon(LucideIcons.user),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      InputDecorator(
                        decoration: InputDecoration(
                          labelText: l10n.memberRole,
                          prefixIcon: const Icon(LucideIcons.shield),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: const Text(
                          'Family',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      Text(
                        l10n.enrollFace,
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _faceButton(
                              context: context,
                              label: l10n.captureFromCamera,
                              icon: LucideIcons.camera,
                              active: faceEnrolled,
                              onTap: () => pickFace(
                                sheetContext,
                                setModalState,
                                ImageSource.camera,
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _faceButton(
                              context: context,
                              label: l10n.pickFromGallery,
                              icon: LucideIcons.image,
                              active: faceEnrolled,
                              onTap: () => pickFace(
                                sheetContext,
                                setModalState,
                                ImageSource.gallery,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 26),
                      ElevatedButton(
                        onPressed: saving
                            ? null
                            : () async {
                                final name = nameController.text.trim();

                                if (name.isEmpty) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Member name is required.'),
                                    ),
                                  );
                                  return;
                                }

                                setModalState(() => saving = true);

                                try {
                                  if (onSaveOverride != null) {
                                    await onSaveOverride(
                                      name,
                                      'Family',
                                      faceEnrolled,
                                    );
                                  } else if (memberToEdit != null) {
                                    await appState.updateFamilyMember(
                                      memberToEdit.id,
                                      name,
                                      'Family',
                                      faceEnrolled,
                                    );
                                  } else {
                                    await appState.addFamilyMember(
                                      name,
                                      'Family',
                                      faceEnrolled,
                                    );
                                  }

                                  if (Navigator.canPop(sheetContext)) {
                                    Navigator.pop(sheetContext);
                                  }
                                } catch (error) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(content: Text(error.toString())),
                                  );
                                } finally {
                                  setModalState(() => saving = false);
                                }
                              },
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 18),
                          backgroundColor: Theme.of(context).primaryColor,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        child: saving
                            ? const SizedBox(
                                height: 18,
                                width: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : Text(
                                l10n.saveMember,
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  fontSize: 16,
                                ),
                              ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  static Future<bool> _openCameraCaptureDialog(
    BuildContext context,
    bool isDark,
  ) async {
    CameraController? controller;

    try {
      final cameras = await availableCameras();

      if (cameras.isEmpty) {
        throw Exception('No camera found.');
      }

      final selectedCamera = cameras.firstWhere(
        (camera) => camera.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      );

      controller = CameraController(
        selectedCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      await controller.initialize();

      if (!context.mounted) {
        await controller.dispose();
        return false;
      }

      final result = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) {
          return Dialog(
            insetPadding: const EdgeInsets.all(24),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(22),
            ),
            child: Container(
              width: 640,
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                color: isDark ? const Color(0xFF1E293B) : Colors.white,
                borderRadius: BorderRadius.circular(22),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Capture Face',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      IconButton(
                        onPressed: () => Navigator.pop(dialogContext, false),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: SizedBox(
                      height: 360,
                      width: double.infinity,
                      child: CameraPreview(controller!),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(LucideIcons.camera),
                      label: const Text('Capture'),
                      onPressed: () async {
                        try {
                          await controller!.takePicture();
                          if (dialogContext.mounted) {
                            Navigator.pop(dialogContext, true);
                          }
                        } catch (_) {
                          if (dialogContext.mounted) {
                            Navigator.pop(dialogContext, false);
                          }
                        }
                      },
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      );

      await controller.dispose();
      return result == true;
    } catch (error) {
      await controller?.dispose();

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Camera failed. Check browser and Windows camera permission. $error'),
          ),
        );
      }

      return false;
    }
  }

  static Widget _faceButton({
    required BuildContext context,
    required String label,
    required IconData icon,
    required bool active,
    required VoidCallback onTap,
  }) {
    final color = active ? Colors.green : Colors.grey;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        height: 86,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: active
              ? Colors.green.withOpacity(0.08)
              : Colors.grey.withOpacity(0.04),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: active ? Colors.green : Colors.grey.withOpacity(0.18),
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(
              label,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.w700,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
