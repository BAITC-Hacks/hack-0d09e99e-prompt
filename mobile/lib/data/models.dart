enum Urgency {
  critical('Критично'),
  warning('Скоро'),
  safe('Норма');

  const Urgency(this.label);
  final String label;

  static Urgency parse(String? s) => switch (s) {
        'critical' => critical,
        'warning' => warning,
        _ => safe,
      };
}

double _d(Object? v) => (v as num?)?.toDouble() ?? 0;

class SkuLine {
  const SkuLine({
    required this.code,
    required this.article,
    required this.name,
    required this.unit,
    required this.stock,
    required this.stockoutNow,
    required this.emptyMonths,
    required this.daysLeft,
    required this.inTransit,
    required this.inTransitEta,
    required this.demandMonth,
    required this.demandWeek,
    required this.forecast8w,
    required this.lostDemand,
    required this.recommended,
    required this.moq,
    required this.urgency,
    required this.category,
  });

  factory SkuLine.fromJson(Map<String, dynamic> j) => SkuLine(
        code: j['code'] as String,
        article: j['article'] as String,
        name: (j['name'] as String).trim(),
        unit: j['unit'] as String? ?? 'шт',
        stock: _d(j['stock']),
        stockoutNow: j['stockoutNow'] as bool? ?? false,
        emptyMonths: (j['emptyMonths'] as num?)?.toInt() ?? 0,
        daysLeft: (j['daysLeft'] as num?)?.toInt() ?? 0,
        inTransit: _d(j['inTransit']),
        inTransitEta: j['inTransitEta'] as String?,
        demandMonth: _d(j['demandMonth']),
        demandWeek: _d(j['demandWeek']),
        forecast8w: _d(j['forecast8w']),
        lostDemand: _d(j['lostDemand']),
        recommended: _d(j['recommended']),
        moq: _d(j['moq']),
        urgency: Urgency.parse(j['urgency'] as String?),
        category: j['category'] as String? ?? 'Прочее',
      );

  final String code;
  final String article;
  final String name;
  final String unit;
  final double stock;
  final bool stockoutNow;
  final int emptyMonths;
  final int daysLeft;
  final double inTransit;
  final String? inTransitEta;
  final double demandMonth;
  final double demandWeek;
  final double forecast8w;
  final double lostDemand;
  final double recommended;
  final double moq;
  final Urgency urgency;
  final String category;
}

class Anomaly {
  const Anomaly({
    required this.date,
    required this.invoice,
    required this.article,
    required this.code,
    required this.name,
    required this.qty,
    required this.median,
    required this.reason,
  });

  factory Anomaly.fromJson(Map<String, dynamic> j) => Anomaly(
        date: j['date'] as String,
        invoice: j['invoice'] as String,
        article: j['article'] as String,
        code: j['code'] as String,
        name: j['name'] as String,
        qty: _d(j['qty']),
        median: _d(j['median']),
        reason: j['reason'] as String? ?? '',
      );

  final String date;
  final String invoice;
  final String article;
  final String code;
  final String name;
  final double qty;
  final double median;
  final String reason;

  String get day => date.length >= 10 ? date.substring(0, 10) : date;
}

class SeriesPoint {
  const SeriesPoint({required this.year, required this.month, required this.coef});

  factory SeriesPoint.fromJson(Map<String, dynamic> j) =>
      SeriesPoint(year: (j['year'] as num).toInt(), month: j['month'] as String, coef: _d(j['coef']));

  final int year;
  final String month;
  final double coef;
}

class Kpis {
  const Kpis({
    required this.toOrder,
    required this.critical,
    required this.deficit,
    required this.inboundSku,
    required this.inboundQty,
    required this.skuTotal,
  });

  factory Kpis.fromJson(Map<String, dynamic> j) => Kpis(
        toOrder: (j['toOrder'] as num).toInt(),
        critical: (j['critical'] as num).toInt(),
        deficit: (j['deficit'] as num).toInt(),
        inboundSku: (j['inboundSku'] as num).toInt(),
        inboundQty: _d(j['inboundQty']),
        skuTotal: (j['skuTotal'] as num).toInt(),
      );

  final int toOrder;
  final int critical;
  final int deficit;
  final int inboundSku;
  final double inboundQty;
  final int skuTotal;
}

class Inbound {
  const Inbound({required this.eta, required this.positions, required this.qty});
  final String eta;
  final int positions;
  final double qty;
}

/// Everything the mobile app needs for one supplier order. Mirrors app/data/iek.json.
class Bundle {
  Bundle({
    required this.asOf,
    required this.supplier,
    required this.warehouse,
    required this.horizonWeeks,
    required this.season,
    required this.kpis,
    required this.lines,
    required this.alerts,
    required this.anomalies,
    required this.series,
  });

  factory Bundle.fromJson(Map<String, dynamic> j) {
    List<T> list<T>(String k, T Function(Map<String, dynamic>) f) =>
        (j[k] as List).cast<Map<String, dynamic>>().map(f).toList();
    return Bundle(
      asOf: DateTime.parse(j['asOf'] as String),
      supplier: j['supplier'] as String,
      warehouse: j['warehouse'] as String,
      horizonWeeks: (j['horizonWeeks'] as num).toInt(),
      season: _d(j['seasonOct']),
      kpis: Kpis.fromJson(j['kpis'] as Map<String, dynamic>),
      lines: list('lines', SkuLine.fromJson),
      alerts: list('alerts', SkuLine.fromJson),
      anomalies: list('anomalies', Anomaly.fromJson),
      series: list('series', SeriesPoint.fromJson),
    );
  }

  final DateTime asOf;
  final String supplier;
  final String warehouse;
  final int horizonWeeks;
  final double season;
  final Kpis kpis;
  final List<SkuLine> lines;
  final List<SkuLine> alerts;
  final List<Anomaly> anomalies;
  final List<SeriesPoint> series;

  late final Map<String, SkuLine> _byCode = {for (final l in lines) l.code: l};

  late final Map<String, Anomaly> _anomalyByCode = () {
    final m = <String, Anomaly>{};
    for (final a in anomalies) {
      final prev = m[a.code];
      if (prev == null || a.qty > prev.qty) m[a.code] = a;
    }
    return m;
  }();

  late final List<SkuLine> sortedLines = [
    for (final u in Urgency.values) ...lines.where((l) => l.urgency == u),
  ];

  late final List<Inbound> inbound = () {
    final m = <String, Inbound>{};
    for (final l in lines.where((l) => l.inTransit > 0 && l.inTransitEta != null)) {
      final p = m[l.inTransitEta!];
      m[l.inTransitEta!] = Inbound(
        eta: l.inTransitEta!,
        positions: (p?.positions ?? 0) + 1,
        qty: (p?.qty ?? 0) + l.inTransit,
      );
    }
    return m.values.toList()..sort((a, b) => b.qty.compareTo(a.qty));
  }();

  SkuLine? byCode(String code) => _byCode[code];
  Anomaly? anomalyFor(String code) => _anomalyByCode[code];
  int count(Urgency u) => lines.where((l) => l.urgency == u).length;

  /// SKU whose stock runs out before a new IEK delivery could arrive.
  int get runsOutBeforeDelivery => lines.where((l) => l.urgency == Urgency.critical).length;
}

enum OrderStatus {
  draft('Черновик'),
  pendingApproval('На согласовании'),
  approved('Утверждено'),
  returned('На доработке');

  const OrderStatus(this.label);
  final String label;
}

class OrderState {
  const OrderState({
    required this.status,
    required this.sentBy,
    required this.sentAt,
    this.decidedAt,
    this.comment,
    this.busy = false,
  });

  final OrderStatus status;
  final String sentBy;
  final DateTime sentAt;
  final DateTime? decidedAt;
  final String? comment;
  final bool busy;

  OrderState copyWith({OrderStatus? status, DateTime? decidedAt, String? comment, bool? busy}) => OrderState(
        status: status ?? this.status,
        sentBy: sentBy,
        sentAt: sentAt,
        decidedAt: decidedAt ?? this.decidedAt,
        comment: comment ?? this.comment,
        busy: busy ?? this.busy,
      );
}

enum Role {
  director('Руководитель', 'Данияр'),
  buyer('Менеджер закупа', 'Айгерим');

  const Role(this.title, this.person);
  final String title;
  final String person;
}
