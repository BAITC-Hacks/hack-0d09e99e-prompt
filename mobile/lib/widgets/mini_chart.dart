import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../data/models.dart';
import '../theme/tokens.dart';

/// Monthly history from `GET /v1/sku/{code}/series`.
class MiniChart extends StatelessWidget {
  const MiniChart({super.key, required this.points, required this.stockoutNow});

  final List<SeriesPoint> points;
  final bool stockoutNow;

  @override
  Widget build(BuildContext context) {
    if (points.length < 2) {
      return const SizedBox(
        height: 72,
        child: Center(
          child: Text('Помесячной истории по артикулу в API пока нет',
              textAlign: TextAlign.center, style: TextStyle(color: Qc.inkMuted)),
        ),
      );
    }
    final pts = points.length > 12 ? points.sublist(points.length - 12) : points;
    final spots = [for (var i = 0; i < pts.length; i++) FlSpot(i.toDouble(), pts[i].value)];
    final maxY = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b) * 1.15;

    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(
        height: 150,
        child: LineChart(
          LineChartData(
            minY: 0,
            maxY: maxY <= 0 ? 1 : maxY,
            gridData: const FlGridData(show: false),
            borderData: FlBorderData(show: false),
            lineTouchData: const LineTouchData(enabled: false),
            rangeAnnotations: RangeAnnotations(verticalRangeAnnotations: [
              if (stockoutNow)
                VerticalRangeAnnotation(
                  x1: pts.length - 1.5,
                  x2: pts.length - 1.0,
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
                    if (i < 0 || i >= pts.length || (i % 3 != 0 && i != pts.length - 1)) {
                      return const SizedBox.shrink();
                    }
                    return Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text(pts[i].label, style: const TextStyle(fontSize: 10, color: Qc.inkMuted)),
                    );
                  },
                ),
              ),
            ),
            lineBarsData: [
              LineChartBarData(
                spots: spots,
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
            ],
          ),
        ),
      ),
      if (stockoutNow) ...[
        const SizedBox(height: 8),
        Row(children: [
          Container(width: 10, height: 10, color: Qc.critical.withValues(alpha: 0.35)),
          const SizedBox(width: 6),
          const Text('сейчас нет на складе', style: TextStyle(fontSize: 11, color: Qc.inkSecondary)),
        ]),
      ],
    ]);
  }
}
