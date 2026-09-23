import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:qor_mobile/data/models.dart';
import 'package:qor_mobile/data/providers.dart';
import 'package:qor_mobile/data/why.dart';
import 'package:qor_mobile/main.dart';
import 'package:qor_mobile/widgets/position_card.dart';

import 'fake_repository.dart';

Future<void> _boot(WidgetTester tester, FakeQorRepository repo) async {
  tester.view.physicalSize = const Size(1170, 2532);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(ProviderScope(
    overrides: [repositoryProvider.overrideWithValue(repo)],
    child: const QorApp(),
  ));
  await tester.pumpAndSettle();
}

Future<void> _scrollTo(WidgetTester tester, String text) =>
    tester.scrollUntilVisible(find.text(text), 300, scrollable: find.byType(Scrollable).last);

void main() {
  test('whyShort uses engine steps and skips the MOQ result', () {
    final line = Bundle.fromJson(bundleJson).lines.first;
    final text = whyShort(line);
    expect(text, contains('Прогноз CatBoost 1 823'));
    expect(text, contains('Страховой запас +2 622'));
    expect(text, isNot(contains('MOQ')));
  });

  testWidgets('director logs in, reviews and approves', (tester) async {
    final repo = FakeQorRepository();
    await _boot(tester, repo);

    expect(find.text('Войти'), findsOneWidget);
    await tester.tap(find.text('Руководитель · daniyar'));
    await tester.pumpAndSettle();
    expect(find.text('1 заказ ждёт вашего утверждения'), findsOneWidget);

    await tester.tap(find.text('Заказы'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(PositionCard).first);
    await tester.pumpAndSettle();
    expect(find.textContaining('остаток 0 → 4450'), findsOneWidget);
    await _scrollTo(tester, 'Спросить почему');
    await tester.tap(find.text('Спросить почему'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Почему так много?'));
    await tester.pumpAndSettle();
    expect(find.textContaining('остаток 0 → 4450'), findsOneWidget);
    await tester.pageBack();
    await tester.pumpAndSettle();
    await tester.pageBack();
    await tester.pumpAndSettle();

    await tester.tap(find.text('Утвердить'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Утвердить').last);
    await tester.pumpAndSettle();
    expect(repo.status, OrderStatus.approved);
    expect(find.text('Утверждено'), findsWidgets);
    await tester.pump(const Duration(seconds: 5)); // let the snackbar go away
    await tester.pumpAndSettle();

    await tester.tap(find.text('Уведомления'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Демо: пуш на экране блокировки'));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('ждёт утверждения'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Профиль'));
    await tester.pumpAndSettle();
    await _scrollTo(tester, 'Выйти');
    await tester.tap(find.text('Выйти'));
    await tester.pumpAndSettle();
    expect(find.text('Войти'), findsOneWidget);
  });

  testWidgets('buyer has no approve button and can resubmit a returned order', (tester) async {
    final repo = FakeQorRepository();
    await _boot(tester, repo);
    await tester.tap(find.text('Менеджер · aigerim'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Заказы'));
    await tester.pumpAndSettle();
    expect(find.text('Утвердить'), findsNothing);
    expect(find.text('Утверждает руководитель. Правки — на сайте.'), findsOneWidget);

    repo.status = OrderStatus.returned;
    await tester.fling(find.byType(Scrollable).last, const Offset(0, 400), 1000);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Отправить на согласование'));
    await tester.pumpAndSettle();
    expect(repo.status, OrderStatus.pendingApproval);
  });

  testWidgets('no 1C upload shows the empty state', (tester) async {
    await _boot(tester, FakeQorRepository(hasBundle: false));
    await tester.tap(find.text('Руководитель · daniyar'));
    await tester.pumpAndSettle();
    expect(find.text('Выгрузки 1С ещё нет'), findsOneWidget);
  });
}
