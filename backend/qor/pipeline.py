"""Turn a 1C dump folder into the workspace JSON the web app already renders.

The model predicts next-month demand. The order is a separate policy:
forecast + safety stock − stock − incoming, rounded up to MOQ.
"""

from __future__ import annotations

import importlib.util
import math
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor

from .contract import CATEGORICAL, FEATURES, MODEL_NAME

REPO = Path(__file__).resolve().parents[2]
PREPARE_PATH = REPO / "scripts" / "prepare_dataset_v2.py"
MODEL_PATH = REPO / "ml" / "models" / MODEL_NAME

CABLE = re.compile(r"кабел|utp|ftp|витая|itk|провод", re.I)
AUTO = re.compile(r"автомат|ва47|узо|выкл|контактор|пускател|диф", re.I)
LIGHT = re.compile(r"свет|дпа|дба|led|ламп|светиль", re.I)
PANEL = re.compile(r"щит|корпус|шкаф|ящик", re.I)


def _load_prepare():
    spec = importlib.util.spec_from_file_location("qor_prepare_dataset", PREPARE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"не найден {PREPARE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _num(value, default=0.0) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return default
    try:
        if pd.isna(value):
            return default
    except TypeError:
        pass
    return float(value)


def _classify(name: str) -> str:
    if CABLE.search(name or ""):
        return "СКС и кабель"
    if AUTO.search(name or ""):
        return "Автоматика"
    if LIGHT.search(name or ""):
        return "Светотехника"
    if PANEL.search(name or ""):
        return "Щитовое"
    return "Прочее"


def _find(directory: Path, keyword: str) -> Path | None:
    needle = keyword.lower()
    hits = [p for p in directory.glob("*.xlsx") if needle in p.name.lower()]
    return hits[0] if hits else None


def _load_moq(directory: Path) -> pd.DataFrame:
    path = _find(directory, "moq")
    empty = pd.DataFrame(columns=["sku", "moq", "article"])
    if path is None:
        return empty
    df = pd.read_excel(path)
    code_col = next(c for c in df.columns if "код" in str(c).lower())
    moq_col = next(c for c in df.columns if "мин" in str(c).lower())
    article_col = next((c for c in df.columns if "артикул" in str(c).lower()), None)
    out = pd.DataFrame({
        "sku": df[code_col].astype(str).str.strip(),
        "moq": pd.to_numeric(df[moq_col], errors="coerce"),
        "article": df[article_col].astype(str).str.strip() if article_col else df[code_col].astype(str),
    })
    out = out.dropna(subset=["moq"])
    return out.groupby("sku", as_index=False).agg(moq=("moq", "max"), article=("article", "first"))


def _load_incoming(directory: Path) -> pd.DataFrame:
    path = _find(directory, "путь")
    empty = pd.DataFrame(columns=["sku", "incoming"])
    if path is None:
        return empty
    df = pd.read_excel(path)
    code_col = next(c for c in df.columns if "код" in str(c).lower())
    meta = [
        c for c in df.columns
        if any(word in str(c).lower() for word in ("код", "артикул", "наимен"))
    ]
    qty_cols = [c for c in df.columns if c not in meta]
    for col in qty_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    out = pd.DataFrame({
        "sku": df[code_col].astype(str).str.strip(),
        "incoming": df[qty_cols].fillna(0).sum(axis=1) if qty_cols else 0,
    })
    return out.groupby("sku", as_index=False)["incoming"].sum()


def _round_moq(quantity: float, moq: float) -> int:
    if quantity <= 0:
        return 0
    if moq is None or pd.isna(moq) or moq <= 1:
        return int(math.ceil(quantity))
    return int(math.ceil(quantity / moq) * moq)


def _risk(forecast: float, available: float) -> str:
    if forecast <= 0:
        return "safe"
    coverage = available / forecast
    if coverage < 0.5:
        return "critical"
    if coverage < 1:
        return "warning"
    return "safe"


_RU_MONTHS = ("янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек")


def monthly_series(frame: pd.DataFrame, codes: set[str], months: int = 12) -> dict[str, list[dict]]:
    """Last months of positive sales for the mobile mini chart."""
    if frame is None or frame.empty or not codes or "sales_positive" not in frame.columns:
        return {}
    wanted = frame[frame["sku"].astype(str).isin(codes)]
    out: dict[str, list[dict]] = {}
    for sku, group in wanted.groupby("sku", sort=False):
        tail = (
            group.groupby("month", as_index=False)["sales_positive"]
            .sum()
            .sort_values("month")
            .tail(months)
        )
        points = []
        for row in tail.itertuples(index=False):
            month = pd.Timestamp(row.month)
            points.append({
                "label": f"{_RU_MONTHS[month.month - 1]} {month.year % 100:02d}",
                "value": round(_num(row.sales_positive), 1),
            })
        if points:
            out[str(sku)] = points
    return out


def build_workspace(data_dir: Path, supplier: str = "IEK") -> dict:
    data_dir = Path(data_dir)
    if not data_dir.is_dir():
        raise FileNotFoundError(f"нет папки выгрузки: {data_dir}")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"нет модели: {MODEL_PATH}")

    prepare = _load_prepare()
    frame = prepare.add_features(prepare.load_supplier(supplier, data_dir))
    frame = frame[frame["demand_lag_3"].notna()].copy()
    if frame.empty:
        raise ValueError("после признаков не осталось SKU с историей хотя бы в 3 месяца")

    latest = frame.sort_values("month").groupby("sku", as_index=False).tail(1).copy()
    features = latest[FEATURES].copy()
    for col in CATEGORICAL:
        features[col] = features[col].fillna("UNKNOWN").astype(str)

    model = CatBoostRegressor()
    model.load_model(MODEL_PATH)
    latest["forecast"] = np.clip(model.predict(features), 0, None)

    latest = latest.merge(_load_moq(data_dir), on="sku", how="left")
    latest = latest.merge(_load_incoming(data_dir), on="sku", how="left")
    latest["incoming"] = latest["incoming"].fillna(0).clip(lower=0)
    latest["stock"] = pd.to_numeric(latest["stock"], errors="coerce").fillna(0).clip(lower=0)
    latest["safety_stock"] = latest["rolling_std_6"].fillna(0).clip(lower=0) * 0.5
    latest["net"] = (latest["forecast"] + latest["safety_stock"] - latest["stock"] - latest["incoming"]).clip(lower=0)
    latest["recommended"] = [
        _round_moq(q, m) for q, m in zip(latest["net"], latest["moq"], strict=True)
    ]
    latest["available"] = latest["stock"] + latest["incoming"]
    latest["urgency"] = [
        _risk(f, a) for f, a in zip(latest["forecast"], latest["available"], strict=True)
    ]

    history = frame.sort_values("month")
    months_used = history.groupby("sku").size()
    stockout_12 = history.groupby("sku").tail(12).groupby("sku")["stockout_flag_v2"].sum()
    stock_known = history.groupby("sku")["stock"].apply(lambda s: bool(s.notna().any()))
    ever_stocked = history.groupby("sku")["stock"].max().fillna(0) > 0

    as_of = pd.Timestamp(latest["month"].max())
    as_of_date = date(as_of.year, as_of.month, 1)

    lines = []
    for row in latest.itertuples(index=False):
        sku = str(row.sku)
        name = " ".join(str(row.product_name).split())
        forecast = _num(row.forecast)
        stock = _num(row.stock)
        incoming = _num(row.incoming)
        safety = _num(row.safety_stock)
        moq = _num(row.moq, 1.0)
        recommended = int(row.recommended)
        used = int(months_used.get(sku, 0))
        article = str(row.article).strip() if isinstance(getattr(row, "article", None), str) and str(row.article).strip() not in ("", "nan") else sku
        daily = forecast / 30 if forecast > 0 else 0
        days_left = int(min(stock / daily, 9999)) if daily > 0 else (9999 if stock > 0 else 0)
        lines.append({
            "code": sku,
            "article": article,
            "name": name,
            "unit": "шт",
            "stock": round(stock, 1),
            "stockoutNow": stock <= 0,
            "neverStocked": not bool(ever_stocked.get(sku, False)),
            "noStockRecord": not bool(stock_known.get(sku, False)),
            "emptyMonths": int(stockout_12.get(sku, 0)),
            "stockout12m": int(stockout_12.get(sku, 0)),
            "monthsUsed": used,
            "daysLeft": days_left,
            "inTransit": round(incoming, 1),
            "inTransitEta": None,
            "demandMonth": round(forecast, 1),
            "demandWeek": round(forecast / 4.345, 1),
            "forecast8w": round(forecast, 1),
            "lostDemand": 0,
            "recommended": recommended,
            "moq": int(moq) if moq >= 1 else 1,
            "urgency": row.urgency,
            "category": _classify(name),
            "steps": [
                {"key": "base", "label": "Прогноз CatBoost на следующий месяц", "value": round(forecast, 1)},
                {"key": "season", "label": "Страховой запас (0.5 × σ за 6 мес.)", "delta": round(safety, 1)},
                {"key": "stock", "label": "Текущий остаток", "delta": round(-stock, 1)},
                {"key": "transit", "label": "В пути", "delta": round(-incoming, 1)},
                {"key": "moq", "label": f"Округление до MOQ {int(moq) if moq >= 1 else 1}", "value": recommended},
            ],
        })

    def trustworthy(item: dict) -> bool:
        return (not item["neverStocked"]) and (not item["noStockRecord"]) and item["monthsUsed"] >= 3

    to_order = [item for item in lines if item["recommended"] > 0]
    to_order.sort(key=lambda item: (0 if item["urgency"] == "critical" else 1 if item["urgency"] == "warning" else 2, -item["recommended"]))
    critical = [item for item in to_order if item["urgency"] == "critical"]
    alerts = [item for item in critical if trustworthy(item)][:8]
    unverified = [item for item in to_order if not trustworthy(item)]

    cat_map: dict[str, dict[str, int]] = {}
    for item in lines:
        bucket = cat_map.setdefault(item["category"], {"sku": 0, "order": 0, "empty": 0})
        bucket["sku"] += 1
        if item["recommended"] > 0:
            bucket["order"] += 1
        if item["stockoutNow"]:
            bucket["empty"] += 1
    total_order = sum(v["order"] for v in cat_map.values()) or 1
    categories = [
        {
            "name": name,
            "sku": bucket["sku"],
            "toOrder": bucket["order"],
            "empty": bucket["empty"],
            "share": round(100 * bucket["order"] / total_order),
        }
        for name, bucket in sorted(cat_map.items(), key=lambda kv: -kv[1]["order"])
    ]

    inbound = latest[latest["incoming"] > 0]
    featured = (alerts or to_order or lines)[0]["article"]

    return {
        "asOf": as_of_date.isoformat(),
        "asOfLabel": as_of.strftime("%m.%Y"),
        "supplier": supplier,
        "warehouse": "Алматы",
        "horizonWeeks": 4,
        "seasonOct": 1,
        "monthEquiv": 1,
        "seasonParts": [],
        "featuredArticle": featured,
        "model": {
            "name": MODEL_NAME,
            "label": "CatBoost v2",
            "target": "спрос на следующий месяц",
            "policy": "прогноз + 0.5σ − остаток − в пути, кратно MOQ",
            "uses": ["лаги 1–12 мес.", "сезонность", "stockout", "выбросы"],
        },
        "kpis": {
            "toOrder": len(to_order),
            "critical": len(critical),
            "deficit": sum(1 for item in lines if item["stockoutNow"]),
            "excess": sum(1 for item in lines if item["demandMonth"] > 0 and item["stock"] > 6 * item["demandMonth"]),
            "inboundSku": int(len(inbound)),
            "inboundQty": round(float(latest["incoming"].sum())),
            "skuTotal": int(len(lines)),
            "unverified": len(unverified),
        },
        "categories": categories,
        "series": [],
        "skuSeries": monthly_series(history, {item["code"] for item in lines}),
        "lines": to_order,
        "alerts": alerts,
        "anomalies": [],
        "suppliers": [{
            "name": supplier,
            "role": "Прогноз CatBoost по загруженной выгрузке",
            "sku": int(latest["moq"].notna().sum()) or len(lines),
            "lead": "горизонт модели — следующий месяц",
            "inbound": int(len(inbound)),
            "inboundQty": round(float(latest["incoming"].sum())),
            "toOrder": len(to_order),
        }],
    }
