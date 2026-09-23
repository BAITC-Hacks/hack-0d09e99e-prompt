import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../data/models.dart';
import '../theme/tokens.dart';

/// 12 months of estimated demand + 2 months dashed forecast.
///
/// The bundle has no per-SKU monthly series yet, so the curve is the SKU's
/// monthly demand shaped by IEK brand seasonality. Replace with the API series.
class MiniChart extends StatelessWidget {
  const MiniChart({super.key, required this.bundle, required this.line});

  final Bundle bundle;
  final SkuLine line;

  @override
  Widget build(BuildContext context) {
    final hist = bundle.series.length > 12 ? bundle.series.sublist(bundle.series.length - 12) : bundle.series;
    final mean = hist.fold<double>(0, (s, p) => s + p.coef) / hist.length;
    final last = hist.last;
    // Next two months: reuse last year's coefficient for the same month.
    const order = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    final nextMonths = [
      for (var k = 1; k <= 2; k++) order[(order.indexOf(last.month) + k) % 12],
    ];
    double coefFor(String m) => bundle.series.lastWhere((p) => p.month == m, orElse: () => last).coef;

    final actual = [
      for (var i = 0; i < hist.length; i++) FlSpot(i.toDouble(), line.demandMonth * hist[i].coef / mean),
    ];
    final forecast = [
      actual.last,
      for (var k = 0; k < nextMonths.length; k++)
        FlSpot((hist.length + k).toDouble(), line.demandMonth * coefFor(nextMonths[k]) / mean),
    ];
    final labels = [...hist.map((p) => p.month), ...nextMonths];
    final maxY = [...actual, ...forecast].map((s) => s.y).reduce((a, b) => a > b ? a : b) * 1.15;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 150,
          child: LineChart(
            LineChartData(
              minY: 0,
              maxY: maxY <= 0 ? 1 : maxY,
              minX: 0,
              maxX: (labels.length - 1).toDouble(),
              gridData: const FlGridData(show: false),
              borderData: FlBorderData(show: false),
              lineTouchData: const LineTouchData(enabled: false),
              rangeAnnotations: RangeAnnotations(verticalRangeAnnotations: [
                if (line.stockoutNow)
                  VerticalRangeAnnotation(
                    x1: hist.length - 1.5,
                    x2: hist.length - 0.5,
                    color: Qc.critical.withValues(alpha: 0.14),
                  ),
              ]),
              titlesData: FlTitlesData(
                leftTitles: const AxisTitles(),
                rightTitles: const AxisTitles(),
                topTitles: const AxisTitles(),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 1,
                    reservedSize: 22,
                    getTitlesWidget: (v, meta) {
                      final i = v.round();
                      if (i < 0 || i >= labels.length || (i % 3 != 0 && i != labels.length - 1)) {
                        return const SizedBox.shrink();
                      }
                      return Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(labels[i], style: const TextStyle(fontSize: 10, color: Qc.inkMuted)),
                      );
                    },
                  ),
                ),
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: actual,
                  isCurved: true,
                  preventCurveOverShooting: true,
                  color: Qc.accent,
                  barWidth: 2.5,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Qc.accent.withValues(alpha: 0.18), Qc.accent.withValues(alpha: 0)],
                    ),
                  ),
                ),
                LineChartBarData(
                  spots: forecast,
                  isCurved: true,
                  preventCurveOverShooting: true,
                  color: Qc.accent,
                  barWidth: 2,
                  dashArray: [5, 4],
                  dotData: const FlDotData(show: false),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),
        Wrap(spacing: 14, runSpacing: 4, children: [
          const _Legend(color: Qc.accent, label: 'спрос'),
          const _Legend(color: Qc.accent, label: 'прогноз', dashed: true),
          if (line.stockoutNow) _Legend(color: Qc.critical.withValues(alpha: 0.35), label: 'нет на складе', block: true),
        ]),
        const SizedBox(height: 4),
        const Text('Оценка по сезонности IEK. Точный ряд по артикулу придёт из API.',
            style: TextStyle(fontSize: 11, color: Qc.inkMuted)),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend({required this.color, required this.label, this.dashed = false, this.block = false});

  final Color color;
  final String label;
  final bool dashed;
  final bool block;

  @override
  Widget build(BuildContext context) {
    final Widget mark = block
        ? Container(width: 10, height: 10, color: color)
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: dashed
                ? [
                    for (var i = 0; i < 3; i++)
                      Container(width: 4, height: 2, margin: const EdgeInsets.only(right: 2), color: color),
                  ]
                : [Container(width: 14, height: 2.5, color: color)],
          );
    return Row(mainAxisSize: MainAxisSize.min, children: [
      mark,
      const SizedBox(width: 6),
      Text(label, style: const TextStyle(fontSize: 11, color: Qc.inkSecondary)),
    ]);
  }
}
