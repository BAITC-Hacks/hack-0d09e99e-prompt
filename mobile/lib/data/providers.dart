import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'models.dart';
import 'repository.dart';

const currentOrderId = 'iek-current';

final repositoryProvider = Provider<QorRepository>((ref) => MockQorRepository());

final bundleProvider = FutureProvider<Bundle>((ref) => ref.watch(repositoryProvider).loadBundle());

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

class RoleController extends Notifier<Role> {
  @override
  Role build() => Role.director;

  void set(Role r) => state = r;
}

final roleProvider = NotifierProvider<RoleController, Role>(RoleController.new);

class OrderController extends Notifier<OrderState> {
  @override
  OrderState build() => OrderState(
        status: OrderStatus.pendingApproval,
        sentBy: Role.buyer.person,
        sentAt: DateTime(2026, 9, 23, 12, 50),
      );

  Future<void> approve() async {
    state = state.copyWith(busy: true);
    await ref.read(repositoryProvider).approveOrder(currentOrderId);
    state = state.copyWith(status: OrderStatus.approved, decidedAt: DateTime.now(), busy: false);
  }

  Future<void> sendBack(String comment) async {
    state = state.copyWith(busy: true);
    await ref.read(repositoryProvider).returnOrder(currentOrderId, comment);
    state = state.copyWith(
      status: OrderStatus.returned,
      decidedAt: DateTime.now(),
      comment: comment,
      busy: false,
    );
  }

  void resetDemo() => ref.invalidateSelf();
}

final orderProvider = NotifierProvider<OrderController, OrderState>(OrderController.new);
