import type { Urgency } from "@/app/data/catalog";

const map: Record<Urgency, { label: string; className: string; dot: string }> = {
  critical: {
    label: "Критично",
    className: "bg-status-critical-bg text-status-critical border-status-critical-border",
    dot: "bg-status-critical",
  },
  warning: {
    label: "Скоро",
    className: "bg-status-warning-bg text-status-warning border-status-warning-border",
    dot: "bg-status-warning",
  },
  safe: {
    label: "Норма",
    className: "bg-status-safe-bg text-status-safe border-status-safe-border",
    dot: "bg-status-safe",
  },
};

export function StatusBadge({ tone, pulse = false }: { tone: Urgency; pulse?: boolean }) {
  const item = map[tone];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${item.className}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${item.dot} ${pulse ? "animate-pulse" : ""}`} />
      {item.label}
    </span>
  );
}
