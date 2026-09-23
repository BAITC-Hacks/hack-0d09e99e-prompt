import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models.dart';
import 'repository.dart';

final repositoryProvider = Provider<QorRepository>((ref) => ApiQorRepository());

class AuthController extends Notifier<User?> {
  @override
  User? build() => null;

  Future<void> login(String username, String password) async {
    state = await ref.read(repositoryProvider).login(username, password);
  }

  void logout() {
    ref.read(repositoryProvider).logout();
    state = null;
  }
}

final authProvider = NotifierProvider<AuthController, User?>(AuthController.new);

final bundleProvider = FutureProvider<Bundle?>((ref) {
  ref.watch(authProvider);
  return ref.watch(repositoryProvider).bundle();
});

final skuAnswerProvider = FutureProvider.family<String, String>(
  (ref, code) => ref.watch(repositoryProvider).ask(code, 'Почему столько?'),
);

final skuSeriesProvider = FutureProvider.family<List<SeriesPoint>, String>(
  (ref, code) => ref.watch(repositoryProvider).series(code),
);

/// Shared order status. Polled so a decision made elsewhere (web, another phone) shows up.
class OrderController extends AsyncNotifier<OrderState> {
  static const pollEvery = Duration(seconds: 20);

  @override
  Future<OrderState> build() async {
    ref.watch(authProvider);
    final timer = Timer.periodic(pollEvery, (_) => refresh());
    ref.onDispose(timer.cancel);
    return ref.read(repositoryProvider).currentOrder();
  }

  /// Silent refresh: keeps the last known status on network errors.
  Future<void> refresh() async {
    final next = await AsyncValue.guard(ref.read(repositoryProvider).currentOrder);
    if (next.hasValue) state = next;
  }

  String get _id => state.value?.id ?? 'iek-current';

  Future<String?> submit() => _act((r) => r.submit(_id));
  Future<String?> approve() => _act((r) => r.approve(_id));
  Future<String?> sendBack(String comment) => _act((r) => r.sendBack(_id, comment));

  /// Returns an error message, or null on success.
  Future<String?> _act(Future<OrderState> Function(QorRepository r) call) async {
    ref.read(orderBusyProvider.notifier).set(true);
    try {
      state = AsyncData(await call(ref.read(repositoryProvider)));
      return null;
    } on ApiException catch (e) {
      if (e.unauthorized) ref.read(authProvider.notifier).logout();
      await refresh();
      return e.message;
    } finally {
      ref.read(orderBusyProvider.notifier).set(false);
    }
  }
}

final orderProvider = AsyncNotifierProvider<OrderController, OrderState>(OrderController.new);

class Flag extends Notifier<bool> {
  @override
  bool build() => false;

  void set(bool v) => state = v;
}

final orderBusyProvider = NotifierProvider<Flag, bool>(Flag.new);

class TabIndex extends Notifier<int> {
  @override
  int build() => 0;

  void go(int index) => state = index;
}

final tabProvider = NotifierProvider<TabIndex, int>(TabIndex.new);

class UrgencyFilter extends Notifier<Urgency?> {
  @override
  Urgency? build() => null;

  void set(Urgency? u) => state = u;
}

final urgencyFilterProvider = NotifierProvider<UrgencyFilter, Urgency?>(UrgencyFilter.new);
