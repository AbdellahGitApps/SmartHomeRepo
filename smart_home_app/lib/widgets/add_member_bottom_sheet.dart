import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
    final nameController = TextEditingController(
      text: memberToEdit?.name ?? '',
    );
    bool faceEnrolled = memberToEdit?.faceEnrolled ?? false;
    String? faceImageData;
    String selectedRole = memberToEdit?.role ?? fixedRole ?? 'Family';
    String selectedAccessType = memberToEdit?.accessType ?? 'Always';
    String? validFrom = memberToEdit?.validFrom;
    String? validTo = memberToEdit?.validTo;
    String? timeStart = memberToEdit?.timeStart;
    String? timeEnd = memberToEdit?.timeEnd;
    int faceCount = memberToEdit?.faceCount ?? 0;
    bool saving = false;

    Future<void> pickFace(
      BuildContext sheetContext,
      void Function(void Function()) setModalState,
      ImageSource source,
    ) async {
      try {
        String? selectedFaceImageData;

        if (source == ImageSource.camera) {
          selectedFaceImageData = await _captureFaceImageData(context, isDark);
        } else {
          final image = await _picker.pickImage(
            source: ImageSource.gallery,
            imageQuality: 75,
          );

          if (image != null) {
            final bytes = await image.readAsBytes();
            final mimeType = image.mimeType ?? 'image/jpeg';
            selectedFaceImageData =
                'data:$mimeType;base64,${base64Encode(bytes)}';
          }
        }

        if (selectedFaceImageData != null && selectedFaceImageData.isNotEmpty) {
          faceImageData = selectedFaceImageData;
          setModalState(() => faceEnrolled = true);

          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  source == ImageSource.camera
                      ? 'Camera image captured. Face marked as enrolled.'
                      : 'Gallery image selected. Face marked as enrolled.',
                ),
              ),
            );
          }
        }
      } catch (error) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Face image selection failed: $error')),
          );
        }
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
                        textCapitalization: TextCapitalization.words,
                        inputFormatters: [
                          FilteringTextInputFormatter.allow(
                            RegExp(
                              r'[A-Za-z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]',
                            ),
                          ),
                        ],
                        decoration: InputDecoration(
                          labelText: l10n.memberName,
                          prefixIcon: const Icon(LucideIcons.user),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: ['Owner', 'Family', 'Guest', 'Worker', 'Child', 'Blocked'].contains(selectedRole) ? selectedRole : 'Family',
                        decoration: InputDecoration(
                          labelText: l10n.memberRole,
                          prefixIcon: const Icon(LucideIcons.shield),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                        items: ['Owner', 'Family', 'Guest', 'Worker', 'Child', 'Blocked']
                            .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                            .toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setModalState(() {
                              selectedRole = val;
                              if (val == 'Owner' || val == 'Family' || val == 'Blocked') {
                                selectedAccessType = 'Always';
                              } else if (val == 'Worker') {
                                selectedAccessType = 'Scheduled';
                              } else if (val == 'Guest') {
                                selectedAccessType = 'Temporary';
                              }
                            });
                          }
                        },
                      ),
                      const SizedBox(height: 16),
                      if (selectedRole == 'Blocked')
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.red.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(color: Colors.red.withOpacity(0.3)),
                          ),
                          child: const Row(
                            children: [
                              Icon(LucideIcons.ban, color: Colors.red),
                              SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  'Access Denied. This user will not be allowed to open any doors.',
                                  style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                                ),
                              ),
                            ],
                          ),
                        )
                      else ...[
                        DropdownButtonFormField<String>(
                          value: ['Always', 'Scheduled', 'Temporary'].contains(selectedAccessType) ? selectedAccessType : 'Always',
                          decoration: InputDecoration(
                            labelText: 'Access Type',
                            prefixIcon: const Icon(LucideIcons.clock),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          items: ['Always', 'Scheduled', 'Temporary']
                              .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                              .toList(),
                          onChanged: (val) {
                            if (val != null) setModalState(() => selectedAccessType = val);
                          },
                        ),
                        if (selectedAccessType == 'Scheduled') ...[
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: TextFormField(
                                  readOnly: true,
                                  decoration: InputDecoration(
                                    labelText: 'Start Time',
                                    prefixIcon: const Icon(LucideIcons.clock),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                  controller: TextEditingController(text: timeStart ?? ''),
                                  onTap: () async {
                                    final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
                                    if (time != null) setModalState(() => timeStart = "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}");
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: TextFormField(
                                  readOnly: true,
                                  decoration: InputDecoration(
                                    labelText: 'End Time',
                                    prefixIcon: const Icon(LucideIcons.clock),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                  controller: TextEditingController(text: timeEnd ?? ''),
                                  onTap: () async {
                                    final time = await showTimePicker(context: context, initialTime: TimeOfDay.now());
                                    if (time != null) setModalState(() => timeEnd = "${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}");
                                  },
                                ),
                              ),
                            ],
                          ),
                        ],
                        if (selectedAccessType == 'Temporary') ...[
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Expanded(
                                child: TextFormField(
                                  readOnly: true,
                                  decoration: InputDecoration(
                                    labelText: 'Start Date',
                                    prefixIcon: const Icon(LucideIcons.calendar),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                  controller: TextEditingController(text: validFrom ?? ''),
                                  onTap: () async {
                                    final date = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime(2020), lastDate: DateTime(2100));
                                    if (date != null) setModalState(() => validFrom = "${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}");
                                  },
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: TextFormField(
                                  readOnly: true,
                                  decoration: InputDecoration(
                                    labelText: 'End Date',
                                    prefixIcon: const Icon(LucideIcons.calendar),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
                                  ),
                                  controller: TextEditingController(text: validTo ?? ''),
                                  onTap: () async {
                                    final date = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime(2020), lastDate: DateTime(2100));
                                    if (date != null) setModalState(() => validTo = "${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}");
                                  },
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                      const SizedBox(height: 24),
                      const SizedBox(height: 24),
                      Row(
                        children: [
                          Text(
                            memberToEdit == null ? l10n.enrollFace : 'AI Face Enrollment',
                            style: TextStyle(
                              color: Colors.grey.shade600,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          if (memberToEdit != null) ...[
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Theme.of(context).primaryColor.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                'Faces: $faceCount',
                                style: TextStyle(
                                  color: Theme.of(context).primaryColor,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _faceButton(
                              context: context,
                              label: memberToEdit == null ? l10n.captureFromCamera : 'Add AI Face Sample',
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
                              label: memberToEdit == null ? l10n.pickFromGallery : 'Add from Gallery',
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

                                final validName = RegExp(
                                  r'^[A-Za-z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+(?:\s+[A-Za-z\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)*$',
                                ).hasMatch(name);

                                if (!validName) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text(
                                        'Member name must contain letters only.',
                                      ),
                                    ),
                                  );
                                  return;
                                }

                                setModalState(() => saving = true);

                                try {
                                  final actAccessType = selectedRole == 'Blocked' ? 'Always' : selectedAccessType;

                                  if (onSaveOverride != null) {
                                    await onSaveOverride(
                                      name,
                                      selectedRole,
                                      faceEnrolled,
                                    );
                                  } else if (memberToEdit != null) {
                                    await appState.updateFamilyMember(
                                      memberToEdit.id,
                                      name,
                                      selectedRole,
                                      faceEnrolled,
                                      faceImageData: faceImageData,
                                      accessType: actAccessType,
                                      validFrom: actAccessType == 'Temporary' ? validFrom : null,
                                      validTo: actAccessType == 'Temporary' ? validTo : null,
                                      timeStart: actAccessType == 'Scheduled' ? timeStart : null,
                                      timeEnd: actAccessType == 'Scheduled' ? timeEnd : null,
                                    );
                                  } else {
                                    await appState.addFamilyMember(
                                      name,
                                      selectedRole,
                                      faceEnrolled,
                                      faceImageData: faceImageData,
                                      accessType: actAccessType,
                                      validFrom: actAccessType == 'Temporary' ? validFrom : null,
                                      validTo: actAccessType == 'Temporary' ? validTo : null,
                                      timeStart: actAccessType == 'Scheduled' ? timeStart : null,
                                      timeEnd: actAccessType == 'Scheduled' ? timeEnd : null,
                                    );
                                  }

                                  if (!context.mounted || !sheetContext.mounted) return;

                                  if (Navigator.canPop(sheetContext)) {
                                    Navigator.pop(sheetContext);
                                  }
                                } catch (error) {
                                  if (!context.mounted) return;
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

  static Future<String?> _captureFaceImageData(
    BuildContext context,
    bool isDark,
  ) async {
    final capturedImage = await showDialog<XFile?>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => _FaceCaptureDialog(isDark: isDark),
    );

    if (capturedImage == null) return null;

    try {
      final bytes = await capturedImage.readAsBytes();
      return 'data:image/jpeg;base64,${base64Encode(bytes)}';
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Camera failed: $error')),
        );
      }
      return null;
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
              ? Colors.green.withValues(alpha: 0.08)
              : Colors.grey.withValues(alpha: 0.04),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: active ? Colors.green : Colors.grey.withValues(alpha: 0.18),
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

class _FaceCaptureDialog extends StatefulWidget {
  final bool isDark;

  const _FaceCaptureDialog({Key? key, required this.isDark}) : super(key: key);

  @override
  State<_FaceCaptureDialog> createState() => _FaceCaptureDialogState();
}

class _FaceCaptureDialogState extends State<_FaceCaptureDialog> {
  CameraController? _controller;
  List<CameraDescription> _cameras = [];
  CameraDescription? _selectedCamera;
  bool _switchingCamera = false;
  String? _cameraError;
  bool _isDisposed = false;
  bool _isCapturing = false;

  @override
  void initState() {
    super.initState();
    _initCameras();
  }

  Future<void> _initCameras() async {
    try {
      final cameras = await availableCameras();
      if (cameras.isEmpty) {
        throw Exception('No camera found.');
      }

      int cameraScore(CameraDescription camera) {
        final name = camera.name.toLowerCase();
        var score = 0;

        if (name.contains('ir') ||
            name.contains('infrared') ||
            name.contains('virtual') ||
            name.contains('obs') ||
            name.contains('screen')) {
          score += 100;
        }

        if (camera.lensDirection == CameraLensDirection.front) {
          score -= 10;
        }

        if (camera.lensDirection == CameraLensDirection.back) {
          score += 5;
        }

        return score;
      }

      _cameras = [...cameras]
        ..sort((a, b) => cameraScore(a).compareTo(cameraScore(b)));

      await _initCamera(_cameras.first);
    } catch (e) {
      if (!_isDisposed && mounted) {
        setState(() => _cameraError = e.toString());
      }
    }
  }

  Future<void> _initCamera(CameraDescription camera) async {
    if (_isDisposed) return;

    final oldController = _controller;

    final newController = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await newController.initialize();
      if (_isDisposed) {
        await newController.dispose();
        return;
      }
      if (mounted) {
        setState(() {
          _controller = newController;
          _selectedCamera = camera;
          _switchingCamera = false;
          _cameraError = null;
        });
      }
      await oldController?.dispose();
    } catch (e) {
      if (!_isDisposed && mounted) {
        setState(() {
          _cameraError = e.toString();
          _switchingCamera = false;
        });
      }
      await newController.dispose();
    }
  }

  Future<void> _switchCamera(CameraDescription camera) async {
    if (camera.name == _selectedCamera?.name) return;

    if (mounted) {
      setState(() {
        _switchingCamera = true;
        _cameraError = null;
      });
    }

    await _initCamera(camera);
  }

  @override
  void dispose() {
    _isDisposed = true;
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ready = _controller != null &&
        _controller!.value.isInitialized &&
        !_switchingCamera &&
        !_isCapturing;

    return Dialog(
      insetPadding: const EdgeInsets.all(24),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
      ),
      child: Container(
        width: 680,
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: widget.isDark ? const Color(0xFF1E293B) : Colors.white,
          borderRadius: BorderRadius.circular(22),
        ),
        child: SingleChildScrollView(
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
                    onPressed: _isCapturing ? null : () => Navigator.pop(context),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              if (_cameras.length > 1) ...[
                const SizedBox(height: 10),
                DropdownButtonFormField<CameraDescription>(
                  value: _selectedCamera,
                  isExpanded: true,
                  decoration: InputDecoration(
                    labelText: 'Camera',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  items: _cameras.map((camera) {
                    final label =
                        camera.name.trim().isEmpty ? 'Camera' : camera.name;
                    return DropdownMenuItem(
                      value: camera,
                      child: Text(label),
                    );
                  }).toList(),
                  onChanged: _switchingCamera || _isCapturing
                      ? null
                      : (camera) {
                          if (camera != null) {
                            _switchCamera(camera);
                          }
                        },
                ),
              ],
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  height: 360,
                  width: double.infinity,
                  color: Colors.black,
                  child: ready
                      ? CameraPreview(_controller!)
                      : const Center(
                          child: CircularProgressIndicator(),
                        ),
                ),
              ),
              if (_cameraError != null) ...[
                const SizedBox(height: 10),
                Text(
                  _cameraError!,
                  style: const TextStyle(
                    color: Colors.red,
                    fontSize: 12,
                  ),
                ),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: _isCapturing
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(LucideIcons.camera),
                  label: Text(_isCapturing ? 'Capturing...' : 'Capture'),
                  onPressed: ready
                      ? () async {
                          setState(() {
                            _isCapturing = true;
                          });
                          try {
                            final image = await _controller!.takePicture();
                            if (mounted) {
                              Navigator.pop(context, image);
                            }
                          } catch (error) {
                            if (mounted) {
                              setState(() {
                                _cameraError = error.toString();
                                _isCapturing = false;
                              });
                            }
                          }
                        }
                      : null,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
