import { Icon } from "./Icon";

type Tone = "primary" | "critical" | "warning" | "secondary";

type Props = {
  label: string;
  value: string;
  unit?: string;
  hint: string;
  tone?: Tone;
  icon: string;
  chip?: string;
};

export function KpiCard({ label, value, unit, hint, tone = "primary", icon, chip }: Props) {
  return (
    <article className="card kpi" data-tone={tone}>
      <header>
        <h2 className="caps">{label}</h2>
        {chip ? <span className="chip-critical">{chip}</span> : null}
      </header>
      <p>
        <strong>{value}</strong> {unit ? <em>{unit}</em> : null}
      </p>
      <footer>
        <span>{hint}</span>
        <Icon name={icon} />
      </footer>
    </article>
  );
}
