import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'data/models.dart';
import 'data/providers.dart';
import 'screens/home_screen.dart';
import 'screens/notifications_screen.dart';
import 'screens/order_screen.dart';
import 'screens/profile_screen.dart';
import 'theme/app_theme.dart';
import 'theme/tokens.dart';

void main() => runApp(const ProviderScope(child: QorApp()));

class QorApp extends StatelessWidget {
  const QorApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Qor',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: const _Root(),
      );
}

class _Root extends ConsumerWidget {
  const _Root();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ref.watch(bundleProvider).when(
          data: (b) => _Shell(bundle: b),
          loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
          error: (e, _) => Scaffold(
            body: Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.cloud_off, size: 40, color: Qc.inkMuted),
                  const SizedBox(height: 12),
                  Text('Не удалось загрузить данные\n$e', textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  FilledButton(onPressed: () => ref.invalidate(bundleProvider), child: const Text('Повторить')),
                ]),
              ),
            ),
          ),
        );
  }
}

class _Shell extends ConsumerWidget {
  const _Shell({required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tab = ref.watch(tabProvider);
    final pending = ref.watch(orderProvider.select((o) => o.status == OrderStatus.pendingApproval));
    final unread = bundle.alerts.length + (pending ? 1 : 0);

    return Scaffold(
      body: IndexedStack(index: tab, children: [
        HomeScreen(bundle: bundle),
        OrderScreen(bundle: bundle),
        NotificationsScreen(bundle: bundle),
        ProfileScreen(bundle: bundle),
      ]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: ref.read(tabProvider.notifier).go,
        destinations: [
          const NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Главная'),
          NavigationDestination(
            icon: Badge(isLabelVisible: pending, child: const Icon(Icons.receipt_long_outlined)),
            selectedIcon: const Icon(Icons.receipt_long),
            label: 'Заказы',
          ),
          NavigationDestination(
            icon: Badge(label: Text('$unread'), child: const Icon(Icons.notifications_outlined)),
            selectedIcon: const Icon(Icons.notifications),
            label: 'Уведомления',
          ),
          const NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Профиль'),
        ],
      ),
    );
  }
}
