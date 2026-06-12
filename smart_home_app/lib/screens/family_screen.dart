import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import '../widgets/add_member_bottom_sheet.dart';

class FamilyScreen extends StatefulWidget {
  const FamilyScreen({super.key});

  @override
  State<FamilyScreen> createState() => _FamilyScreenState();
}

class _FamilyScreenState extends State<FamilyScreen> {
  String _searchQuery = '';

  Uint8List? _decodeMemberPhoto(String data) {
    final clean = data.trim();
    if (clean.isEmpty) return null;

    try {
      final payload = clean.contains(',') ? clean.split(',').last : clean;
      return base64Decode(payload);
    } catch (_) {
      return null;
    }
  }

  void _showMemberPhoto(FamilyMember member) {
    final bytes = _decodeMemberPhoto(member.photoData);
    if (bytes == null) return;

    showDialog<void>(
      context: context,
      builder: (context) {
        return Dialog(
          insetPadding: const EdgeInsets.all(24),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(24),
            child: Stack(
              children: [
                InteractiveViewer(
                  child: Image.memory(bytes, fit: BoxFit.contain),
                ),
                Positioned(
                  top: 8,
                  right: 8,
                  child: Material(
                    color: Colors.black.withOpacity(0.45),
                    shape: const CircleBorder(),
                    child: IconButton(
                      icon: const Icon(Icons.close, color: Colors.white),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _memberAvatar(FamilyMember member, bool isDark) {
    final hasPhoto = _decodeMemberPhoto(member.photoData) != null;

    final avatar = CircleAvatar(
      radius: 28,
      backgroundColor: Theme.of(context).primaryColor.withOpacity(0.1),
      child: Icon(
        LucideIcons.user,
        color: Theme.of(context).primaryColor,
        size: 24,
      ),
    );

    if (!hasPhoto) return avatar;

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => _showMemberPhoto(member),
        child: avatar,
      ),
    );
  }

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<AppStateProvider>(context, listen: false).loadFamilyMembers();
    });
  }

  Future<void> _confirmDeleteAllFamilyMembers(
    BuildContext context,
    AppStateProvider appState,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete All Family Members'),
        content: const Text('Delete all family members for this apartment?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text(
              'Delete All',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );

    if (ok != true) return;

    await appState.clearFamilyMembers();

    if (!context.mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('All family members deleted.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final canManage = appState.canManageFamily;

    final filteredMembers = appState.familyMembers.where((m) {
      if (_searchQuery.trim().isEmpty) return true;
      final q = _searchQuery.toLowerCase();
      return m.name.toLowerCase().contains(q) || m.role.toLowerCase().contains(q);
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.family),
        elevation: 0,
        centerTitle: true,
        actions: [
          IconButton(
            tooltip: 'Refresh',
            onPressed: appState.familyLoading
                ? null
                : appState.loadFamilyMembers,
            icon: appState.familyLoading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh, size: 20),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: appState.loadFamilyMembers,
        child: appState.familyLoading && appState.familyMembers.isEmpty
            ? const Center(child: CircularProgressIndicator())
            : appState.familyError != null && appState.familyMembers.isEmpty
            ? ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 120),
                  Icon(
                    LucideIcons.serverCrash,
                    size: 42,
                    color: Colors.red.withOpacity(0.8),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Family backend error:\n${appState.familyError}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.red),
                  ),
                ],
              )
            : appState.familyMembers.isEmpty
            ? ListView(
                padding: const EdgeInsets.all(24),
                children: const [
                  SizedBox(height: 120),
                  Center(child: Text('No family members from backend yet')),
                ],
              )
            : Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: 'Search by name or role...',
                        prefixIcon: const Icon(LucideIcons.search),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                        contentPadding: const EdgeInsets.symmetric(vertical: 0),
                      ),
                      onChanged: (val) {
                        setState(() {
                          _searchQuery = val;
                        });
                      },
                    ),
                  ),
                  Expanded(
                    child: ListView.separated(
                      padding: const EdgeInsets.all(24),
                      itemCount: filteredMembers.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 16),
                      itemBuilder: (context, index) {
                        final member = filteredMembers[index];
                        return _buildMemberCard(
                          context,
                          member,
                          l10n,
                          isDark,
                          canManage,
                        );
                      },
                    ),
                  ),
                ],
              ),
      ),
      floatingActionButton: canManage
          ? FloatingActionButton.extended(
              onPressed: () => AddMemberBottomSheet.show(
                context,
                l10n: l10n,
                appState: appState,
                isDark: isDark,
                fixedRole: 'Family',
              ),
              backgroundColor: Theme.of(context).primaryColor,
              icon: const Icon(LucideIcons.plus, color: Colors.white),
              label: Text(
                l10n.addMember,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            )
          : null,
    );
  }

  Widget _buildMemberCard(
    BuildContext context,
    FamilyMember member,
    AppLocalizations l10n,
    bool isDark,
    bool canManage,
  ) {
    Widget _buildAccessPolicySubtitle(FamilyMember m) {
      if (m.role == 'Blocked') {
        return const Row(
          children: [
            Icon(LucideIcons.ban, size: 12, color: Colors.red),
            SizedBox(width: 4),
            Text('Access Denied', style: TextStyle(color: Colors.red, fontSize: 13, fontWeight: FontWeight.bold)),
          ],
        );
      }

      if (m.accessType == 'Scheduled') {
        final timeStr = (m.timeStart != null && m.timeEnd != null && m.timeStart!.isNotEmpty && m.timeEnd!.isNotEmpty) 
            ? '${m.timeStart} - ${m.timeEnd}' 
            : 'Not set';
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(LucideIcons.clock, size: 12, color: Colors.blue),
                SizedBox(width: 4),
                Text('Scheduled Access', style: TextStyle(color: Colors.blue, fontSize: 13, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 2),
            Text(timeStr, style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        );
      }

      if (m.accessType == 'Temporary') {
        final dateStr = (m.validTo != null && m.validTo!.isNotEmpty) ? 'Until ${m.validTo}' : 'Not set';
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(LucideIcons.calendar, size: 12, color: Colors.orange),
                SizedBox(width: 4),
                Text('Temporary Access', style: TextStyle(color: Colors.orange, fontSize: 13, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 2),
            Text(dateStr, style: TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        );
      }

      return const Row(
        children: [
          Icon(LucideIcons.checkCircle2, size: 12, color: Colors.green),
          SizedBox(width: 4),
          Text('Always Access', style: TextStyle(color: Colors.green, fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      );
    }

    Widget memberInfo({required bool compact}) {
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _memberAvatar(member, isDark),
          SizedBox(width: compact ? 12 : 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  member.name,
                  maxLines: compact ? 2 : 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: compact ? 16 : 18,
                    fontWeight: FontWeight.bold,
                    decoration: member.isEnabled
                        ? null
                        : TextDecoration.lineThrough,
                    color: member.isEnabled ? null : Colors.grey,
                  ),
                ),
                Text(
                  member.role,
                  style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                ),
                const SizedBox(height: 4),
                _buildAccessPolicySubtitle(member),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 10,
                  runSpacing: 6,
                  crossAxisAlignment: WrapCrossAlignment.center,
                  children: [
                    _statusText(
                      icon: member.faceEnrolled
                          ? LucideIcons.checkCircle2
                          : LucideIcons.alertCircle,
                      text: member.faceEnrolled
                          ? '${l10n.faceEnrolled} (${member.faceCount})'
                          : l10n.noFace,
                      color: member.faceEnrolled ? Colors.green : Colors.orange,
                    ),
                    if (!member.isEnabled)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 7,
                          vertical: 3,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.red.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          l10n.disable,
                          style: const TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: Colors.red,
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
      );
    }

    Widget addedInfo({required bool compact}) {
      return ConstrainedBox(
        constraints: BoxConstraints(maxWidth: compact ? 210 : 220),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Padding(
              padding: const EdgeInsets.only(right: 30),
              child: Text(
                'Added',
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey.shade500,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(height: 4),
            Text(
              member.addedAtLabel,
              textAlign: TextAlign.end,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 12,
                color: isDark ? Colors.grey.shade300 : Colors.grey.shade700,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      );
    }

    Widget actionButton({
      required IconData icon,
      required String label,
      required Color color,
      required VoidCallback onPressed,
    }) {
      return TextButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 18, color: color),
        label: Text(label, style: TextStyle(color: color)),
      );
    }

    return LayoutBuilder(
      builder: (context, constraints) {
        final compact = constraints.maxWidth < 430;

        return Container(
          padding: EdgeInsets.all(compact ? 16 : 20),
          decoration: BoxDecoration(
            color: isDark ? const Color(0xFF1E293B) : Colors.white,
            borderRadius: BorderRadius.circular(24),
            border: isDark ? Border.all(color: const Color(0xFF334155)) : null,
            boxShadow: isDark
                ? []
                : [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
          ),
          child: Column(
            children: [
              if (compact) ...[
                memberInfo(compact: true),
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: addedInfo(compact: true),
                ),
              ] else
                Row(
                  children: [
                    Expanded(child: memberInfo(compact: false)),
                    const SizedBox(width: 12),
                    ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 210),
                      child: addedInfo(compact: false),
                    ),
                  ],
                ),
              if (canManage) ...[
                const SizedBox(height: 16),
                Divider(
                  color: isDark
                      ? const Color(0xFF334155)
                      : Colors.grey.shade200,
                  height: 1,
                ),
                const SizedBox(height: 8),
                Wrap(
                  alignment: WrapAlignment.spaceEvenly,
                  spacing: compact ? 10 : 24,
                  runSpacing: 4,
                  children: [
                    actionButton(
                      icon: LucideIcons.edit,
                      label: l10n.edit,
                      color: Theme.of(context).primaryColor,
                      onPressed: () {
                        AddMemberBottomSheet.show(
                          context,
                          l10n: l10n,
                          appState: Provider.of<AppStateProvider>(
                            context,
                            listen: false,
                          ),
                          isDark: isDark,
                          memberToEdit: member,
                          fixedRole: 'Family',
                        );
                      },
                    ),
                    actionButton(
                      icon: member.isEnabled
                          ? LucideIcons.userX
                          : LucideIcons.userCheck,
                      label: member.isEnabled ? l10n.disable : l10n.enable,
                      color: member.isEnabled ? Colors.orange : Colors.green,
                      onPressed: () {
                        Provider.of<AppStateProvider>(
                          context,
                          listen: false,
                        ).toggleFamilyMemberStatus(member.id);
                      },
                    ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _statusText({
    required IconData icon,
    required String text,
    required Color color,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color),
        const SizedBox(width: 6),
        Text(
          text,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: color,
          ),
        ),
      ],
    );
  }
}
