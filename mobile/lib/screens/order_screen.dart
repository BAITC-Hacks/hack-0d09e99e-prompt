import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import '../widgets/position_card.dart';
import 'sku_screen.dart';

class OrderScreen extends ConsumerWidget {
  const OrderScreen({super.key, required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final order = ref.watch(orderProvider).value;
    final filter = ref.watch(urgencyFilterProvider);
    final lines = filter == null ? bundle.sortedLines : bundle.sortedLines.where((l) => l.urgency == filter).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text('Заказ ${bundle.supplier}'),
        actions: [
          if (order != null) Padding(padding: const EdgeInsets.only(right: 16), child: OrderStatusChip(order.status)),
        ],
      ),
      bottomNavigationBar: _ApprovalBar(bundle: bundle),
      body: RefreshIndicator(
        onRefresh: () => ref.read(orderProvider.notifier).refresh(),
        child: CustomScrollView(physics: const AlwaysScrollableScrollPhysics(), slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
            sliver: SliverList.list(children: [
              Text(
                [
                  if (order?.sentBy != null) 'от ${order!.sentBy}',
                  if (order?.sentAt != null) '${ddmm(order!.sentAt!)} ${hhmm(order.sentAt!)}',
                  'склад ${bundle.warehouse}',
                  '${fmtQty(bundle.lines.length)} позиций',
                  'выгрузка ${bundle.asOfLabel}',
                ].join(' · '),
                style: const TextStyle(color: Qc.inkSecondary, height: 1.4),
              ),
              if (order?.status == OrderStatus.returned) ...[
                const SizedBox(height: 12),
                _Banner(
                  icon: Icons.undo,
                  color: Qc.critical,
                  bg: Qc.criticalBg,
                  title: 'Возвращён на доработку${order!.decidedBy != null ? ' · ${order.decidedBy}' : ''}',
                  text: order.comment ?? '',
                ),
              ],
              if (order?.status == OrderStatus.approved) ...[
                const SizedBox(height: 12),
                _Banner(
                  icon: Icons.check_circle,
                  color: Qc.safe,
                  bg: Qc.safeBg,
                  title: 'Утверждено${order!.decidedAt != null ? ' в ${hhmm(order.decidedAt!)}' : ''}'
                      '${order.decidedBy != null ? ' · ${order.decidedBy}' : ''}',
                  text: 'Менеджер выгружает заказ в 1С на сайте. Поставщику ничего не отправлено.',
                ),
              ],
              const SizedBox(height: 14),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(children: [
                  _FilterChip(
                    label: 'Все ${fmtQty(bundle.lines.length)}',
                    selected: filter == null,
                    onTap: () => ref.read(urgencyFilterProvider.notifier).set(null),
                  ),
                  for (final u in Urgency.values)
                    _FilterChip(
                      label: '${u.label} ${fmtQty(bundle.count(u))}',
                      urgency: u,
                      selected: filter == u,
                      onTap: () => ref.read(urgencyFilterProvider.notifier).set(u),
                    ),
                ]),
              ),
              const SizedBox(height: 12),
            ]),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            sliver: SliverList.separated(
              itemCount: lines.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (context, i) => PositionCard(
                line: lines[i],
                onTap: () => Navigator.of(context).push(SkuScreen.route(bundle, lines[i])),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}


class _FilterChip extends StatelessWidget {
  const _FilterChip({required this.label, required this.selected, required this.onTap, this.urgency});

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final Urgency? urgency;

  @override
  Widget build(BuildContext context) {
    final c = urgency == null ? null : urgencyColors(urgency!);
    final fg = selected ? Colors.white : (c?.fg ?? Qc.ink);
    final bg = selected ? (c?.fg ?? Qc.ink) : (c?.bg ?? Qc.card);
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Material(
        color: bg,
        shape: StadiumBorder(side: BorderSide(color: selected ? bg : (c?.border ?? Qc.line))),
        child: InkWell(
          customBorder: const StadiumBorder(),
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
            child: Text(label, style: TextStyle(color: fg, fontWeight: FontWeight.w600, fontSize: 13)),
          ),
        ),
      ),
    );
  }
}

class _Banner extends StatelessWidget {
  const _Banner({required this.icon, required this.color, required this.bg, required this.title, required this.text});

  final IconData icon;
  final Color color;
  final Color bg;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return QCard(
      color: bg,
      borderColor: color.withValues(alpha: 0.3),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: color),
        const SizedBox(width: 10),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.w700, color: color)),
            if (text.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(text, style: const TextStyle(color: Qc.ink, height: 1.35)),
            ],
          ]),
        ),
      ]),
    );
  }
}

class _ApprovalBar extends ConsumerWidget {
  const _ApprovalBar({required this.bundle});

  final Bundle bundle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(orderProvider).value?.status;
    final user = ref.watch(authProvider);
    final busy = ref.watch(orderBusyProvider);
    final director = user?.role == UserRole.director;
    final canDecide = director && status == OrderStatus.pendingApproval && !busy;
    final canSubmit = !director && (status == OrderStatus.draft || status == OrderStatus.returned) && !busy;

    final hint = switch (status) {
      OrderStatus.pendingApproval when !director => 'Утверждает руководитель. Правки — на сайте.',
      OrderStatus.draft || OrderStatus.returned when director => 'Ждём, пока менеджер отправит заказ.',
      _ => null,
    };

    return Container(
      decoration: const BoxDecoration(color: Qc.card, border: Border(top: BorderSide(color: Qc.line))),
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      child: SafeArea(
        top: false,
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Text('Итого', style: TextStyle(color: Qc.inkSecondary)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                '${fmtQty(bundle.lines.length)} позиций · ${fmtQty(bundle.count(Urgency.critical))} критично',
                textAlign: TextAlign.right,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontWeight: FontWeight.w700, color: Qc.ink),
              ),
            ),
          ]),
          if (hint != null) ...[
            const SizedBox(height: 6),
            Text(hint, style: const TextStyle(fontSize: 12, color: Qc.inkMuted)),
          ],
          const SizedBox(height: 10),
          if (director)
            Row(children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: canDecide ? () => _returnSheet(context, ref) : null,
                  child: const Text('Вернуть'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                flex: 2,
                child: FilledButton(
                  onPressed: canDecide ? () => _confirmApprove(context, ref) : null,
                  child: busy ? const _Spinner() : const Text('Утвердить'),
                ),
              ),
            ])
          else
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: canSubmit ? () => _submit(context, ref) : null,
                child: busy ? const _Spinner() : const Text('Отправить на согласование'),
              ),
            ),
        ]),
      ),
    );
  }

  void _report(BuildContext context, String? error, String success) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(error ?? success),
      backgroundColor: error == null ? null : Qc.critical,
    ));
  }

  Future<void> _submit(BuildContext context, WidgetRef ref) async {
    final error = await ref.read(orderProvider.notifier).submit();
    if (context.mounted) _report(context, error, 'Отправлено руководителю');
  }

  Future<void> _confirmApprove(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Утвердить заказ ${bundle.supplier}?'),
        content: const Text('Заказ не уйдёт поставщику — меняется только статус в системе, '
            'а выгрузку в 1С делает менеджер на сайте.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Отмена')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Утвердить')),
        ],
      ),
    );
    if (ok != true) return;
    final error = await ref.read(orderProvider.notifier).approve();
    if (context.mounted) _report(context, error, 'Утверждено. Менеджер может выгрузить в 1С');
  }

  Future<void> _returnSheet(BuildContext context, WidgetRef ref) async {
    final controller = TextEditingController();
    final comment = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.fromLTRB(16, 0, 16, MediaQuery.of(ctx).viewInsets.bottom + 16),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Вернуть на доработку', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          const Text('Менеджер увидит комментарий на сайте и поправит таблицу.',
              style: TextStyle(color: Qc.inkSecondary)),
          const SizedBox(height: 12),
          TextField(
            controller: controller,
            autofocus: true,
            minLines: 3,
            maxLines: 5,
            decoration: InputDecoration(
              hintText: 'Что исправить?',
              filled: true,
              fillColor: Qc.canvas,
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Qc.line)),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              style: FilledButton.styleFrom(backgroundColor: Qc.critical),
              onPressed: () {
                final text = controller.text.trim();
                if (text.isNotEmpty) Navigator.pop(ctx, text);
              },
              child: const Text('Отправить'),
            ),
          ),
        ]),
      ),
    );
    controller.dispose();
    if (comment == null) return;
    final error = await ref.read(orderProvider.notifier).sendBack(comment);
    if (context.mounted) _report(context, error, 'Возвращено менеджеру');
  }
}

class _Spinner extends StatelessWidget {
  const _Spinner();

  @override
  Widget build(BuildContext context) =>
      const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white));
}
