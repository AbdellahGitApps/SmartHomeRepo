import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:smart_home_app/main.dart';
import 'package:smart_home_app/providers/app_state_provider.dart';

void main() {
  testWidgets('SmartHomeApp smoke test', (WidgetTester tester) async {
    // Build our app with the required provider and trigger a frame.
    await tester.pumpWidget(
      MultiProvider(
        providers: [ChangeNotifierProvider(create: (_) => AppStateProvider())],
        child: const SmartHomeApp(),
      ),
    );

    // Verify that the app renders without crashing.
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
