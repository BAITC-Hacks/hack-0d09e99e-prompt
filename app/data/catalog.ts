import bundle from "./iek.json";

export type Urgency = "critical" | "warning" | "safe";

export type OrderLine = {
  code: string;
  article: string;
  name: string;
  unit: string;
  stock: number;
  stockoutNow: boolean;
  emptyMonths: number;
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
};

export const data = bundle;
export const kpis = bundle.kpis;
export const categories = bundle.categories;
export const alerts = bundle.alerts as OrderLine[];
export const lines = bundle.lines as OrderLine[];
export const anomalies = bundle.anomalies;
export const suppliers = bundle.suppliers;
export const series = bundle.series as { year: number; month: string; sales: number; coef: number }[];
export const featuredArticle = bundle.featuredArticle;

export function findSku(article: string) {
  const decoded = decodeURIComponent(article);
  return lines.find((l) => l.article === decoded || l.code === decoded) ?? lines[0];
}

export function formatQty(value: number) {
  return new Intl.NumberFormat("ru-KZ", { maximumFractionDigits: 1 }).format(value);
}
