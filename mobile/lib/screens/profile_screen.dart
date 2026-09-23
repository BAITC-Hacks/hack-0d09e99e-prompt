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
    final role = ref.watch(roleProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Профиль')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        children: [
          const SectionLabel('Роль'),
          QCard(
            padding: EdgeInsets.zero,
            child: RadioGroup<Role>(
              groupValue: role,
              onChanged: (r) => ref.read(roleProvider.notifier).set(r ?? role),
              child: Column(children: [
                for (final r in Role.values)
                  RadioListTile<Role>(
                    value: r,
                    title: Text('${r.title} · ${r.person}'),
                    subtitle: Text(r == Role.director ? 'Утверждает или возвращает заказ' : 'Смотрит риски вне офиса'),
                  ),
              ]),
            ),
          ),
          const SectionLabel('Данные'),
          QCard(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _Row('Склад', bundle.warehouse),
              _Row('Поставщик', bundle.supplier),
              _Row('Выгрузка 1С', '${ddmm(bundle.asOf)}.${bundle.asOf.year}'),
              _Row('SKU в расчёте', fmtQty(bundle.kpis.skuTotal)),
              const _Row('Источник', 'демо-данные (API в работе)'),
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
              ref.read(orderProvider.notifier).resetDemo();
              ScaffoldMessenger.of(context)
                  .showSnackBar(const SnackBar(content: Text('Заказ снова на согласовании')));
            },
            icon: const Icon(Icons.restart_alt),
            label: const Text('Сбросить демо'),
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
          const Spacer(),
          Flexible(child: Text(value, textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w600))),
        ]),
      );
}
