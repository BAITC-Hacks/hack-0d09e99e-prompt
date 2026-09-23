from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
IEK_DIR = DATA_DIR / "IEK"
SYSTEME_DIR = DATA_DIR / "Systeme"

PROCESSED_DIR = DATA_DIR / "processed"

DATASET = (
    PROCESSED_DIR
    / "training_dataset_v2.csv"
)

MODEL_PATH = (
    ROOT
    / "ml"
    / "models"
    / "demand_model_v2.cbm"
)

CSV_OUTPUT = (
    PROCESSED_DIR
    / "recommended_orders_v2.csv"
)

JSON_OUTPUT = (
    PROCESSED_DIR
    / "recommended_orders_v2.json"
)


# ============================================================
# MODEL FEATURES
# ============================================================

FEATURES = [
    "supplier",
    "sku",

    "demand_lag_1",
    "demand_lag_2",
    "demand_lag_3",
    "demand_lag_6",
    "demand_lag_12",

    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_mean_12",

    "rolling_std_3",
    "rolling_std_6",

    "growth_3m",

    "stock",

    "year",
    "month_num",
    "quarter",

    "month_sin",
    "month_cos",

    "seasonality_index",

    "outlier_lag_1",
    "stockout_lag_1",
    "lost_demand_lag_1",
]

CATEGORICAL = [
    "supplier",
    "sku",
]


# ============================================================
# HELPERS
# ============================================================

def find_file(directory: Path, keyword: str) -> Path:
    for path in directory.glob("*.xlsx"):
        if keyword.lower() in path.name.lower():
            return path

    raise FileNotFoundError(
        f"Не найден '{keyword}' в {directory}"
    )


def normalize_sku(series):
    return (
        series
        .astype(str)
        .str.strip()
        .replace(
            {
                "nan": np.nan,
                "None": np.nan,
            }
        )
    )


def numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def safe_number(value, default=0.0):
    if pd.isna(value):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# IEK MOQ
# ============================================================

def load_iek_moq():
    path = find_file(
        IEK_DIR,
        "MOQ",
    )

    print(
        f"IEK MOQ: {path.name}",
        flush=True,
    )

    df = pd.read_excel(path)

    code_candidates = [
        c
        for c in df.columns
        if "код" in str(c).lower()
    ]

    if not code_candidates:
        raise ValueError(
            "IEK MOQ: не найдена колонка кода."
        )

    code_col = code_candidates[0]

    moq_candidates = [
        c
        for c in df.columns
        if "мин" in str(c).lower()
        or "крат" in str(c).lower()
    ]

    if not moq_candidates:
        raise ValueError(
            "IEK MOQ: не найдена колонка MOQ."
        )

    moq_col = moq_candidates[0]

    result = df[
        [
            code_col,
            moq_col,
        ]
    ].copy()

    result.columns = [
        "sku",
        "moq",
    ]

    result["sku"] = normalize_sku(
        result["sku"]
    )

    result["moq"] = numeric(
        result["moq"]
    )

    result = result.dropna(
        subset=["sku"]
    )

    result = (
        result
        .groupby(
            "sku",
            as_index=False,
        )["moq"]
        .max()
    )

    return result


# ============================================================
# SYSTEME MOQ
# ============================================================

def load_systeme_moq():
    path = find_file(
        SYSTEME_DIR,
        "MOQ",
    )

    print(
        f"Systeme MOQ: {path.name}",
        flush=True,
    )

    df = pd.read_excel(path)

    code_col = None

    for col in df.columns:
        text = str(col).lower()

        if (
            "номенклатура" in text
            and "код" in text
        ):
            code_col = col
            break

    if code_col is None:
        for col in df.columns:
            if "код" in str(col).lower():
                code_col = col
                break

    if code_col is None:
        raise ValueError(
            "Systeme MOQ: SKU column not found."
        )

    moq_col = None

    for col in df.columns:
        text = str(col).lower()

        if (
            "крат" in text
            or "min" in text
            or "мин" in text
        ):
            moq_col = col
            break

    if moq_col is None:
        raise ValueError(
            "Systeme MOQ column not found."
        )

    result = df[
        [
            code_col,
            moq_col,
        ]
    ].copy()

    result.columns = [
        "sku",
        "moq",
    ]

    result["sku"] = normalize_sku(
        result["sku"]
    )

    result["moq"] = numeric(
        result["moq"]
    )

    result = result.dropna(
        subset=["sku"]
    )

    result = (
        result
        .groupby(
            "sku",
            as_index=False,
        )["moq"]
        .max()
    )

    return result


# ============================================================
# IEK INCOMING
# ============================================================

def load_iek_incoming():
    path = find_file(
        IEK_DIR,
        "Путь",
    )

    print(
        f"IEK incoming: {path.name}",
        flush=True,
    )

    df = pd.read_excel(path)

    code_col = "Код 1с"

    if code_col not in df.columns:
        raise ValueError(
            "IEK incoming: 'Код 1с' не найден."
        )

    metadata = {
        "Код 1с",
        "Артикул ИЭК",
        " Наименование",
        "Наименование",
    }

    quantity_columns = [
        col
        for col in df.columns
        if col not in metadata
    ]

    for col in quantity_columns:
        df[col] = numeric(
            df[col]
        )

    df["incoming"] = (
        df[quantity_columns]
        .fillna(0)
        .sum(axis=1)
    )

    result = df[
        [
            code_col,
            "incoming",
        ]
    ].copy()

    result.columns = [
        "sku",
        "incoming",
    ]

    result["sku"] = normalize_sku(
        result["sku"]
    )

    result["incoming"] = (
        numeric(
            result["incoming"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    result = result.dropna(
        subset=["sku"]
    )

    result = (
        result
        .groupby(
            "sku",
            as_index=False,
        )["incoming"]
        .sum()
    )

    return result


# ============================================================
# SYSTEME STOCK + INCOMING
# ============================================================

def load_systeme_inventory():
    path = find_file(
        SYSTEME_DIR,
        "Товар в пути",
    )

    print(
        f"Systeme inventory: {path.name}",
        flush=True,
    )

    df = pd.read_excel(
        path,
        sheet_name="TDSheet",
        header=1,
    )

    required = [
        "Код 1с",
        "Свободный остаток",
        "СЭ в пути 24.09",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Systeme inventory missing columns: "
            f"{missing}"
        )

    result = df[
        required
    ].copy()

    result.columns = [
        "sku",
        "free_stock",
        "incoming",
    ]

    result["sku"] = normalize_sku(
        result["sku"]
    )

    result["free_stock"] = (
        numeric(
            result["free_stock"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    result["incoming"] = (
        numeric(
            result["incoming"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    result = result.dropna(
        subset=["sku"]
    )

    result = (
        result
        .groupby(
            "sku",
            as_index=False,
        )
        .agg(
            free_stock=(
                "free_stock",
                "max",
            ),
            incoming=(
                "incoming",
                "sum",
            ),
        )
    )

    return result


# ============================================================
# MOQ ROUNDING
# ============================================================

def round_to_moq(quantity, moq):
    quantity = safe_number(
        quantity,
        0,
    )

    moq = safe_number(
        moq,
        0,
    )

    if quantity <= 0:
        return 0

    if moq <= 0:
        return int(
            math.ceil(quantity)
        )

    return int(
        math.ceil(
            quantity / moq
        )
        * moq
    )


# ============================================================
# SAFETY STOCK
# ============================================================

def calculate_safety_stock(row):
    """
    MVP V2.

    Не используем старую агрессивную формулу
    rolling_std * 0.5 без ограничений.

    Safety stock ограничивается сверху
    50% прогнозируемого месячного спроса.
    """

    forecast = max(
        safe_number(
            row["forecast"],
            0,
        ),
        0,
    )

    volatility = max(
        safe_number(
            row["rolling_std_6"],
            0,
        ),
        0,
    )

    raw_safety = (
        volatility * 0.35
    )

    max_safety = (
        forecast * 0.50
    )

    safety = min(
        raw_safety,
        max_safety,
    )

    return max(
        safety,
        0,
    )


# ============================================================
# RISK
# ============================================================

def calculate_risk(row):
    forecast = safe_number(
        row["forecast"],
        0,
    )

    available = (
        safe_number(
            row["free_stock"],
            0,
        )
        + safe_number(
            row["incoming"],
            0,
        )
    )

    if forecast <= 0:
        return "LOW"

    coverage = (
        available / forecast
    )

    if coverage < 0.5:
        return "HIGH"

    if coverage < 1.0:
        return "MEDIUM"

    return "LOW"


# ============================================================
# URGENCY
# ============================================================

def calculate_urgency(row):
    order = safe_number(
        row["recommended_order"],
        0,
    )

    risk = row["risk"]

    stock = safe_number(
        row["free_stock"],
        0,
    )

    if (
        order > 0
        and risk == "HIGH"
        and stock <= 0
    ):
        return "CRITICAL"

    if (
        order > 0
        and risk == "HIGH"
    ):
        return "HIGH"

    if (
        order > 0
        and risk == "MEDIUM"
    ):
        return "MEDIUM"

    return "LOW"


# ============================================================
# TREND
# ============================================================

def calculate_trend(value):
    value = safe_number(
        value,
        0,
    )

    if value >= 0.20:
        return "GROWING"

    if value <= -0.20:
        return "DECLINING"

    return "STABLE"


# ============================================================
# EXPLANATION
# ============================================================

def build_reason(row):
    parts = [
        f"Прогноз спроса: "
        f"{row['forecast']:.0f} шт.",

        f"Свободный остаток: "
        f"{row['free_stock']:.0f} шт.",

        f"В пути: "
        f"{row['incoming']:.0f} шт.",

        f"Страховой запас: "
        f"{row['safety_stock']:.0f} шт.",
    ]

    if pd.notna(
        row["moq"]
    ):
        parts.append(
            f"MOQ: "
            f"{row['moq']:.0f} шт."
        )

    if row["stockout_signal"]:
        parts.append(
            "Есть сигнал предыдущего stockout."
        )

    if row["outlier_signal"]:
        parts.append(
            "В истории обнаружена "
            "аномальная продажа."
        )

    if row["trend"] == "GROWING":
        parts.append(
            "Наблюдается рост спроса."
        )

    if row["trend"] == "DECLINING":
        parts.append(
            "Наблюдается снижение спроса."
        )

    return " ".join(parts)


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "\nQOR / ProcureAI",
        flush=True,
    )

    print(
        "PROCUREMENT ENGINE V2\n",
        flush=True,
    )

    # ========================================================
    # LOAD MODEL
    # ========================================================

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Нет модели: {MODEL_PATH}"
        )

    model = CatBoostRegressor()

    model.load_model(
        MODEL_PATH
    )

    print(
        "✓ CatBoost V2 загружен",
        flush=True,
    )

    # ========================================================
    # LOAD DATASET
    # ========================================================

    df = pd.read_csv(
        DATASET
    )

    df["month"] = pd.to_datetime(
        df["month"]
    )

    print(
        f"Dataset: {len(df):,} rows",
        flush=True,
    )

    # Последнее доступное состояние каждого SKU.
    latest = (
        df.sort_values(
            "month"
        )
        .groupby(
            [
                "supplier",
                "sku",
            ],
            as_index=False,
        )
        .tail(1)
        .copy()
    )

    print(
        f"SKU для расчёта: "
        f"{len(latest):,}",
        flush=True,
    )

    # ========================================================
    # MODEL INPUT
    # ========================================================

    X = (
        latest[
            FEATURES
        ]
        .copy()
    )

    for col in CATEGORICAL:
        X[col] = (
            X[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

    # ========================================================
    # FORECAST
    # ========================================================

    print(
        "Генерируем forecast...",
        flush=True,
    )

    predictions = (
        model.predict(
            X
        )
    )

    latest["forecast"] = np.clip(
        predictions,
        0,
        None,
    )

    # ========================================================
    # DEFAULT INVENTORY
    # ========================================================

    latest["free_stock"] = (
        numeric(
            latest["stock"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    latest["incoming"] = 0.0

    latest["moq"] = np.nan

    # ========================================================
    # LOAD IEK DATA
    # ========================================================

    print(
        "\nЗагружаем IEK procurement data...",
        flush=True,
    )

    iek_moq = load_iek_moq()

    iek_incoming = (
        load_iek_incoming()
    )

    # ========================================================
    # LOAD SYSTEME DATA
    # ========================================================

    print(
        "\nЗагружаем Systeme procurement data...",
        flush=True,
    )

    systeme_moq = (
        load_systeme_moq()
    )

    systeme_inventory = (
        load_systeme_inventory()
    )

    # ========================================================
    # APPLY IEK
    # ========================================================

    iek_mask = (
        latest["supplier"] == "IEK"
    )

    iek = (
        latest.loc[
            iek_mask
        ]
        .copy()
    )

    iek = iek.merge(
        iek_moq,
        on="sku",
        how="left",
        suffixes=(
            "",
            "_source",
        ),
    )

    if "moq_source" in iek.columns:
        iek["moq"] = (
            iek["moq_source"]
        )

        iek = iek.drop(
            columns=[
                "moq_source",
            ]
        )

    iek = iek.merge(
        iek_incoming,
        on="sku",
        how="left",
        suffixes=(
            "",
            "_source",
        ),
    )

    if "incoming_source" in iek.columns:
        iek["incoming"] = (
            iek["incoming_source"]
            .fillna(0)
        )

        iek = iek.drop(
            columns=[
                "incoming_source",
            ]
        )

    # ========================================================
    # APPLY SYSTEME
    # ========================================================

    systeme_mask = (
        latest["supplier"]
        == "Systeme"
    )

    systeme = (
        latest.loc[
            systeme_mask
        ]
        .copy()
    )

    systeme = systeme.merge(
        systeme_moq,
        on="sku",
        how="left",
        suffixes=(
            "",
            "_source",
        ),
    )

    if "moq_source" in systeme.columns:
        systeme["moq"] = (
            systeme["moq_source"])

        systeme = systeme.drop(
            columns=[
                "moq_source",
            ]
        )

    # --------------------------------------------------------
    # Systeme: реальный свободный остаток + товар в пути
    # --------------------------------------------------------

    systeme = systeme.merge(
        systeme_inventory,
        on="sku",
        how="left",
        suffixes=(
            "",
            "_source",
        ),
    )

    if "free_stock_source" in systeme.columns:

        systeme["free_stock"] = (
            systeme["free_stock_source"]
            .fillna(
                systeme["free_stock"]
            )
        )

        systeme = systeme.drop(
            columns=[
                "free_stock_source",
            ]
        )

    if "incoming_source" in systeme.columns:

        systeme["incoming"] = (
            systeme["incoming_source"]
            .fillna(0)
        )

        systeme = systeme.drop(
            columns=[
                "incoming_source",
            ]
        )

    # ========================================================
    # COMBINE IEK + SYSTEME
    # ========================================================

    latest = pd.concat(
        [
            iek,
            systeme,
        ],
        ignore_index=True,
    )

    # ========================================================
    # CLEAN NUMERIC VALUES
    # ========================================================

    latest["free_stock"] = (
        numeric(
            latest["free_stock"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    latest["incoming"] = (
        numeric(
            latest["incoming"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    latest["moq"] = (
        numeric(
            latest["moq"]
        )
    )

    latest["forecast"] = (
        numeric(
            latest["forecast"]
        )
        .fillna(0)
        .clip(lower=0)
    )

    # ========================================================
    # SAFETY STOCK
    # ========================================================

    print(
        "\nРассчитываем safety stock...",
        flush=True,
    )

    latest["safety_stock"] = (
        latest.apply(
            calculate_safety_stock,
            axis=1,
        )
    )

    # ========================================================
    # AVAILABLE
    # ========================================================

    latest["available"] = (
        latest["free_stock"]
        + latest["incoming"]
    )

    # ========================================================
    # NET REQUIREMENT
    # ========================================================

    latest["net_requirement"] = (
        latest["forecast"]
        + latest["safety_stock"]
        - latest["free_stock"]
        - latest["incoming"]
    )

    latest["net_requirement"] = (
        latest["net_requirement"]
        .clip(lower=0)
    )

    # ========================================================
    # MOQ ROUNDING
    # ========================================================

    print(
        "Применяем MOQ...",
        flush=True,
    )

    latest["recommended_order"] = (
        latest.apply(
            lambda row:
            round_to_moq(
                row["net_requirement"],
                row["moq"],
            ),
            axis=1,
        )
    )

    # ========================================================
    # RISK
    # ========================================================

    latest["risk"] = (
        latest.apply(
            calculate_risk,
            axis=1,
        )
    )

    # ========================================================
    # URGENCY
    # ========================================================

    latest["urgency"] = (
        latest.apply(
            calculate_urgency,
            axis=1,
        )
    )

    # ========================================================
    # TREND
    # ========================================================

    latest["trend"] = (
        latest["growth_3m"]
        .apply(
            calculate_trend
        )
    )

    # ========================================================
    # SIGNALS
    # ========================================================

    latest["stockout_signal"] = (
        latest["stockout_lag_1"]
        .fillna(0)
        .astype(float)
        > 0
    )

    latest["outlier_signal"] = (
        latest["outlier_lag_1"]
        .fillna(0)
        .astype(float)
        > 0
    )

    # ========================================================
    # COVERAGE RATIO
    # ========================================================

    latest["coverage_ratio"] = np.where(
        latest["forecast"] > 0,

        latest["available"]
        / latest["forecast"],

        np.inf,
    )

    # ========================================================
    # SHORTAGE
    # ========================================================

    latest["shortage_without_order"] = (
        latest["forecast"]
        - latest["available"]
    ).clip(lower=0)

    # ========================================================
    # PROJECTED STOCK AFTER ORDER
    # ========================================================

    latest["projected_stock_after_order"] = (
        latest["free_stock"]
        + latest["incoming"]
        + latest["recommended_order"]
        - latest["forecast"]
    )

    # ========================================================
    # REASON
    # ========================================================

    latest["reason"] = (
        latest.apply(
            build_reason,
            axis=1,
        )
    )

    # ========================================================
    # ORDER REQUIRED
    # ========================================================

    latest["order_required"] = (
        latest["recommended_order"]
        > 0
    )

    # ========================================================
    # SORTING PRIORITY
    # ========================================================

    urgency_priority = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    risk_priority = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    latest["_urgency_priority"] = (
        latest["urgency"]
        .map(
            urgency_priority
        )
        .fillna(99)
    )

    latest["_risk_priority"] = (
        latest["risk"]
        .map(
            risk_priority
        )
        .fillna(99)
    )

    latest = (
        latest
        .sort_values(
            [
                "_urgency_priority",
                "_risk_priority",
                "recommended_order",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    latest = latest.drop(
        columns=[
            "_urgency_priority",
            "_risk_priority",
        ]
    )

    # ========================================================
    # FINAL COLUMNS
    # ========================================================

    output_columns = [
        "supplier",
        "sku",
        "product_name",

        "forecast",

        "free_stock",
        "incoming",
        "available",

        "safety_stock",

        "moq",

        "net_requirement",
        "recommended_order",

        "shortage_without_order",
        "projected_stock_after_order",

        "coverage_ratio",

        "risk",
        "urgency",

        "trend",
        "seasonality_index",

        "stockout_signal",
        "outlier_signal",

        "order_required",

        "reason",
    ]

    result = (
        latest[
            output_columns
        ]
        .copy()
    )

    # ========================================================
    # SAVE CSV
    # ========================================================

    result.to_csv(
        CSV_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # SAVE JSON
    # ========================================================

    json_records = []

    for _, row in result.iterrows():

        record = {
            "supplier":
                str(
                    row["supplier"]
                ),

            "sku":
                str(
                    row["sku"]
                ),

            "product_name":
                (
                    ""
                    if pd.isna(
                        row["product_name"]
                    )
                    else str(
                        row["product_name"]
                    )
                ),

            "forecast":
                round(
                    safe_number(
                        row["forecast"]
                    ),
                    2,
                ),

            "inventory": {
                "free_stock":
                    round(
                        safe_number(
                            row["free_stock"]
                        ),
                        2,
                    ),

                "incoming":
                    round(
                        safe_number(
                            row["incoming"]
                        ),
                        2,
                    ),

                "available":
                    round(
                        safe_number(
                            row["available"]
                        ),
                        2,
                    ),
            },

            "procurement": {
                "safety_stock":
                    round(
                        safe_number(
                            row["safety_stock"]
                        ),
                        2,
                    ),

                "moq":
                    (
                        None
                        if pd.isna(
                            row["moq"]
                        )
                        else
                        round(
                            safe_number(
                                row["moq"]
                            ),
                            2,
                        )
                    ),

                "net_requirement":
                    round(
                        safe_number(
                            row[
                                "net_requirement"
                            ]
                        ),
                        2,
                    ),

                "recommended_order":
                    int(
                        safe_number(
                            row[
                                "recommended_order"
                            ]
                        )
                    ),

                "projected_stock_after_order":
                    round(
                        safe_number(
                            row[
                                "projected_stock_after_order"
                            ]
                        ),
                        2,
                    ),
            },

            "risk": {
                "level":
                    str(
                        row["risk"]
                    ),

                "urgency":
                    str(
                        row["urgency"]
                    ),

                "coverage_ratio":
                    (
                        None
                        if not np.isfinite(
                            safe_number(
                                row[
                                    "coverage_ratio"
                                ]
                            )
                        )
                        else
                        round(
                            safe_number(
                                row[
                                    "coverage_ratio"
                                ]
                            ),
                            3,
                        )
                    ),

                "shortage_without_order":
                    round(
                        safe_number(
                            row[
                                "shortage_without_order"
                            ]
                        ),
                        2,
                    ),
            },

            "signals": {
                "trend":
                    str(
                        row["trend"]
                    ),

                "seasonality_index":
                    round(
                        safe_number(
                            row[
                                "seasonality_index"
                            ],
                            1,
                        ),
                        3,
                    ),

                "stockout":
                    bool(
                        row[
                            "stockout_signal"
                        ]
                    ),

                "outlier":
                    bool(
                        row[
                            "outlier_signal"
                        ]
                    ),
            },

            "order_required":
                bool(
                    row[
                        "order_required"
                    ]
                ),

            "reason":
                str(
                    row["reason"]
                ),
        }

        json_records.append(
            record
        )

    with open(
        JSON_OUTPUT,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            json_records,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # REPORT
    # ========================================================

    print(
        "\n" + "=" * 70,
        flush=True,
    )

    print(
        "PROCUREMENT ENGINE V2 — RESULT",
        flush=True,
    )

    print(
        "=" * 70,
        flush=True,
    )

    print(
        f"Всего SKU: "
        f"{len(result):,}",
        flush=True,
    )

    print(
        f"Требуют заказа: "
        f"{result['order_required'].sum():,}",
        flush=True,
    )

    # ========================================================
    # SUPPLIERS
    # ========================================================

    print(
        "\nПо поставщикам:",
        flush=True,
    )

    supplier_stats = (
        result
        .groupby(
            "supplier"
        )
        .agg(
            sku=(
                "sku",
                "size",
            ),

            order_required=(
                "order_required",
                "sum",
            ),

            total_forecast=(
                "forecast",
                "sum",
            ),

            total_order=(
                "recommended_order",
                "sum",
            ),
        )
    )

    print(
        supplier_stats.to_string(),
        flush=True,
    )

    # ========================================================
    # RISK
    # ========================================================

    print(
        "\nRisk:",
        flush=True,
    )

    print(
        result[
            "risk"
        ]
        .value_counts()
        .to_string(),
        flush=True,
    )

    # ========================================================
    # URGENCY
    # ========================================================

    print(
        "\nUrgency:",
        flush=True,
    )

    print(
        result[
            "urgency"
        ]
        .value_counts()
        .to_string(),
        flush=True,
    )

    # ========================================================
    # TOP 15
    # ========================================================

    print(
        "\nTOP-15 CRITICAL ORDERS:\n",
        flush=True,
    )

    top = (
        result[
            result[
                "recommended_order"
            ] > 0
        ]
        .head(15)
    )

    print(
        top[
            [
                "supplier",
                "sku",
                "forecast",
                "free_stock",
                "incoming",
                "safety_stock",
                "moq",
                "recommended_order",
                "risk",
                "urgency",
            ]
        ]
        .to_string(
            index=False
        ),
        flush=True,
    )

    # ========================================================
    # FILES
    # ========================================================

    print(
        "\nCSV:",
        flush=True,
    )

    print(
        CSV_OUTPUT,
        flush=True,
    )

    print(
        "\nJSON:",
        flush=True,
    )

    print(
        JSON_OUTPUT,
        flush=True,
    )

    print(
        "\n✓ Procurement Engine V2 готов.",
        flush=True,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()