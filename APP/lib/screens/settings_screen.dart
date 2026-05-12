import 'package:flutter/material.dart';
import 'local_network_settings_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: ListView(
        children: [
          ListTile(
            leading: const Icon(Icons.wifi),
            title: const Text('Local Network Settings'),
            subtitle: const Text('Configure API and ESP32 URLs'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const LocalNetworkSettingsScreen(),
                ),
              );
            },
          ),
          const Divider(),
          const ListTile(
            leading: Icon(Icons.person),
            title: Text('Account Settings'),
            subtitle: Text('Coming soon'),
            enabled: false,
          ),
          const ListTile(
            leading: Icon(Icons.notifications),
            title: Text('Notifications'),
            subtitle: Text('Coming soon'),
            enabled: false,
          ),
          const ListTile(
            leading: Icon(Icons.devices),
            title: Text('Device Settings'),
            subtitle: Text('Coming soon'),
            enabled: false,
          ),
        ],
      ),
    );
  }
}
