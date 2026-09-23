import 'dart:convert';

import 'package:flutter/services.dart';

import 'explain.dart';
import 'models.dart';

/// Contract the mobile app expects from the backend. The mock below reads the
/// same bundle the web uses; swap it for an HTTP implementation once the API lands.
abstract interface class QorRepository {
  Future<Bundle> loadBundle();
  Future<String> ask(Bundle bundle, SkuLine line, String question);
  Future<void> approveOrder(String orderId);
  Future<void> returnOrder(String orderId, String comment);
}

class MockQorRepository implements QorRepository {
  @override
  Future<Bundle> loadBundle() async {
    final raw = await rootBundle.loadString('assets/data/iek.json');
    return Bundle.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  @override
  Future<String> ask(Bundle bundle, SkuLine line, String question) async {
    await Future<void>.delayed(const Duration(milliseconds: 700));
    return Explain(
      line,
      bundle.anomalyFor(line.code),
      season: bundle.season,
      horizonWeeks: bundle.horizonWeeks,
    ).answer(question);
  }

  @override
  Future<void> approveOrder(String orderId) => Future.delayed(const Duration(milliseconds: 400));

  @override
  Future<void> returnOrder(String orderId, String comment) => Future.delayed(const Duration(milliseconds: 400));
}
