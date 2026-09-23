const MONTHS = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];

type Point = { year: number; month: string; sales: number; coef: number };

export function ForecastChart({
  asOf: asOfRaw,
  series,
  supplier,
}: {
  asOf: string;
  series: Point[];
  supplier: string;
}) {
  const asOf = new Date(asOfRaw || Date.now());
  const asOfYear = asOf.getFullYear();
  const asOfMonth = MONTHS[asOf.getMonth()];
  const cutoff = asOfYear * 12 + asOf.getMonth();

  const points = series.filter((s) => s.year * 12 + MONTHS.indexOf(s.month) <= cutoff);
  if (!points.length) {
    return (
      <figure className="card p-4 lg:col-span-8">
        <p className="text-sm text-ink-secondary">В выгрузке нет ряда сезонности.</p>
      </figure>
    );
  }
  const peak = series.reduce((a, b) => (b.coef > a.coef ? b : a));
  const values = points.map((p) => p.sales);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const w = 860;
  const h = 180;
  const x0 = 48;
  const y0 = 20;

  const xy = points.map((p, i) => {
    const x = x0 + (i / Math.max(points.length - 1, 1)) * w;
    const y = y0 + (1 - (p.sales - min) / (max - min || 1)) * h;
    return { ...p, x, y };
  });
  const path = xy.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const area = `${path} L${xy[xy.length - 1].x},${y0 + h} L${xy[0].x},${y0 + h} Z`;
  const now = xy.find((p) => p.year === asOfYear && p.month === asOfMonth) ?? xy[xy.length - 1];
  const ticks = [max, (max + min) / 2, min];

  return (
    <figure className="card flex flex-col p-4 lg:col-span-8">
      <header className="mb-3 flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-ink">Выручка {supplier} по месяцам</h2>
          <p className="text-xs text-ink-secondary">Файл «Сезонность ИЭК», ₸. Не модель — фактические суммы партнёра.</p>
        </div>
        <p className="inline-flex items-center gap-1 rounded-lg bg-status-warning-bg px-2 py-1 text-[11px] font-semibold text-status-warning">
          Пик года: {peak.month}, коэф. {peak.coef}
        </p>
      </header>
      <div className="h-72 overflow-hidden rounded-lg bg-surface-low/40 p-2">
        <svg viewBox="0 0 940 240" className="h-full w-full" role="img" aria-label="Помесячная выручка IEK">
          {ticks.map((t, i) => {
            const y = y0 + (i / 2) * h;
            return (
              <g key={`tick-${i}`}>
                <line x1={x0} x2={x0 + w} y1={y} y2={y} stroke="#E2E8F0" strokeDasharray="3 3" />
                <text x={x0 - 8} y={y + 3} textAnchor="end" fill="#94A3B8" fontSize="10">
                  {(t / 1_000_000).toFixed(0)}M
                </text>
              </g>
            );
          })}
          <path d={area} fill="#2563EB" fillOpacity="0.12" />
          <path d={path} fill="none" stroke="#004AC6" strokeWidth="2.5" strokeLinejoin="round" />
          <line x1={now.x} x2={now.x} y1="12" y2={y0 + h} stroke="#2563EB" strokeDasharray="4 4" />
          <rect x={now.x - 22} y="2" width="44" height="14" rx="3" fill="#2563EB" />
          <text x={now.x} y="12" textAnchor="middle" fill="#fff" fontSize="9" fontWeight="700">
            {now.month.toUpperCase()} {String(now.year).slice(2)}
          </text>
          {xy.filter((_, i) => i % 3 === 0).map((p) => (
            <text key={`${p.year}-${p.month}`} x={p.x} y="228" textAnchor="middle" fill="#64748B" fontSize="10">
              {p.month} {String(p.year).slice(2)}
            </text>
          ))}
        </svg>
      </div>
    </figure>
  );
}
