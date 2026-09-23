/// Wire models for the Qor API (backend/main.py). Field names follow the JSON.
library;

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
double? _dn(Object? v) => (v as num?)?.toDouble();
DateTime? _date(Object? v) => v is String ? DateTime.tryParse(v)?.toLocal() : null;

/// One step of the engine's calculation, e.g. forecast, safety stock, stock, MOQ.
class CalcStep {
  const CalcStep({required this.key, required this.label, this.value, this.delta});

  factory CalcStep.fromJson(Map<String, dynamic> j) => CalcStep(
        key: j['key'] as String? ?? '',
        label: j['label'] as String? ?? '',
        value: _dn(j['value']),
        delta: _dn(j['delta']),
      );

  final String key;
  final String label;
  final double? value;
  final double? delta;
}

class SkuLine {
  const SkuLine({
    required this.code,
    required this.article,
    required this.name,
    required this.unit,
    required this.stock,
    required this.stockoutNow,
    required this.daysLeft,
    required this.inTransit,
    required this.inTransitEta,
    required this.demandMonth,
    required this.recommended,
    required this.moq,
    required this.urgency,
    required this.category,
    required this.steps,
  });

  factory SkuLine.fromJson(Map<String, dynamic> j) => SkuLine(
        code: j['code'] as String,
        article: j['article'] as String? ?? j['code'] as String,
        name: (j['name'] as String? ?? '').trim(),
        unit: j['unit'] as String? ?? 'шт',
        stock: _d(j['stock']),
        stockoutNow: j['stockoutNow'] as bool? ?? false,
        daysLeft: (j['daysLeft'] as num?)?.toInt() ?? 0,
        inTransit: _d(j['inTransit']),
        inTransitEta: j['inTransitEta'] as String?,
        demandMonth: _d(j['demandMonth']),
        recommended: _d(j['recommended']),
        moq: _d(j['moq']),
        urgency: Urgency.parse(j['urgency'] as String?),
        category: j['category'] as String? ?? 'Прочее',
        steps: ((j['steps'] as List?) ?? const []).cast<Map<String, dynamic>>().map(CalcStep.fromJson).toList(),
      );

  final String code;
  final String article;
  final String name;
  final String unit;
  final double stock;
  final bool stockoutNow;
  final int daysLeft;
  final double inTransit;
  final String? inTransitEta;
  final double demandMonth;
  final double recommended;
  final double moq;
  final Urgency urgency;
  final String category;
  final List<CalcStep> steps;

  /// The engine uses 9999 for "enough stock / no demand".
  bool get hasDaysLeft => daysLeft > 0 && daysLeft < 9999;
}

class Anomaly {
  const Anomaly({required this.invoice, required this.code, required this.qty, required this.date});

  factory Anomaly.fromJson(Map<String, dynamic> j) => Anomaly(
        invoice: j['invoice'] as String? ?? '',
        code: j['code'] as String? ?? '',
        qty: _d(j['qty']),
        date: j['date'] as String? ?? '',
      );

  final String invoice;
  final String code;
  final double qty;
  final String date;

  String get day => date.length >= 10 ? date.substring(0, 10) : date;
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
        toOrder: (j['toOrder'] as num?)?.toInt() ?? 0,
        critical: (j['critical'] as num?)?.toInt() ?? 0,
        deficit: (j['deficit'] as num?)?.toInt() ?? 0,
        inboundSku: (j['inboundSku'] as num?)?.toInt() ?? 0,
        inboundQty: _d(j['inboundQty']),
        skuTotal: (j['skuTotal'] as num?)?.toInt() ?? 0,
      );

  final int toOrder;
  final int critical;
  final int deficit;
  final int inboundSku;
  final double inboundQty;
  final int skuTotal;
}

/// `GET /v1/bundle` — the order the engine calculated from the latest 1C upload.
class Bundle {
  Bundle({
    required this.asOfLabel,
    required this.supplier,
    required this.warehouse,
    required this.modelName,
    required this.kpis,
    required this.lines,
    required this.alerts,
    required this.anomalies,
  });

  factory Bundle.fromJson(Map<String, dynamic> j) {
    List<T> list<T>(String k, T Function(Map<String, dynamic>) f) =>
        ((j[k] as List?) ?? const []).cast<Map<String, dynamic>>().map(f).toList();
    return Bundle(
      asOfLabel: j['asOfLabel'] as String? ?? j['asOf'] as String? ?? '—',
      supplier: j['supplier'] as String? ?? '—',
      warehouse: j['warehouse'] as String? ?? '—',
      modelName: (j['model'] as Map<String, dynamic>?)?['label'] as String? ??
          (j['model'] as Map<String, dynamic>?)?['name'] as String?,
      kpis: Kpis.fromJson(j['kpis'] as Map<String, dynamic>? ?? const {}),
      lines: list('lines', SkuLine.fromJson),
      alerts: list('alerts', SkuLine.fromJson),
      anomalies: list('anomalies', Anomaly.fromJson),
    );
  }

  final String asOfLabel;
  final String supplier;
  final String warehouse;
  final String? modelName;
  final Kpis kpis;
  final List<SkuLine> lines;
  final List<SkuLine> alerts;
  final List<Anomaly> anomalies;

  late final List<SkuLine> sortedLines = [
    for (final u in Urgency.values) ...lines.where((l) => l.urgency == u),
  ];

  late final Map<String, Anomaly> _anomalyByCode = () {
    final m = <String, Anomaly>{};
    for (final a in anomalies) {
      final prev = m[a.code];
      if (prev == null || a.qty > prev.qty) m[a.code] = a;
    }
    return m;
  }();

  Anomaly? anomalyFor(String code) => _anomalyByCode[code];
  int count(Urgency u) => lines.where((l) => l.urgency == u).length;
}

/// `GET /v1/sku/{code}/series` point. The backend has not fixed the shape yet,
/// so common key names are accepted.
class SeriesPoint {
  const SeriesPoint({required this.label, required this.value});

  factory SeriesPoint.fromJson(Map<String, dynamic> j) => SeriesPoint(
        label: '${j['label'] ?? j['month'] ?? j['period'] ?? ''}',
        value: _d(j['value'] ?? j['qty'] ?? j['sales'] ?? j['demand']),
      );

  final String label;
  final double value;
}

enum OrderStatus {
  draft('draft', 'Черновик'),
  pendingApproval('pending_approval', 'На согласовании'),
  approved('approved', 'Утверждено'),
  returned('returned', 'На доработке');

  const OrderStatus(this.wire, this.label);
  final String wire;
  final String label;

  static OrderStatus parse(String? s) => values.firstWhere((v) => v.wire == s, orElse: () => draft);
}

/// `GET /v1/orders/current`.
class OrderState {
  const OrderState({
    required this.id,
    required this.status,
    this.sentBy,
    this.sentAt,
    this.decidedBy,
    this.decidedAt,
    this.comment,
  });

  factory OrderState.fromJson(Map<String, dynamic> j) => OrderState(
        id: j['id'] as String? ?? 'iek-current',
        status: OrderStatus.parse(j['status'] as String?),
        sentBy: j['sentBy'] as String?,
        sentAt: _date(j['sentAt']),
        decidedBy: j['decidedBy'] as String?,
        decidedAt: _date(j['decidedAt']),
        comment: j['comment'] as String?,
      );

  final String id;
  final OrderStatus status;
  final String? sentBy;
  final DateTime? sentAt;
  final String? decidedBy;
  final DateTime? decidedAt;
  final String? comment;
}

enum UserRole { buyer, director }

class User {
  const User({required this.username, required this.role, required this.name, required this.title});

  factory User.fromJson(Map<String, dynamic> j) => User(
        username: j['username'] as String,
        role: j['role'] == 'director' ? UserRole.director : UserRole.buyer,
        name: j['name'] as String? ?? j['username'] as String,
        title: j['title'] as String? ?? '',
      );

  final String username;
  final UserRole role;
  final String name;
  final String title;
}
