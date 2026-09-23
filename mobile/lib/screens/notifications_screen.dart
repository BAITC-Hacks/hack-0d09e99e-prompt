import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/explain.dart';
import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'lock_screen_push.dart';
import 'sku_screen.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key, required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final order = ref.watch(orderProvider);
    void openOrder() {
      ref.read(urgencyFilterProvider.notifier).set(null);
      ref.read(tabProvider.notifier).go(1);
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Уведомления')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        children: [
          QCard(
            color: Qc.ink,
            borderColor: Qc.ink,
            onTap: () => Navigator.of(context).push(LockScreenPush.route(bundle)),
            child: const Row(children: [
              Icon(Icons.phone_iphone, color: Colors.white),
              SizedBox(width: 12),
              Expanded(
                child: Text('Демо: пуш на экране блокировки',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
              ),
              Icon(Icons.play_arrow_rounded, color: Colors.white),
            ]),
          ),
          if (order.status == OrderStatus.pendingApproval) ...[
            const SectionLabel('Ждёт решения'),
            _Notice(
              color: Qc.accent,
              bg: Qc.primaryFixed.withValues(alpha: 0.4),
              icon: Icons.fact_check_outlined,
              title: 'Заказ поставщику ${bundle.supplier} готов к утверждению',
              body: '${fmtQty(bundle.lines.length)} позиций · ${fmtQty(bundle.count(Urgency.critical))} критично · от ${order.sentBy}',
              cta: 'Рассмотреть',
              onTap: openOrder,
            ),
          ],
          const SectionLabel('Риск дефицита'),
          for (final l in bundle.alerts) ...[
            _Notice(
              color: Qc.critical,
              bg: Qc.criticalBg,
              icon: Icons.warning_amber_rounded,
              title: l.stockoutNow || l.daysLeft == 0
                  ? '${l.article}: нет на складе, поставка ~$leadDays дн.'
                  : '${l.article} закончится через ${l.daysLeft} дн., поставка ~$leadDays дн.',
              body: l.name,
              cta: 'Открыть артикул',
              onTap: () => Navigator.of(context).push(SkuScreen.route(bundle, l)),
            ),
            const SizedBox(height: 10),
          ],
          if (bundle.inbound.isNotEmpty) const SectionLabel('Поставки'),
          for (final i in bundle.inbound) ...[
            _Notice(
              color: Qc.inkSecondary,
              bg: Qc.card,
              icon: Icons.local_shipping_outlined,
              title: i.eta,
              body: '${fmtQty(i.positions)} позиций из заказа · ${fmtQty(i.qty)} ед.',
            ),
            const SizedBox(height: 10),
          ],
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({
    required this.color,
    required this.bg,
    required this.icon,
    required this.title,
    required this.body,
    this.cta,
    this.onTap,
  });

  final Color color;
  final Color bg;
  final IconData icon;
  final String title;
  final String body;
  final String? cta;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return QCard(
      onTap: onTap,
      color: bg,
      borderColor: color.withValues(alpha: 0.25),
      padding: const EdgeInsets.all(14),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700, color: Qc.ink, height: 1.3)),
            const SizedBox(height: 4),
            Text(body,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13, color: Qc.inkSecondary, height: 1.3)),
            if (cta != null) ...[
              const SizedBox(height: 8),
              Text('$cta →', style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 13)),
            ],
          ]),
        ),
      ]),
    );
  }
}
