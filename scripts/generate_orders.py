from pathlib import Path
import math

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "processed" / "training_dataset.csv"
MODEL_PATH = ROOT / "ml" / "models" / "demand_model.cbm"
IEK_DIR = ROOT / "data" / "IEK"

OUTPUT = ROOT / "data" / "processed" / "recommended_orders.csv"


FEATURES = [
    "supplier",
    "sku",
    "sales_lag_1",
    "sales_lag_2",
    "sales_lag_3",
    "sales_lag_6",
    "sales_lag_12",
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
    "stockout_flag",
]

CATEGORICAL = ["supplier", "sku"]


def find_file(directory, keyword):
    for path in directory.glob("*.xlsx"):
        if keyword.lower() in path.name.lower():
            return path

    raise FileNotFoundError(
        f"Не найден '{keyword}' в {directory}"
    )


def load_moq():
    path = find_file(IEK_DIR, "MOQ")

    print(f"MOQ: {path.name}")

    df = pd.read_excel(path)

    # IEK:
    # Код 1с
    # Мин. разр. к отгр.
    code_col = next(
        c for c in df.columns
        if "код" in str(c).lower()
    )

    moq_col = next(
        c for c in df.columns
        if "мин" in str(c).lower()
    )

    result = df[[code_col, moq_col]].copy()

    result.columns = ["sku", "moq"]

    result["sku"] = (
        result["sku"]
        .astype(str)
        .str.strip()
    )

    result["moq"] = pd.to_numeric(
        result["moq"],
        errors="coerce"
    )

    result = (
        result.dropna(subset=["moq"])
        .groupby("sku", as_index=False)["moq"]
        .max()
    )

    return result


def load_incoming():
    path = find_file(IEK_DIR, "Путь")

    print(f"Товар в пути: {path.name}")

    df = pd.read_excel(path)

    code_col = next(
        c for c in df.columns
        if "код" in str(c).lower()
    )

    meta_columns = []

    for col in df.columns:
        text = str(col).lower()

        if (
            "код" in text
            or "артикул" in text
            or "наимен" in text
        ):
            meta_columns.append(col)

    quantity_columns = [
        col for col in df.columns
        if col not in meta_columns
    ]

    for col in quantity_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    df["incoming"] = (
        df[quantity_columns]
        .fillna(0)
        .sum(axis=1)
    )

    result = df[
        [code_col, "incoming"]
    ].copy()

    result.columns = ["sku", "incoming"]

    result["sku"] = (
        result["sku"]
        .astype(str)
        .str.strip()
    )

    result = (
        result.groupby("sku", as_index=False)["incoming"]
        .sum()
    )

    return result


def round_to_moq(quantity, moq):
    if quantity <= 0:
        return 0

    if pd.isna(moq) or moq <= 0:
        return int(math.ceil(quantity))

    return int(
        math.ceil(quantity / moq) * moq
    )


def risk_level(forecast, available):
    if forecast <= 0:
        return "LOW"

    coverage = available / forecast

    if coverage < 0.5:
        return "HIGH"

    if coverage < 1:
        return "MEDIUM"

    return "LOW"


def main():

    print("\nQOR / ProcureAI")
    print("Генерация рекомендаций закупки\n")

    # --------------------------------------------------
    # Model
    # --------------------------------------------------

    model = CatBoostRegressor()

    model.load_model(
        MODEL_PATH
    )

    print("✓ CatBoost загружен")

    # --------------------------------------------------
    # Dataset
    # --------------------------------------------------

    df = pd.read_csv(DATASET)

    df["month"] = pd.to_datetime(
        df["month"]
    )

    # Сейчас начинаем только с IEK.
    df = df[
        df["supplier"] == "IEK"
    ].copy()

    # Последняя доступная строка каждого SKU.
    latest = (
        df.sort_values("month")
        .groupby("sku", as_index=False)
        .tail(1)
        .copy()
    )

    print(
        f"Последних SKU IEK: {len(latest):,}"
    )

    # --------------------------------------------------
    # Predict
    # --------------------------------------------------

    X = latest[FEATURES].copy()

    for col in CATEGORICAL:
        X[col] = (
            X[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

    forecast = model.predict(X)

    latest["forecast"] = np.clip(
        forecast,
        0,
        None
    )

    # --------------------------------------------------
    # MOQ
    # --------------------------------------------------

    moq = load_moq()

    latest = latest.merge(
        moq,
        on="sku",
        how="left"
    )

    # --------------------------------------------------
    # Incoming
    # --------------------------------------------------

    incoming = load_incoming()

    latest = latest.merge(
        incoming,
        on="sku",
        how="left"
    )

    latest["incoming"] = (
        latest["incoming"]
        .fillna(0)
        .clip(lower=0)
    )

    # --------------------------------------------------
    # Current stock
    # --------------------------------------------------

    latest["stock"] = (
        pd.to_numeric(
            latest["stock"],
            errors="coerce"
        )
        .fillna(0)
        .clip(lower=0)
    )

    # --------------------------------------------------
    # Safety stock
    #
    # MVP:
    # 50% от rolling std за 6 месяцев.
    # Позже сделаем нормальную service-level формулу.
    # --------------------------------------------------

    latest["safety_stock"] = (
        latest["rolling_std_6"]
        .fillna(0)
        .clip(lower=0)
        * 0.5
    )

    # --------------------------------------------------
    # Net requirement
    # --------------------------------------------------

    latest["net_requirement"] = (
        latest["forecast"]
        + latest["safety_stock"]
        - latest["stock"]
        - latest["incoming"]
    )

    latest["net_requirement"] = (
        latest["net_requirement"]
        .clip(lower=0)
    )

    # --------------------------------------------------
    # MOQ rounding
    # --------------------------------------------------

    latest["recommended_order"] = latest.apply(
        lambda row: round_to_moq(
            row["net_requirement"],
            row["moq"],
        ),
        axis=1,
    )

    # --------------------------------------------------
    # Risk
    # --------------------------------------------------

    latest["available"] = (
        latest["stock"]
        + latest["incoming"]
    )

    latest["risk"] = latest.apply(
        lambda row: risk_level(
            row["forecast"],
            row["available"],
        ),
        axis=1,
    )

    # --------------------------------------------------
    # Reason
    # --------------------------------------------------

    latest["reason"] = latest.apply(
        lambda row: (
            f"Прогноз {row['forecast']:.0f} шт.; "
            f"остаток {row['stock']:.0f}; "
            f"в пути {row['incoming']:.0f}; "
            f"страховой запас "
            f"{row['safety_stock']:.0f}; "
            f"MOQ "
            f"{row['moq'] if pd.notna(row['moq']) else 'не указан'}."
        ),
        axis=1,
    )

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    output_columns = [
        "supplier",
        "sku",
        "product_name",
        "month",
        "forecast",
        "stock",
        "incoming",
        "safety_stock",
        "moq",
        "net_requirement",
        "recommended_order",
        "risk",
        "reason",
    ]

    result = latest[
        output_columns
    ].copy()

    # Сначала наиболее критичные.
    risk_order = {
        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2,
    }

    result["_risk_order"] = (
        result["risk"]
        .map(risk_order)
    )

    result = result.sort_values(
        [
            "_risk_order",
            "recommended_order",
        ],
        ascending=[True, False],
    )

    result = result.drop(
        columns="_risk_order"
    )

    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ ГОТОВЫ")
    print("=" * 70)

    print(
        f"Всего SKU: {len(result):,}"
    )

    print(
        f"Требуют заказа: "
        f"{(result['recommended_order'] > 0).sum():,}"
    )

    print("\nРиски:")

    print(
        result["risk"]
        .value_counts()
        .to_string()
    )

    print("\nTOP-10 рекомендаций:\n")

    print(
        result[
            [
                "sku",
                "forecast",
                "stock",
                "incoming",
                "moq",
                "recommended_order",
                "risk",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nФайл:")
    print(OUTPUT)


if __name__ == "__main__":
    main()