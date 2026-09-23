import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'data/models.dart';
import 'data/providers.dart';
import 'data/repository.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
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
    if (ref.watch(authProvider) == null) return const LoginScreen();

    return ref.watch(bundleProvider).when(
          data: (b) => b == null ? const _Message.noUpload() : _Shell(bundle: b),
          loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
          error: (e, _) => _Message.error(e),
        );
  }
}

class _Message extends ConsumerWidget {
  const _Message.noUpload()
      : icon = Icons.upload_file,
        title = 'Выгрузки 1С ещё нет',
        text = 'Менеджер загружает Excel из 1С на сайте. После расчёта заказ появится здесь.',
        error = null;

  const _Message.error(Object this.error)
      : icon = Icons.cloud_off,
        title = 'Не удалось загрузить заказ',
        text = '$error';

  final IconData icon;
  final String title;
  final String text;
  final Object? error;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final expired = error is ApiException && (error as ApiException).unauthorized;
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Icon(icon, size: 44, color: Qc.inkMuted),
            const SizedBox(height: 12),
            Text(title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Qc.ink)),
            const SizedBox(height: 8),
            Text(error?.toString() ?? text, textAlign: TextAlign.center, style: const TextStyle(color: Qc.inkSecondary, height: 1.4)),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: expired
                  ? ref.read(authProvider.notifier).logout
                  : () => ref.invalidate(bundleProvider),
              child: Text(expired ? 'Войти снова' : 'Обновить'),
            ),
            if (!expired)
              TextButton(onPressed: ref.read(authProvider.notifier).logout, child: const Text('Выйти')),
          ]),
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
    final status = ref.watch(orderProvider).value?.status;
    final user = ref.watch(authProvider);
    final needsMe = switch (status) {
      OrderStatus.pendingApproval => user?.role == UserRole.director,
      OrderStatus.draft || OrderStatus.returned => user?.role == UserRole.buyer,
      _ => false,
    };
    final unread = bundle.alerts.length + (needsMe ? 1 : 0);

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
            icon: Badge(isLabelVisible: needsMe, child: const Icon(Icons.receipt_long_outlined)),
            selectedIcon: const Icon(Icons.receipt_long),
            label: 'Заказы',
          ),
          NavigationDestination(
            icon: Badge(isLabelVisible: unread > 0, label: Text('$unread'), child: const Icon(Icons.notifications_outlined)),
            selectedIcon: const Icon(Icons.notifications),
            label: 'Уведомления',
          ),
          const NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Профиль'),
        ],
      ),
    );
  }
}
