import { Icon } from "./Icon";

type Props = {
  label: string;
  value: string;
  unit?: string;
  hint: string;
  accent: string;
  icon: string;
  chip?: string;
  chipClass?: string;
  valueClass?: string;
};

export function KpiCard({ label, value, unit, hint, accent, icon, chip, chipClass, valueClass }: Props) {
  return (
    <article className="card relative overflow-hidden p-4">
      <div className={`absolute inset-x-0 top-0 h-1 ${accent}`} />
      <header className="mb-2 flex items-start justify-between gap-2">
        <h2 className="label-caps">{label}</h2>
        {chip ? <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${chipClass}`}>{chip}</span> : null}
      </header>
      <p className="flex items-baseline gap-1">
        <strong className={`text-[30px] font-bold leading-none tracking-tight ${valueClass ?? "text-ink"}`}>{value}</strong>
        {unit ? <span className="text-base font-medium text-ink-muted">{unit}</span> : null}
      </p>
      <footer className="mt-3 flex items-center justify-between text-xs text-ink-secondary">
        <span>{hint}</span>
        <Icon name={icon} className="text-lg" />
      </footer>
    </article>
  );
}
