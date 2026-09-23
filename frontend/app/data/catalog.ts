export type Urgency = "critical" | "warning" | "safe";

/** Шаг расчёта. Формула живёт в движке, клиенты только рисуют эти шаги. */
export type Step = {
  key: "base" | "season" | "stock" | "transit" | "moq";
  label: string;
  value?: number;
  delta?: number;
  factor?: number;
};

export type OrderLine = {
  code: string;
  article: string;
  name: string;
  unit: string;
  stock: number;
  stockoutNow: boolean;
  neverStocked: boolean;
  noStockRecord: boolean;
  emptyMonths: number;
  stockout12m: number;
  monthsUsed: number;
  daysLeft: number;
  inTransit: number;
  inTransitEta?: string | null;
  demandMonth: number;
  demandWeek: number;
  forecast8w: number;
  lostDemand: number;
  recommended: number;
  moq: number;
  urgency: Urgency;
  category: string;
  steps: Step[];
};

export type WorkspaceBundle = {
  asOf?: string;
  asOfLabel?: string;
  supplier?: string;
  warehouse?: string;
  horizonWeeks?: number;
  seasonOct?: number;
  monthEquiv?: number;
  seasonParts?: { month: string; share: number; coef: number }[];
  featuredArticle?: string;
  kpis: {
    toOrder: number;
    critical: number;
    deficit: number;
    excess: number;
    inboundSku: number;
    inboundQty: number;
    skuTotal: number;
    unverified?: number;
  };
  categories: { name: string; sku: number; toOrder: number; empty: number; share: number }[];
  alerts: OrderLine[];
  lines: OrderLine[];
  anomalies: {
    date: string;
    invoice: string;
    article: string;
    code: string;
    name: string;
    qty: number;
    median: number;
    reason: string;
  }[];
  suppliers: {
    name: string;
    role: string;
    sku: number;
    lead: string;
    inbound: number;
    inboundQty: number;
    toOrder: number;
  }[];
  series: { year: number; month: string; sales: number; coef: number }[];
};

export function metaFrom(bundle: WorkspaceBundle) {
  return {
    asOf: bundle.asOf ?? "",
    asOfLabel: bundle.asOfLabel ?? "нет выгрузки",
    supplier: bundle.supplier ?? "—",
    warehouse: bundle.warehouse ?? "—",
    horizonWeeks: bundle.horizonWeeks ?? 8,
    seasonOct: bundle.seasonOct ?? 1,
    monthEquiv: bundle.monthEquiv ?? 2,
    seasonParts: bundle.seasonParts ?? [],
  };
}

export function peakSeasonFrom(bundle: WorkspaceBundle) {
  const parts = bundle.seasonParts ?? [];
  if (!parts.length) return { month: "—", share: 0, coef: 1 };
  return parts.reduce((a, b) => (b.coef > a.coef ? b : a));
}

export function findSkuIn(bundle: WorkspaceBundle, codeOrArticle: string): OrderLine | undefined {
  return bundle.lines.find((l) => l.article === codeOrArticle || l.code === codeOrArticle);
}

export function formatQty(value: number) {
  return new Intl.NumberFormat("ru-KZ", { maximumFractionDigits: 1 }).format(value);
}

export function formatSigned(value: number) {
  if (value === 0) return "0"; // -0 иначе печатается как «+0»
  const s = formatQty(Math.abs(value));
  return value < 0 ? `−${s}` : `+${s}`;
}
