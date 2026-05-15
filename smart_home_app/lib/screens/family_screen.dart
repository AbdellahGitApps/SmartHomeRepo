import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';
import '../widgets/add_member_bottom_sheet.dart';

class FamilyScreen extends StatelessWidget {
  const FamilyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);
    bool isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.family),
        elevation: 0,
        centerTitle: true,
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(24),
        itemCount: appState.familyMembers.length,
        separatorBuilder: (_, __) => const SizedBox(height: 16),
        itemBuilder: (context, index) {
          final member = appState.familyMembers[index];
          return _buildMemberCard(context, member, l10n, isDark);
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => AddMemberBottomSheet.show(
          context,
          l10n: l10n,
          appState: appState,
          isDark: isDark,
        ),
        backgroundColor: Theme.of(context).primaryColor,
        icon: const Icon(LucideIcons.plus, color: Colors.white),
        label: Text(
          l10n.addMember,
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  Widget _buildMemberCard(
    BuildContext context,
    FamilyMember member,
    AppLocalizations l10n,
    bool isDark,
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
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(
              member.role == 'Admin' ? LucideIcons.shieldCheck : LucideIcons.user,
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
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Text(
                  member.role,
                  style: TextStyle(color: Colors.grey.shade500, fontSize: 13),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(
                      member.faceEnrolled ? LucideIcons.checkCircle2 : LucideIcons.alertCircle,
                      size: 14,
                      color: member.faceEnrolled ? Colors.green : Colors.orange,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      member.faceEnrolled ? l10n.faceEnrolled : l10n.noFace,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: member.faceEnrolled ? Colors.green : Colors.orange,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(LucideIcons.trash2, color: Colors.red, size: 20),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: Text(l10n.deleteMember),
                  content: Text(l10n.removeMemberPrompt(member.name)),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: Text(l10n.cancel)),
                    TextButton(
                      onPressed: () {
                        Provider.of<AppStateProvider>(context, listen: false)
                            .deleteFamilyMember(member.id);
                        Navigator.pop(ctx);
                      },
                      child: Text(l10n.delete, style: const TextStyle(color: Colors.red)),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
