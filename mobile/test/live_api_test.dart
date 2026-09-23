// Runs the real HTTP client against a running backend:
//   QOR_LIVE=http://127.0.0.1:8000 flutter test test/live_api_test.dart
// Needs a calculated workspace. Walks the order draft → pending_approval → approved.
// Skipped unless QOR_LIVE is set.
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:qor_mobile/data/models.dart';
import 'package:qor_mobile/data/repository.dart';

void main() {
  final base = Platform.environment['QOR_LIVE'];

  test('login, bundle, order, ask, roles', () async {
    final director = ApiQorRepository(baseUrl: base);
    final me = await director.login('daniyar', 'director');
    expect(me.role, UserRole.director);

    final bundle = await director.bundle();
    expect(bundle, isNotNull);
    expect(bundle!.lines, isNotEmpty);

    final buyer = ApiQorRepository(baseUrl: base);
    await buyer.login('aigerim', 'buyer');

    var order = await director.currentOrder();
    if (order.status != OrderStatus.pendingApproval) {
      order = await buyer.submit(order.id);
      expect(order.sentBy, 'Айгерим');
    }
    expect(order.status, OrderStatus.pendingApproval);

    final line = bundle.lines.first;
    expect(await director.ask(line.code, 'Почему так много?'), isNotEmpty);
    expect(await director.series(line.code), isA<List<SeriesPoint>>());

    await expectLater(buyer.approve(order.id), throwsA(isA<ApiException>().having((e) => e.status, 'status', 403)));

    final approved = await director.approve(order.id);
    expect(approved.status, OrderStatus.approved);
    expect(approved.decidedBy, me.name);
    await expectLater(director.approve(order.id), throwsA(isA<ApiException>().having((e) => e.status, 'status', 409)));

    await expectLater(
      ApiQorRepository(baseUrl: base).login('daniyar', 'wrong'),
      throwsA(isA<ApiException>().having((e) => e.status, 'status', 401)),
    );
  }, skip: base == null ? 'set QOR_LIVE to run against a backend' : false);
}
