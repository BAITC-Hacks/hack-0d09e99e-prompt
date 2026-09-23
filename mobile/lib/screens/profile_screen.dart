import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key, required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider)!;
    final director = user.role == UserRole.director;
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        children: [
          QCard(
            child: Row(children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: Qc.primaryFixed,
                child: Text(user.name.characters.first,
                    style: const TextStyle(color: Qc.primary, fontWeight: FontWeight.w700, fontSize: 20)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(user.name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                  Text('${user.title} · ${user.username}', style: const TextStyle(color: Qc.inkSecondary)),
                ]),
              ),
            ]),
          ),
          const SizedBox(height: 8),
          Text(
            director ? 'Утверждаете или возвращаете заказ.' : 'Отправляете заказ на согласование. Правки — на сайте.',
            style: const TextStyle(color: Qc.inkSecondary),
          ),
          const SectionLabel('Данные'),
          QCard(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _Row('Склад', bundle.warehouse),
              _Row('Поставщик', bundle.supplier),
              _Row('Выгрузка 1С', bundle.asOfLabel),
              _Row('Позиций к заказу', fmtQty(bundle.kpis.toOrder)),
              if (bundle.modelName != null) _Row('Модель спроса', bundle.modelName!),
              _Row('Сервер', ref.read(repositoryProvider).baseUrl),
            ]),
          ),
          const SizedBox(height: 16),
          const Text(
            'Заказ никогда не уходит поставщику из приложения. «Утвердить» меняет статус, '
            'выгрузку в 1С делает менеджер на сайте.',
            style: TextStyle(color: Qc.inkSecondary, height: 1.4),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () {
              ref.invalidate(bundleProvider);
              ref.read(orderProvider.notifier).refresh();
            },
            icon: const Icon(Icons.refresh),
            label: const Text('Обновить данные'),
          ),
          const SizedBox(height: 10),
          OutlinedButton.icon(
            onPressed: () {
              ref.read(tabProvider.notifier).go(0);
              ref.read(authProvider.notifier).logout();
            },
            icon: const Icon(Icons.logout, color: Qc.critical),
            label: const Text('Выйти', style: TextStyle(color: Qc.critical)),
          ),
        ],
      ),
    );
  }
}

class _Row extends StatelessWidget {
  const _Row(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(children: [
          Text(label, style: const TextStyle(color: Qc.inkSecondary)),
          const SizedBox(width: 12),
          Expanded(child: Text(value, textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w600))),
        ]),
      );
}
