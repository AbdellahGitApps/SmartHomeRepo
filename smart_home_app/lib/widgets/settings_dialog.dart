import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/app_localizations.dart';
import '../providers/app_state_provider.dart';

class SettingsDialog extends StatelessWidget {
  const SettingsDialog({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final appState = Provider.of<AppStateProvider>(context);

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.settings,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 24),

          // Theme Toggle
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(l10n.theme, style: Theme.of(context).textTheme.titleLarge),
              Row(
                children: [
                  Text(l10n.lightMode),
                  Switch(
                    value: appState.themeMode == ThemeMode.dark,
                    onChanged: (val) => appState.toggleTheme(val),
                    activeColor: Theme.of(context).primaryColor,
                  ),
                  Text(l10n.darkMode),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Language Toggle
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                l10n.language,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment<String>(value: 'en', label: Text('English')),
                  ButtonSegment<String>(value: 'ar', label: Text('العربية')),
                ],
                selected: {appState.locale.languageCode},
                onSelectionChanged: (Set<String> newSelection) {
                  appState.switchLanguage(newSelection.first);
                },
                style: ButtonStyle(
                  backgroundColor: WidgetStateProperty.resolveWith<Color>((
                    Set<WidgetState> states,
                  ) {
                    if (states.contains(WidgetState.selected)) {
                      return Theme.of(context).primaryColor.withOpacity(0.2);
                    }
                    return Colors.transparent;
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }
}
