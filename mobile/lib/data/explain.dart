import 'format.dart';
import 'models.dart';

/// Supplier lead time used by the engine for IEK (see docs/06-datasets.md).
const leadDays = 14;

/// Human-readable reasons built only from engine numbers. Once the backend
/// ships LLM justifications these become the offline fallback.
class Explain {
  const Explain(this.line, this.anomaly, {required this.season, required this.horizonWeeks});

  final SkuLine line;
  final Anomaly? anomaly;
  final double season;
  final int horizonWeeks;

  String get _u => line.unit;
  String get _season => season.toStringAsFixed(2).replaceAll('.', ',');
  double get _raw => line.forecast8w + line.lostDemand - line.stock - line.inTransit;

  /// One line under a position card.
  String get short {
    final p = ['${fmtQty(line.demandMonth)}/мес × сезон $_season'];
    if (line.lostDemand > 0) p.add('+${fmtQty(line.lostDemand)} упущ. спрос');
    if (line.inTransit > 0) p.add('−${fmtQty(line.inTransit)} в пути');
    if (anomaly != null) p.add('накладная ${fmtQty(anomaly!.qty)} исключена');
    return p.join(' · ');
  }

  /// Two sentences for the SKU card.
  String get blurb {
    final first = StringBuffer(
      '${fmtQty(line.recommended)} $_u — это $horizonWeeks недель спроса '
      '(${fmtQty(line.demandMonth)} $_u/мес) с октябрьской сезонностью ×$_season',
    );
    if (line.lostDemand > 0) first.write(' плюс ${fmtQty(line.lostDemand)} $_u упущенного спроса за месяцы без остатка');
    first.write(', за вычетом остатка ${fmtQty(line.stock)}');
    if (line.inTransit > 0) first.write(' и ${fmtQty(line.inTransit)} в пути');
    first.write('.');

    final String second;
    if (anomaly != null) {
      second = 'Разовая накладная ${anomaly!.invoice} на ${fmtQty(anomaly!.qty)} $_u (${anomaly!.day}) '
          'исключена — обычно берут ~${fmtQty(anomaly!.median)} $_u.';
    } else if (line.stockoutNow) {
      second = 'Сейчас товара нет на складе — без заказа продажи будут упущены.';
    } else if (line.daysLeft < leadDays) {
      second = 'Остатка хватит на ${line.daysLeft} дн., а поставка идёт ~$leadDays дн.';
    } else {
      second = 'Остатка хватит на ${line.daysLeft} дн., заказ держит запас на горизонт.';
    }
    return '$first $second';
  }

  String get breakdown {
    final b = StringBuffer(
      'Спрос ${fmtQty(line.demandWeek)} $_u/нед × $horizonWeeks нед × сезон $_season = ${fmtQty(line.forecast8w)}',
    );
    if (line.lostDemand > 0) b.write(' + ${fmtQty(line.lostDemand)} упущенного спроса');
    b.write(' − остаток ${fmtQty(line.stock)}');
    if (line.inTransit > 0) b.write(' − в пути ${fmtQty(line.inTransit)}');
    b.write(' = ${fmtQty(_raw)}. ');
    b.write(line.moq > 1
        ? 'Округлено вверх до кратности MOQ ${fmtQty(line.moq)} → ${fmtQty(line.recommended)} $_u.'
        : 'Итого ${fmtQty(line.recommended)} $_u.');
    if (anomaly != null) {
      b.write(' Накладная ${anomaly!.invoice} на ${fmtQty(anomaly!.qty)} $_u в спрос не вошла — это разовая отгрузка.');
    }
    return b.toString();
  }

  /// Mock chat answer until the backend /chat endpoint exists.
  String answer(String question) {
    final q = question.toLowerCase();
    if (q.contains('пути')) {
      return line.inTransit > 0
          ? 'Да: ${fmtQty(line.inTransit)} $_u, ${line.inTransitEta}. Это уже вычтено из рекомендации ${fmtQty(line.recommended)} $_u.'
          : 'Нет, в пути по этому артикулу ничего нет. Поэтому заказ считается только от остатка ${fmtQty(line.stock)} $_u.';
    }
    if (q.contains('как есть') || q.contains('утверд')) {
      return 'Заказ получит статус «Утверждено», менеджер выгрузит его в 1С. '
          'Поставщику автоматически ничего не уходит. По этой позиции ${fmtQty(line.recommended)} $_u '
          'закроют примерно $horizonWeeks недель спроса.';
    }
    if (q.contains('не заказ') || q.contains('если не')) {
      final days = line.stockoutNow ? 'уже сейчас' : 'через ${line.daysLeft} дн.';
      return 'Остаток закончится $days, а новая поставка идёт ~$leadDays дн. '
          'Упущенный спрос — около ${fmtQty(line.demandWeek)} $_u в неделю.';
    }
    return breakdown;
  }
}
