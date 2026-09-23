#!/usr/bin/env python3
"""Build app/data/iek.json from partner 1C dumps. No invented SKUs or money."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/azamatomirtaj/Documents/IEK")
OUT = Path("/Users/azamatomirtaj/hack-0d09e99e-prompt/app/data/iek.json")

MONTHS = [
    "янв", "фев", "мар", "апр", "май", "июн",
    "июл", "авг", "сен", "окт", "ноя", "дек",
]
SEASON = {
    "янв": 0.7916, "фев": 0.8034, "мар": 0.7882, "апр": 0.9441,
    "май": 0.9031, "июн": 1.0653, "июл": 1.2176, "авг": 1.1800,
    "сен": 0.9706, "окт": 1.2421, "ноя": 1.0437, "дек": 1.0503,
}

CABLE = re.compile(r"кабел|utp|ftp|витая|itk|провод", re.I)
AUTO = re.compile(r"автомат|ва47|узо|выкл|контактор|пускател|диф", re.I)
LIGHT = re.compile(r"свет|дпа|дба|led|ламп|светиль", re.I)
PANEL = re.compile(r"щит|корпус|шкаф|ящик", re.I)


def classify(name: str) -> str:
    if CABLE.search(name or ""):
        return "СКС и кабель"
    if AUTO.search(name or ""):
        return "Автоматика"
    if LIGHT.search(name or ""):
        return "Светотехника"
    if PANEL.search(name or ""):
        return "Щитовое"
    return "Прочее"


def load_wide(path: Path, header_rows: int, name_col: int, code_col: int, unit_col: int | None):
    raw = pd.read_excel(path, header=None)
    header = raw.iloc[0].tolist()
    data = raw.iloc[header_rows:].copy()
    month_idx = []
    for i, h in enumerate(header):
        if i <= max(name_col, code_col, unit_col or 0):
            continue
        if h == "Итого" or pd.isna(h):
            continue
        month_idx.append(i)
    rows = []
    for _, r in data.iterrows():
        code = r.iloc[code_col]
        name = r.iloc[name_col]
        if pd.isna(code) or pd.isna(name) or str(name).strip().lower() == "итого":
            continue
        series = []
        for i in month_idx:
            v = pd.to_numeric(r.iloc[i], errors="coerce")
            series.append(None if pd.isna(v) else float(v))
        unit = str(r.iloc[unit_col]) if unit_col is not None and pd.notna(r.iloc[unit_col]) else "шт"
        rows.append({
            "code": str(code).strip(),
            "name": str(name).strip(),
            "unit": unit,
            "series": series,
            "months": [str(header[i]) for i in month_idx],
        })
    return rows


def median_positive(vals):
    xs = [v for v in vals if v is not None and v > 0]
    if not xs:
        return 0.0
    return float(np.median(xs))


def iqr_filter(vals):
    xs = [v for v in vals if v is not None and v > 0]
    if len(xs) < 4:
        return xs
    q1, q3 = np.percentile(xs, [25, 75])
    iqr = q3 - q1
    hi = q3 + 1.5 * iqr
    return [v for v in xs if v <= hi]


def ceil_moq(qty: float, moq: float) -> int:
    if qty <= 0:
        return 0
    m = max(moq, 1)
    return int(math.ceil(qty / m) * m)


def main():
    sales = load_wide(
        ROOT / "Ежемесячные продажи в количественном выражении за последние 2 года.xlsx",
        header_rows=2, name_col=0, code_col=1, unit_col=None,
    )
    stock = load_wide(
        ROOT / "Ежемесячные остатки продукции за последние 2 года  ИЭК.xlsx",
        header_rows=3, name_col=0, code_col=2, unit_col=1,
    )
    moq_df = pd.read_excel(ROOT / "MOQ  ИЭК.xlsx")
    moq_map = {}
    art_map = {}
    for _, r in moq_df.iterrows():
        code = str(r["Код 1с"]).strip()
        moq_map[code] = float(r["Мин. разр. к отгр."]) if pd.notna(r["Мин. разр. к отгр."]) else 1.0
        art_map[code] = str(r["Артикул поставщика"]).strip() if pd.notna(r["Артикул поставщика"]) else code

    tr = pd.read_excel(ROOT / "Путь ИЭК 22.09.2026.xlsx")
    transit = defaultdict(lambda: {"qty": 0.0, "etas": []})
    eta_re = re.compile(r"поступление до\s*(\d{2}\.\d{2}\.\d{4})")
    doc_re = re.compile(r"(УТ-\d+)")
    for col in tr.columns[3:]:
        eta = eta_re.search(str(col))
        doc = doc_re.search(str(col))
        label = f"{doc.group(1) if doc else 'УТ'} до {eta.group(1) if eta else '?'}"
        for _, r in tr.iterrows():
            qty = pd.to_numeric(r[col], errors="coerce")
            if pd.isna(qty) or qty <= 0 or pd.isna(r["Код 1с"]):
                continue
            code = str(r["Код 1с"]).strip()
            transit[code]["qty"] += float(qty)
            transit[code]["etas"].append(label)
            if pd.notna(r.get("Артикул ИЭК")):
                art_map[code] = str(r["Артикул ИЭК"]).strip()

    stock_by = {s["code"]: s for s in stock}
    sales_by = {s["code"]: s for s in sales}

    oct_coef = SEASON["окт"]
    lines = []
    for code, s in sales_by.items():
        st = stock_by.get(code)
        series = s["series"]
        cleaned = iqr_filter(series)
        demand_month = float(np.median(cleaned)) if cleaned else 0.0
        last_stock = None
        empty_months = 0
        if st:
            empty_months = sum(1 for v in st["series"] if v is None)
            for v in reversed(st["series"]):
                if v is not None:
                    last_stock = v
                    break
        stock_now = 0.0 if last_stock is None else last_stock
        stockout_now = last_stock is None
        in_tr = transit[code]["qty"]
        eta = "; ".join(dict.fromkeys(transit[code]["etas"])) or None
        forecast_8w = demand_month * 2 * oct_coef
        lost = demand_month * 0.5 if stockout_now and demand_month > 0 else 0.0
        need = forecast_8w + lost - stock_now - in_tr
        moq = moq_map.get(code, 1.0)
        rec = ceil_moq(need, moq)
        days = int(stock_now / (demand_month / 30)) if demand_month > 0 else (999 if stock_now > 0 else 0)
        if stockout_now and rec > 0:
            urgency = "critical"
        elif days < 14 and rec > 0:
            urgency = "critical"
        elif days < 30 and rec > 0:
            urgency = "warning"
        else:
            urgency = "safe"
        name = s["name"]
        lines.append({
            "code": code,
            "article": art_map.get(code, code),
            "name": name,
            "unit": (st["unit"] if st else "шт") or "шт",
            "stock": round(stock_now, 2),
            "stockoutNow": stockout_now,
            "emptyMonths": empty_months,
            "daysLeft": min(days, 999),
            "inTransit": round(in_tr, 2),
            "inTransitEta": eta,
            "demandMonth": round(demand_month, 2),
            "demandWeek": round(demand_month / 4, 2),
            "forecast8w": round(forecast_8w, 1),
            "lostDemand": round(lost, 1),
            "recommended": rec,
            "moq": int(moq) if moq == int(moq) else moq,
            "urgency": urgency,
            "category": classify(name),
        })

    to_order = [x for x in lines if x["recommended"] > 0]
    critical = [x for x in to_order if x["urgency"] == "critical"]
    excess = [x for x in lines if x["demandMonth"] > 0 and x["stock"] > x["demandMonth"] * 6]
    inbound_sku = sum(1 for v in transit.values() if v["qty"] > 0)
    inbound_qty = sum(v["qty"] for v in transit.values())

    cat_map = defaultdict(lambda: {"sku": 0, "order": 0, "empty": 0})
    for x in lines:
        c = cat_map[x["category"]]
        c["sku"] += 1
        if x["recommended"] > 0:
            c["order"] += 1
        if x["stockoutNow"]:
            c["empty"] += 1
    total_order = max(len(to_order), 1)
    categories = []
    for name, c in sorted(cat_map.items(), key=lambda kv: -kv[1]["order"]):
        categories.append({
            "name": name,
            "sku": c["sku"],
            "toOrder": c["order"],
            "empty": c["empty"],
            "share": round(100 * c["order"] / total_order),
        })

    # seasonality revenue — real ₸ from partner file
    raw_s = pd.read_excel(ROOT / "Сезонность ИЭК.xlsx", header=None)
    series = []
    for year_row, year in [(3, 2024), (4, 2025), (5, 2026)]:
        for i, m in enumerate(MONTHS, start=1):
            v = pd.to_numeric(raw_s.iloc[year_row, i], errors="coerce")
            if pd.isna(v):
                continue
            series.append({"year": year, "month": m, "sales": float(v), "coef": SEASON[m]})

    # anomalies from dynamics: qty >= 1000 on расходная
    dyn = pd.read_excel(ROOT / "Динамика продаж_2025-2026.xlsx")
    dyn = dyn[dyn["Дата"].astype(str) != "Итого"]
    dyn["Количество"] = pd.to_numeric(dyn["Количество"], errors="coerce")
    dyn = dyn[(dyn["Количество"] > 0) & dyn["Документ"].astype(str).str.startswith("Расходная")]
    med = dyn.groupby("Код")["Количество"].median()
    big = dyn[dyn["Количество"] >= 1000].copy()
    anomalies = []
    for _, r in big.nlargest(40, "Количество").iterrows():
        code = str(r["Код"])
        med_v = float(med.get(code, 0))
        if r["Количество"] < max(med_v * 8, 500):
            continue
        anomalies.append({
            "date": str(r["Дата"])[:10] if not isinstance(r["Дата"], str) else str(r["Дата"])[:19],
            "invoice": str(r["Номер"]),
            "article": art_map.get(code, code),
            "code": code,
            "name": str(r["Номенклатура"]),
            "qty": float(r["Количество"]),
            "median": round(med_v, 1),
            "reason": "IQR / разовая накладная, исключена из регулярного спроса",
        })

    to_order_sorted = sorted(to_order, key=lambda x: (0 if x["urgency"] == "critical" else 1 if x["urgency"] == "warning" else 2, -x["recommended"]))
    alerts = [x for x in to_order_sorted if x["urgency"] == "critical"][:8]
    featured_article = alerts[0]["article"] if alerts else to_order_sorted[0]["article"]

    bundle = {
        "source": str(ROOT),
        "asOf": "2026-09-22",
        "supplier": "IEK",
        "warehouse": "Алматы",
        "horizonWeeks": 8,
        "seasonOct": oct_coef,
        "featuredArticle": featured_article,
        "kpis": {
            "toOrder": len(to_order),
            "critical": len(critical),
            "deficit": sum(1 for x in lines if x["stockoutNow"]),
            "excess": len(excess),
            "inboundSku": inbound_sku,
            "inboundQty": round(inbound_qty),
            "skuTotal": len(lines),
        },
        "categories": categories,
        "series": series,
        "lines": to_order_sorted,
        "alerts": alerts,
        "anomalies": anomalies[:25],
        "suppliers": [{
            "name": "IEK",
            "role": "Единственный поставщик в выгрузке",
            "sku": len(moq_map) or len(lines),
            "lead": "до 14 дней (по УТ в пути)",
            "inbound": inbound_sku,
            "inboundQty": round(inbound_qty),
            "toOrder": len(to_order),
        }],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} sku={len(lines)} toOrder={len(to_order)} critical={len(critical)} anomalies={len(anomalies)}")


if __name__ == "__main__":
    main()
