import 'dart:io' show Platform;

import 'package:dio/dio.dart';

import 'models.dart';

/// Error with a message ready to show the user.
class ApiException implements Exception {
  const ApiException(this.message, {this.status});

  final String message;
  final int? status;

  bool get unauthorized => status == 401;

  @override
  String toString() => message;
}

/// Qor API used by the app. See mobile/README.md for the endpoint table.
abstract interface class QorRepository {
  String get baseUrl;
  Future<User> login(String username, String password);
  void logout();

  /// `null` when the engine has no calculation yet (404: nothing uploaded on the web).
  Future<Bundle?> bundle();
  Future<OrderState> currentOrder();
  Future<OrderState> submit(String orderId);
  Future<OrderState> approve(String orderId);
  Future<OrderState> sendBack(String orderId, String comment);
  Future<String> ask(String code, String question);
  Future<List<SeriesPoint>> series(String code);
}

class ApiQorRepository implements QorRepository {
  ApiQorRepository({String? baseUrl})
      : baseUrl = baseUrl ?? defaultBaseUrl,
        _dio = Dio(BaseOptions(
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 30),
        ));

  /// Override with `flutter run --dart-define=QOR_API=http://192.168.1.10:8000`.
  static String get defaultBaseUrl {
    const fromEnv = String.fromEnvironment('QOR_API');
    if (fromEnv.isNotEmpty) return fromEnv;
    return Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
  }

  @override
  final String baseUrl;
  final Dio _dio;
  String? _token;

  Options get _auth => Options(headers: {if (_token != null) 'Authorization': 'Bearer $_token'});

  Future<Map<String, dynamic>> _call(String method, String path, {Object? body}) async {
    try {
      final res = await _dio.request<Map<String, dynamic>>(
        '$baseUrl$path',
        data: body,
        options: _auth.copyWith(method: method),
      );
      return res.data ?? const {};
    } on DioException catch (e) {
      final res = e.response;
      if (res == null) {
        throw ApiException('Нет связи с $baseUrl. Запущен ли backend (uvicorn main:app)?');
      }
      throw ApiException(_detail(res.data) ?? 'Ошибка ${res.statusCode}', status: res.statusCode);
    }
  }

  static String? _detail(Object? data) {
    if (data is Map && data['detail'] != null) {
      final d = data['detail'];
      if (d is String) return d;
      if (d is List && d.isNotEmpty && d.first is Map) return '${(d.first as Map)['msg']}';
    }
    return null;
  }

  @override
  Future<User> login(String username, String password) async {
    final j = await _call('POST', '/v1/auth/login', body: {'username': username, 'password': password});
    _token = j['token'] as String?;
    return User.fromJson(j);
  }

  @override
  void logout() => _token = null;

  @override
  Future<Bundle?> bundle() async {
    try {
      return Bundle.fromJson(await _call('GET', '/v1/bundle'));
    } on ApiException catch (e) {
      if (e.status == 404) return null;
      rethrow;
    }
  }

  @override
  Future<OrderState> currentOrder() async => OrderState.fromJson(await _call('GET', '/v1/orders/current'));

  @override
  Future<OrderState> submit(String orderId) async =>
      OrderState.fromJson(await _call('POST', '/v1/orders/$orderId/submit'));

  @override
  Future<OrderState> approve(String orderId) async =>
      OrderState.fromJson(await _call('POST', '/v1/orders/$orderId/approve'));

  @override
  Future<OrderState> sendBack(String orderId, String comment) async =>
      OrderState.fromJson(await _call('POST', '/v1/orders/$orderId/return', body: {'comment': comment}));

  @override
  Future<String> ask(String code, String question) async {
    final j = await _call('POST', '/v1/sku/${Uri.encodeComponent(code)}/ask', body: {'question': question});
    return j['answer'] as String? ?? '';
  }

  @override
  Future<List<SeriesPoint>> series(String code) async {
    final j = await _call('GET', '/v1/sku/${Uri.encodeComponent(code)}/series');
    return ((j['points'] as List?) ?? const []).cast<Map<String, dynamic>>().map(SeriesPoint.fromJson).toList();
  }
}
