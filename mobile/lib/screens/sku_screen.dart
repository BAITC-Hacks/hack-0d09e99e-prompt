import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import '../widgets/mini_chart.dart';
import 'chat_screen.dart';

class SkuScreen extends ConsumerWidget {
  const SkuScreen({super.key, required this.bundle, required this.line});

  final Bundle bundle;
  final SkuLine line;

  static Route<void> route(Bundle bundle, SkuLine line) =>
      MaterialPageRoute(builder: (_) => SkuScreen(bundle: bundle, line: line));

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final anomaly = bundle.anomalyFor(line.code);
    final answer = ref.watch(skuAnswerProvider(line.code));
    final series = ref.watch(skuSeriesProvider(line.code));

    return Scaffold(
      appBar: AppBar(title: Text(line.article, style: Qc.mono.copyWith(fontSize: 17, color: Qc.ink))),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        children: [
          Text(line.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Qc.ink, height: 1.25)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, runSpacing: 6, crossAxisAlignment: WrapCrossAlignment.center, children: [
            UrgencyBadge(line.urgency),
            Text('${line.code} · ${line.category} · MOQ ${fmtQty(line.moq)}',
                style: const TextStyle(color: Qc.inkSecondary, fontSize: 13)),
          ]),
          const SizedBox(height: 16),
          QCard(
            child: series.when(
              data: (p) => MiniChart(points: p, stockoutNow: line.stockoutNow),
              loading: () => const SizedBox(height: 72, child: Center(child: CircularProgressIndicator())),
              error: (e, _) => Text('$e', style: const TextStyle(color: Qc.inkMuted)),
            ),
          ),
          const SizedBox(height: 12),
          QCard(
            child: Row(children: [
              Expanded(
                child: StatTile(
                  label: 'На складе',
                  value: '${fmtQty(line.stock)} ${line.unit}',
                  valueColor: line.stockoutNow ? Qc.critical : null,
                ),
              ),
              Expanded(child: StatTile(label: 'В пути', value: fmtQty(line.inTransit))),
              Expanded(
                child: StatTile(label: 'Рек.', value: '${fmtQty(line.recommended)} ${line.unit}', valueColor: Qc.primary),
              ),
            ]),
          ),
          if (line.inTransitEta != null) ...[
            const SizedBox(height: 8),
            Text('Поставка: ${line.inTransitEta}', style: const TextStyle(fontSize: 13, color: Qc.inkSecondary)),
          ],
          const SizedBox(height: 12),
          InsightBox(
            title: 'Почему ${fmtQty(line.recommended)} ${line.unit}',
            text: answer.when(data: (t) => t, loading: () => 'Спрашиваю модель…', error: (e, _) => '$e'),
          ),
          if (anomaly != null) ...[
            const SizedBox(height: 12),
            QCard(
              color: Qc.anomalyBg,
              borderColor: Qc.anomalyBorder,
              child: Row(children: [
                const Icon(Icons.filter_alt_off_outlined, color: Qc.anomaly),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Исключена накладная ${anomaly.invoice} · ${fmtQty(anomaly.qty)} ${line.unit} · ${anomaly.day}',
                    style: const TextStyle(color: Qc.anomaly, fontWeight: FontWeight.w600),
                  ),
                ),
              ]),
            ),
          ],
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: () => Navigator.of(context).push(ChatScreen.route(bundle, line)),
            icon: const Icon(Icons.chat_bubble_outline),
            label: const Text('Спросить почему'),
          ),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: () {
              ref.read(tabProvider.notifier).go(1);
              Navigator.of(context).popUntil((r) => r.isFirst);
            },
            child: Text('К заказу ${bundle.supplier}'),
          ),
        ],
      ),
    );
  }
}
