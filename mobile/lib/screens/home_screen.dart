import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/explain.dart';
import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'sku_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key, required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final role = ref.watch(roleProvider);
    final order = ref.watch(orderProvider);
    final tabs = ref.read(tabProvider.notifier);
    final firstAlert = bundle.alerts.isNotEmpty ? bundle.alerts.first : null;

    final (orderTitle, orderHint, orderColor) = switch (order.status) {
      OrderStatus.pendingApproval => (
          role == Role.director ? '1 заказ ждёт вашего утверждения' : 'Заказ ждёт утверждения руководителя',
          'IEK · от ${order.sentBy}, ${ddmm(order.sentAt)} ${hhmm(order.sentAt)}',
          Qc.accent,
        ),
      OrderStatus.approved => ('Заказ IEK утверждён', 'Менеджер может выгрузить его в 1С на сайте', Qc.safe),
      OrderStatus.returned => ('Заказ IEK на доработке', order.comment ?? '', Qc.critical),
      OrderStatus.draft => ('Заказ IEK в черновике', 'Менеджер ещё считает', Qc.inkSecondary),
    };

    return SafeArea(
      child: ListView(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
        children: [
          Row(children: [
            Container(
              width: 36,
              height: 36,
              alignment: Alignment.center,
              decoration: BoxDecoration(color: Qc.primary, borderRadius: BorderRadius.circular(10)),
              child: const Text('Q', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18)),
            ),
            const SizedBox(width: 10),
            const Text('Qor', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: Qc.ink)),
            const SizedBox(width: 12),
            Expanded(
              child: Align(
                alignment: Alignment.centerRight,
                child: Pill(label: '${role.title} · ${role.person}', fg: Qc.inkSecondary, bg: Qc.card, border: Qc.line, dot: false),
              ),
            ),
          ]),
          const SizedBox(height: 18),
          Text(ruDate(DateTime.now()),
              style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: Qc.ink, height: 1.1)),
          const SizedBox(height: 4),
          Text('${bundle.warehouse} · ${bundle.supplier} · данные 1С на ${ddmm(bundle.asOf)}.${bundle.asOf.year}',
              style: const TextStyle(color: Qc.inkSecondary)),
          const SizedBox(height: 18),
          _BigCard(
            icon: Icons.warning_amber_rounded,
            color: Qc.critical,
            bg: Qc.criticalBg,
            border: Qc.criticalBorder,
            value: fmtQty(bundle.runsOutBeforeDelivery),
            title: 'артикулов закончатся раньше поставки',
            hint: 'Остатка меньше, чем на $leadDays дн. — срок поставки IEK',
            onTap: () {
              ref.read(urgencyFilterProvider.notifier).set(Urgency.critical);
              tabs.go(1);
            },
          ),
          const SizedBox(height: 12),
          _BigCard(
            icon: Icons.fact_check_outlined,
            color: orderColor,
            bg: Qc.card,
            border: orderColor.withValues(alpha: 0.35),
            title: orderTitle,
            hint: orderHint,
            onTap: () {
              ref.read(urgencyFilterProvider.notifier).set(null);
              tabs.go(1);
            },
          ),
          const SizedBox(height: 12),
          _BigCard(
            icon: Icons.inventory_2_outlined,
            color: Qc.ink,
            bg: Qc.card,
            border: Qc.line,
            value: fmtQty(bundle.kpis.toOrder),
            title: 'позиций в заказе IEK',
            hint: '${fmtQty(bundle.kpis.inboundSku)} SKU уже в пути · ${fmtQty(bundle.kpis.inboundQty)} ед.',
            onTap: () => tabs.go(1),
          ),
          const SectionLabel('Сегодня'),
          QCard(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Column(children: [
              if (firstAlert != null)
                _FeedRow(
                  time: '13:04',
                  text: '${firstAlert.article}: остаток ${fmtQty(firstAlert.stock)} ${firstAlert.unit}'
                      '${firstAlert.inTransit > 0 ? ', в пути ${fmtQty(firstAlert.inTransit)}' : ', в пути нет'}',
                  color: Qc.critical,
                  onTap: () => Navigator.of(context).push(SkuScreen.route(bundle, firstAlert)),
                ),
              _FeedRow(
                time: hhmm(order.sentAt),
                text: 'Заказ IEK отправлен на согласование · ${order.sentBy}',
                color: Qc.accent,
                onTap: () => tabs.go(1),
              ),
              _FeedRow(
                time: '09:10',
                text: '${fmtQty(bundle.kpis.deficit)} SKU с пустым остатком в сентябре',
                color: Qc.inkMuted,
                last: true,
              ),
            ]),
          ),
        ],
      ),
    );
  }
}

class _BigCard extends StatelessWidget {
  const _BigCard({
    required this.icon,
    required this.color,
    required this.bg,
    required this.border,
    required this.title,
    required this.hint,
    this.value,
    this.onTap,
  });

  final IconData icon;
  final Color color;
  final Color bg;
  final Color border;
  final String? value;
  final String title;
  final String hint;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return QCard(
      onTap: onTap,
      color: bg,
      borderColor: border,
      padding: const EdgeInsets.all(18),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
          child: Icon(icon, color: color),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (value != null)
              Text(value!,
                  style: TextStyle(fontSize: 30, fontWeight: FontWeight.w800, color: color, height: 1.05)),
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Qc.ink, height: 1.3)),
            if (hint.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(hint, style: const TextStyle(fontSize: 13, color: Qc.inkSecondary, height: 1.3)),
            ],
          ]),
        ),
        const Icon(Icons.chevron_right, color: Qc.inkMuted),
      ]),
    );
  }
}

class _FeedRow extends StatelessWidget {
  const _FeedRow({required this.time, required this.text, required this.color, this.onTap, this.last = false});

  final String time;
  final String text;
  final Color color;
  final VoidCallback? onTap;
  final bool last;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(border: last ? null : const Border(bottom: BorderSide(color: Qc.line))),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(
            width: 48,
            child: Text(time,
                style: const TextStyle(fontSize: 13, color: Qc.inkMuted, fontFeatures: [FontFeature.tabularFigures()])),
          ),
          Container(
            width: 8,
            height: 8,
            margin: const EdgeInsets.only(top: 5, right: 10),
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 14, color: Qc.ink, height: 1.35))),
        ]),
      ),
    );
  }
}
