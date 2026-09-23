/// Russian-style number: thousands separated by a non-breaking space, comma decimals.
String fmtQty(num v) {
  final neg = v < 0;
  final a = v.abs();
  final whole = a >= 100 || a == a.roundToDouble();
  final raw = whole ? a.round().toString() : a.toStringAsFixed(1);
  final parts = raw.split('.');
  final i = parts[0];
  final buf = StringBuffer();
  for (var k = 0; k < i.length; k++) {
    if (k > 0 && (i.length - k) % 3 == 0) buf.write(' ');
    buf.write(i[k]);
  }
  final frac = parts.length > 1 ? ',${parts[1]}' : '';
  return '${neg ? '−' : ''}$buf$frac';
}

const _monthsGen = [
  'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
];
const _weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

String ruDate(DateTime d) => '${_weekdays[d.weekday - 1]}, ${d.day} ${_monthsGen[d.month - 1]}';

String hhmm(DateTime d) => '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';

String ddmm(DateTime d) => '${d.day.toString().padLeft(2, '0')}.${d.month.toString().padLeft(2, '0')}';
