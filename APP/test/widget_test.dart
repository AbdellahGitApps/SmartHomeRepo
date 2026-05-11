import 'package:flutter_test/flutter_test.dart';
import 'package:smart_home_app/main.dart';

void main() {
  testWidgets('Smart Home app starts', (WidgetTester tester) async {
    await tester.pumpWidget(const SmartHomeApp());

    expect(find.text('Smart Home Admin'), findsOneWidget);
  });
}