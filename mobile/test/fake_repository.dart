import 'package:qor_mobile/data/models.dart';
import 'package:qor_mobile/data/repository.dart';

/// In-memory stand-in for the Qor API, only for widget tests.
class FakeQorRepository implements QorRepository {
  FakeQorRepository({this.hasBundle = true});

  final bool hasBundle;
  OrderStatus status = OrderStatus.pendingApproval;
  String? comment;
  User? _user;

  @override
  String get baseUrl => 'http://fake';

  @override
  Future<User> login(String username, String password) async {
    if (password.isEmpty) throw const ApiException('Неверный логин или пароль', status: 401);
    return _user = User(
      username: username,
      role: username == 'daniyar' ? UserRole.director : UserRole.buyer,
      name: username == 'daniyar' ? 'Данияр' : 'Айгерим',
      title: username == 'daniyar' ? 'Руководитель' : 'Менеджер закупа',
    );
  }

  @override
  void logout() => _user = null;

  @override
  Future<Bundle?> bundle() async => hasBundle ? Bundle.fromJson(bundleJson) : null;

  OrderState get _order => OrderState(
        id: 'iek-current',
        status: status,
        sentBy: 'Айгерим',
        sentAt: DateTime(2026, 9, 23, 12, 50),
        decidedBy: status == OrderStatus.approved || status == OrderStatus.returned ? _user?.name : null,
        decidedAt: status == OrderStatus.approved || status == OrderStatus.returned ? DateTime(2026, 9, 23, 13) : null,
        comment: comment,
      );

  @override
  Future<OrderState> currentOrder() async => _order;

  @override
  Future<OrderState> submit(String orderId) async {
    status = OrderStatus.pendingApproval;
    return _order;
  }

  @override
  Future<OrderState> approve(String orderId) async {
    if (status != OrderStatus.pendingApproval) {
      throw const ApiException('Утвердить можно только заказ на согласовании', status: 409);
    }
    status = OrderStatus.approved;
    return _order;
  }

  @override
  Future<OrderState> sendBack(String orderId, String text) async {
    status = OrderStatus.returned;
    comment = text;
    return _order;
  }

  @override
  Future<String> ask(String code, String question) async => 'Прогноз 1823 − остаток 0 → 4450 шт.';

  @override
  Future<List<SeriesPoint>> series(String code) async => const [];
}

Map<String, dynamic> _line(String code, String urgency, {double stock = 0}) => {
      'code': code,
      'article': 'ART-$code',
      'name': 'Позиция $code IEK',
      'unit': 'шт',
      'stock': stock,
      'stockoutNow': stock <= 0,
      'daysLeft': stock <= 0 ? 0 : 9,
      'inTransit': 0,
      'inTransitEta': null,
      'demandMonth': 1823.1,
      'recommended': 4450,
      'moq': 50,
      'urgency': urgency,
      'category': 'Прочее',
      'steps': [
        {'key': 'base', 'label': 'Прогноз CatBoost на следующий месяц', 'value': 1823.1},
        {'key': 'season', 'label': 'Страховой запас (0.5 × σ за 6 мес.)', 'delta': 2622.4},
        {'key': 'stock', 'label': 'Текущий остаток', 'delta': -stock},
        {'key': 'transit', 'label': 'В пути', 'delta': 0},
        {'key': 'moq', 'label': 'Округление до MOQ 50', 'value': 4450},
      ],
    };

final bundleJson = <String, dynamic>{
  'asOf': '2026-08-01',
  'asOfLabel': '08.2026',
  'supplier': 'IEK',
  'warehouse': 'Алматы',
  'model': {'name': 'demand_model.cbm'},
  'kpis': {'toOrder': 3, 'critical': 1, 'deficit': 1, 'inboundSku': 2, 'inboundQty': 500, 'skuTotal': 10},
  'lines': [_line('A1', 'critical'), _line('B2', 'warning', stock: 40), _line('C3', 'safe', stock: 900)],
  'alerts': [_line('A1', 'critical')],
  'anomalies': [],
  'series': [],
};
