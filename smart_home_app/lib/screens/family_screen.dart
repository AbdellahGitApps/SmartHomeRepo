
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

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.family),
        elevation: 0,
        centerTitle: true,
        actions: [
          if (canManage && appState.familyMembers.isNotEmpty)
            TextButton.icon(
              onPressed: appState.familyLoading
                  ? null
                  : () => _confirmDeleteAllFamilyMembers(context, appState),
              icon: const Icon(
                LucideIcons.trash2,
                color: Colors.red,
                size: 18,
              ),
              label: const Text(
                'Delete All',
                style: TextStyle(
                  color: Colors.red,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
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
            : ListView.separated(
                padding: const EdgeInsets.all(24),
                itemCount: appState.familyMembers.length,
                separatorBuilder: (_, __) => const SizedBox(height: 16),
                itemBuilder: (context, index) {
                  final member = appState.familyMembers[index];
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
    return Container(
      padding: const EdgeInsets.all(20),
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
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.1),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  LucideIcons.user,
                  color: Theme.of(context).primaryColor,
                  size: 24,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      member.name,
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        decoration: member.isEnabled
                            ? null
                            : TextDecoration.lineThrough,
                        color: member.isEnabled ? null : Colors.grey,
                      ),
                    ),
                    Text(
                      'Family',
                      style: TextStyle(
                        color: Colors.grey.shade500,
                        fontSize: 13,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 12,
                      runSpacing: 6,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        _statusText(
                          icon: member.faceEnrolled
                              ? LucideIcons.checkCircle2
                              : LucideIcons.alertCircle,
                          text: member.faceEnrolled
                              ? l10n.faceEnrolled
                              : l10n.noFace,
                          color: member.faceEnrolled
                              ? Colors.green
                              : Colors.orange,
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
              const SizedBox(width: 12),
              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 210),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Added',
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey.shade500,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      member.addedAtLabel,
                      textAlign: TextAlign.end,
                      style: TextStyle(
                        fontSize: 12,
                        color: isDark ? Colors.grey.shade300 : Colors.grey.shade700,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (canManage) ...[
            const SizedBox(height: 16),
            Divider(
              color: isDark ? const Color(0xFF334155) : Colors.grey.shade200,
              height: 1,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                TextButton.icon(
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
                  icon: Icon(
                    LucideIcons.edit,
                    size: 18,
                    color: Theme.of(context).primaryColor,
                  ),
                  label: Text(
                    l10n.edit,
                    style: TextStyle(color: Theme.of(context).primaryColor),
                  ),
                ),
                TextButton.icon(
                  onPressed: () {
                    Provider.of<AppStateProvider>(
                      context,
                      listen: false,
                    ).toggleFamilyMemberStatus(member.id);
                  },
                  icon: Icon(
                    member.isEnabled
                        ? LucideIcons.userX
                        : LucideIcons.userCheck,
                    size: 18,
                    color: member.isEnabled ? Colors.orange : Colors.green,
                  ),
                  label: Text(
                    member.isEnabled ? l10n.disable : l10n.enable,
                    style: TextStyle(
                      color: member.isEnabled ? Colors.orange : Colors.green,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: () {
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: Text(l10n.deleteMember),
                        content: Text(l10n.removeMemberPrompt(member.name)),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.pop(ctx),
                            child: Text(l10n.cancel),
                          ),
                          TextButton(
                            onPressed: () async {
                              await Provider.of<AppStateProvider>(
                                context,
                                listen: false,
                              ).deleteFamilyMember(member.id);
                              if (ctx.mounted) Navigator.pop(ctx);
                            },
                            child: Text(
                              l10n.delete,
                              style: const TextStyle(color: Colors.red),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                  icon: const Icon(
                    LucideIcons.trash2,
                    size: 18,
                    color: Colors.red,
                  ),
                  label: Text(
                    l10n.delete,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
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
