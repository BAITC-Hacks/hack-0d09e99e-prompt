import 'package:flutter/material.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/why.dart';
import '../theme/tokens.dart';
import 'common.dart';

class PositionCard extends StatelessWidget {
  const PositionCard({super.key, required this.line, this.onTap});

  final SkuLine line;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return QCard(
      onTap: onTap,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Expanded(
              child: Text(line.article,
                  style: Qc.mono.copyWith(fontSize: 13, color: Qc.primary), overflow: TextOverflow.ellipsis),
            ),
            const SizedBox(width: 8),
            UrgencyBadge(line.urgency),
          ]),
          const SizedBox(height: 4),
          Text(line.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Qc.ink, height: 1.3)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: StatTile(
                label: 'Остаток',
                value: '${fmtQty(line.stock)} ${line.unit}',
                valueColor: line.stockoutNow ? Qc.critical : null,
              ),
            ),
            Expanded(child: StatTile(label: 'В пути', value: fmtQty(line.inTransit))),
            Expanded(child: StatTile(label: 'Рек.', value: '${fmtQty(line.recommended)} ${line.unit}', valueColor: Qc.primary)),
          ]),
          const SizedBox(height: 10),
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Padding(padding: EdgeInsets.only(top: 1), child: Icon(Icons.auto_awesome, size: 14, color: Qc.ai)),
            const SizedBox(width: 6),
            Expanded(
              child: Text(whyShort(line),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: Qc.inkSecondary, height: 1.35)),
            ),
          ]),
        ],
      ),
    );
  }
}
