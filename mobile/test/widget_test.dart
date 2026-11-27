import 'package:andesbank/core/theme.dart';
import 'package:andesbank/core/widgets.dart';
import 'package:andesbank/features/auth/login_page.dart';
import 'package:andesbank/types/money.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('el ingreso con DNI corto no llama al API', () async {
    final model = LoginViewModel();
    model.initialize();
    final accepted = await model.submit('123', 'Clave.2026');
    expect(accepted, isFalse);
    expect(model.error, contains('8'));
  });

  testWidgets('el ojo de la parte superior cambia el saldo por una máscara', (tester) async {
    SharedPreferences.setMockInitialValues({});
    final visibility = BalanceVisibility();
    await visibility.initialize();
    await tester.pumpWidget(
      ChangeNotifierProvider<BalanceVisibility>.value(
        value: visibility,
        child: const MaterialApp(
          home: Scaffold(
            appBar: null,
            body: Column(children: [EyeButton(), BalanceText('11647.45')]),
          ),
        ),
      ),
    );
    expect(find.text('S/ 11,647.45'), findsOneWidget);
    await tester.tap(find.byType(IconButton));
    await tester.pump();
    expect(find.text('S/ ••••••'), findsOneWidget);
    expect(find.text('S/ 11,647.45'), findsNothing);
  });

  testWidgets('un saldo se puede forzar oculto sin leer la preferencia', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: BalanceText('10.00', hidden: true)));
    expect(find.text(Money.hidden), findsOneWidget);
  });
}
