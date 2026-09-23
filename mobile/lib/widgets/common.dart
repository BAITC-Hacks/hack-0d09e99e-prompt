import 'package:flutter/material.dart';

import '../data/models.dart';
import '../theme/tokens.dart';

({Color fg, Color bg, Color border}) urgencyColors(Urgency u) => switch (u) {
      Urgency.critical => (fg: Qc.critical, bg: Qc.criticalBg, border: Qc.criticalBorder),
      Urgency.warning => (fg: Qc.warning, bg: Qc.warningBg, border: Qc.warningBorder),
      Urgency.safe => (fg: Qc.safe, bg: Qc.safeBg, border: Qc.safeBorder),
    };

class Pill extends StatelessWidget {
  const Pill({super.key, required this.label, required this.fg, required this.bg, this.border, this.dot = true});

  final String label;
  final Color fg;
  final Color bg;
  final Color? border;
  final bool dot;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
        border: border == null ? null : Border.all(color: border!),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (dot) ...[
            Container(width: 6, height: 6, decoration: BoxDecoration(color: fg, shape: BoxShape.circle)),
            const SizedBox(width: 6),
          ],
          Flexible(
            child: Text(label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: fg, fontSize: 12, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}

class UrgencyBadge extends StatelessWidget {
  const UrgencyBadge(this.urgency, {super.key});

  final Urgency urgency;

  @override
  Widget build(BuildContext context) {
    final c = urgencyColors(urgency);
    return Pill(label: urgency.label, fg: c.fg, bg: c.bg, border: c.border);
  }
}

class OrderStatusChip extends StatelessWidget {
  const OrderStatusChip(this.status, {super.key});

  final OrderStatus status;

  @override
  Widget build(BuildContext context) {
    final (fg, bg) = switch (status) {
      OrderStatus.draft => (Qc.inkSecondary, Qc.surfaceLow),
      OrderStatus.pendingApproval => (Qc.accent, Qc.primaryFixed),
      OrderStatus.approved => (Qc.safe, Qc.safeBg),
      OrderStatus.returned => (Qc.critical, Qc.criticalBg),
    };
    return Pill(label: status.label, fg: fg, bg: bg);
  }
}

class QCard extends StatelessWidget {
  const QCard({super.key, required this.child, this.onTap, this.padding = const EdgeInsets.all(16), this.color, this.borderColor});

  final Widget child;
  final VoidCallback? onTap;
  final EdgeInsets padding;
  final Color? color;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    final radius = BorderRadius.circular(Qc.radius);
    return Material(
      color: color ?? Qc.card,
      shape: RoundedRectangleBorder(borderRadius: radius, side: BorderSide(color: borderColor ?? Qc.line)),
      clipBehavior: Clip.antiAlias,
      child: InkWell(onTap: onTap, child: Padding(padding: padding, child: child)),
    );
  }
}

class StatTile extends StatelessWidget {
  const StatTile({super.key, required this.label, required this.value, this.valueColor});

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label.toUpperCase(),
            style: const TextStyle(fontSize: 10, letterSpacing: 0.6, fontWeight: FontWeight.w600, color: Qc.inkMuted)),
        const SizedBox(height: 2),
        Text(value,
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: valueColor ?? Qc.ink,
              fontFeatures: const [FontFeature.tabularFigures()],
            )),
      ],
    );
  }
}

class SectionLabel extends StatelessWidget {
  const SectionLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 20, 4, 8),
        child: Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: Qc.ink)),
      );
}

/// Block that marks model-written text (same "ai-insight" look as the web).
class InsightBox extends StatelessWidget {
  const InsightBox({super.key, required this.title, required this.text});

  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return QCard(
      color: Qc.aiBg,
      borderColor: Qc.aiBorder,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const Icon(Icons.auto_awesome, size: 16, color: Qc.ai),
            const SizedBox(width: 6),
            Text(title, style: const TextStyle(fontWeight: FontWeight.w700, color: Qc.ai)),
          ]),
          const SizedBox(height: 8),
          Text(text, style: const TextStyle(fontSize: 14, height: 1.45, color: Qc.ink)),
        ],
      ),
    );
  }
}
