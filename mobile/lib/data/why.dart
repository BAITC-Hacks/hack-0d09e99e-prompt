import 'format.dart';
import 'models.dart';

/// One-line reason for a position card, built from the engine's own steps.
String whyShort(SkuLine l) {
  final parts = <String>[];
  for (final s in l.steps) {
    if (s.key == 'moq') continue; // the result is already shown as «Рек.»
    final name = _shortLabel(s.label);
    if (s.value != null) parts.add('$name ${fmtQty(s.value!)}');
    if (s.delta != null && s.delta != 0) parts.add('$name ${s.delta! > 0 ? '+' : ''}${fmtQty(s.delta!)}');
  }
  if (parts.isEmpty) parts.add('спрос ${fmtQty(l.demandMonth)} ${l.unit}/мес');
  return parts.join(' · ');
}

String _shortLabel(String label) {
  final head = label.split(' (').first.trim();
  final words = head.split(' ');
  return words.take(2).join(' ');
}
