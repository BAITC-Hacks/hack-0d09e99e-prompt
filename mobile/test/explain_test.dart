import 'package:flutter_test/flutter_test.dart';
import 'package:qor_mobile/data/explain.dart';
import 'package:qor_mobile/data/format.dart';
import 'package:qor_mobile/data/models.dart';

void main() {
  test('fmtQty groups thousands with nbsp', () {
    expect(fmtQty(13429), '13 429');
    expect(fmtQty(12.5), '12,5');
    expect(fmtQty(-120), '−120');
  });

  test('breakdown reproduces engine number', () {
    final line = SkuLine.fromJson({
      'code': '130300779_', 'article': 'CTG12-063', 'name': 'Труба', 'unit': 'м',
      'stock': 64, 'stockoutNow': false, 'emptyMonths': 0, 'daysLeft': 0,
      'inTransit': 2000, 'inTransitEta': 'УТ-7848 до 01.10.2026',
      'demandMonth': 2918, 'demandWeek': 729.5, 'forecast8w': 7248.9, 'lostDemand': 0,
      'recommended': 5200, 'moq': 50, 'urgency': 'critical', 'category': 'Прочее',
    });
    final text = Explain(line, null, season: 1.2421, horizonWeeks: 8).breakdown;
    expect(text, contains('= 5 185'));
    expect(text, contains('MOQ 50 → 5 200'));
  });
}
