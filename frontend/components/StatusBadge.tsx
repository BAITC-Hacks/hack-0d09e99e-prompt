import type { Urgency } from "@/data/catalog";

const labels: Record<Urgency, string> = {
  critical: "Критично",
  warning: "Скоро",
  safe: "Норма",
};

export function StatusBadge({ tone, pulse = false }: { tone: Urgency; pulse?: boolean }) {
  return (
    <span className="badge" data-tone={tone} data-pulse={pulse ? "true" : undefined}>
      <i />
      {labels[tone]}
    </span>
  );
}
