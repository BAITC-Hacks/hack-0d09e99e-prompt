import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qor_mobile/main.dart';
import 'package:qor_mobile/widgets/position_card.dart';

void main() {
  testWidgets('all screens render on an iPhone-sized screen', (tester) async {
    tester.view.physicalSize = const Size(1170, 2532);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(const ProviderScope(child: QorApp()));
    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 2)));
    await tester.pumpAndSettle();
    expect(find.text('Qor'), findsWidgets);

    await tester.tap(find.text('Заказы'));
    await tester.pumpAndSettle();
    expect(find.text('Утвердить'), findsOneWidget);

    await tester.tap(find.byType(PositionCard).first);
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Спросить почему'), 300, scrollable: find.byType(Scrollable).last);
    expect(find.text('Спросить почему'), findsOneWidget);

    await tester.tap(find.text('Спросить почему'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Почему так много?'));
    await tester.runAsync(() => Future<void>.delayed(const Duration(seconds: 1)));
    await tester.pumpAndSettle();
    expect(find.textContaining('Спрос'), findsWidgets);

    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.pageBack();
    await tester.pumpAndSettle();

    await tester.tap(find.text('Утвердить'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Утвердить').last);
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 600)));
    await tester.pumpAndSettle();
    expect(find.text('Утверждено'), findsWidgets);

    await tester.tap(find.text('Уведомления'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Демо: пуш на экране блокировки'));
    await tester.pumpAndSettle();
    expect(find.text('Нажмите на уведомление'), findsOneWidget);
    await tester.tap(find.textContaining('ждёт утверждения'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Профиль'));
    await tester.pumpAndSettle();
    await tester.scrollUntilVisible(find.text('Сбросить демо'), 300, scrollable: find.byType(Scrollable).last);
    expect(find.text('Сбросить демо'), findsOneWidget);
  });
}
