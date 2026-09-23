from pathlib import Path

import numpy as np
import pandas as pd

from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "processed" / "training_dataset.csv"

MODEL_DIR = ROOT / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "demand_model.cbm"


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

CATEGORICAL = [
    "supplier",
    "sku",
]


def wape(y_true, y_pred):
    denominator = np.abs(y_true).sum()

    if denominator == 0:
        return np.nan

    return (
        np.abs(y_true - y_pred).sum()
        / denominator
        * 100
    )


def main():

    print("\nQOR / ProcureAI")
    print("CatBoost Demand Forecast Training\n")

    print("Читаем dataset...")

    df = pd.read_csv(DATASET)

    df["month"] = pd.to_datetime(df["month"])

    print(f"Всего строк: {len(df):,}")
    print(f"SKU: {df['sku'].nunique():,}")

    # -------------------------------------------------
    # TEMPORAL SPLIT
    #
    # Train:
    # всё до июня 2026 включительно
    #
    # Validation:
    # июль + август 2026
    # -------------------------------------------------

    split_date = pd.Timestamp("2026-07-01")

    train = df[
        df["month"] < split_date
    ].copy()

    valid = df[
        df["month"] >= split_date
    ].copy()

    print("\nTemporal split:")
    print(
        f"TRAIN: "
        f"{train['month'].min().date()} "
        f"→ {train['month'].max().date()}"
    )

    print(
        f"VALID: "
        f"{valid['month'].min().date()} "
        f"→ {valid['month'].max().date()}"
    )

    print(f"\nTrain rows: {len(train):,}")
    print(f"Valid rows: {len(valid):,}")

    X_train = train[FEATURES].copy()
    y_train = train["target_next_month"]

    X_valid = valid[FEATURES].copy()
    y_valid = valid["target_next_month"]

    # CatBoost categorical values должны быть строками.
    for col in CATEGORICAL:

        X_train[col] = (
            X_train[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

        X_valid[col] = (
            X_valid[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

    print("\nОбучаем CatBoost...\n")

    model = CatBoostRegressor(
        iterations=1500,
        learning_rate=0.04,
        depth=8,

        loss_function="MAE",
        eval_metric="MAE",

        l2_leaf_reg=5,

        random_seed=42,

        verbose=100,

        allow_writing_files=False,
    )

    model.fit(
        X_train,
        y_train,

        cat_features=CATEGORICAL,

        eval_set=(X_valid, y_valid),

        early_stopping_rounds=150,

        verbose=100,
    )

    # -------------------------------------------------
    # Prediction
    # -------------------------------------------------

    predictions = model.predict(X_valid)

    # Спрос не может быть отрицательным.
    predictions = np.clip(
        predictions,
        0,
        None,
    )

    # -------------------------------------------------
    # Metrics
    # -------------------------------------------------

    mae = mean_absolute_error(
        y_valid,
        predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_valid,
            predictions,
        )
    )

    metric_wape = wape(
        y_valid.to_numpy(),
        predictions,
    )

    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТ")
    print("=" * 70)

    print(f"MAE:  {mae:,.2f}")
    print(f"RMSE: {rmse:,.2f}")
    print(f"WAPE: {metric_wape:,.2f}%")

    # -------------------------------------------------
    # Baseline
    #
    # Просто считаем, что следующий месяц =
    # предыдущий месяц.
    # -------------------------------------------------

    baseline = (
        X_valid["sales_lag_1"]
        .fillna(0)
        .clip(lower=0)
        .to_numpy()
    )

    baseline_mae = mean_absolute_error(
        y_valid,
        baseline,
    )

    baseline_wape = wape(
        y_valid.to_numpy(),
        baseline,
    )

    print("\nBASELINE (предыдущий месяц):")

    print(
        f"MAE:  {baseline_mae:,.2f}"
    )

    print(
        f"WAPE: {baseline_wape:,.2f}%"
    )

    print("\nСравнение:")

    if metric_wape < baseline_wape:
        improvement = (
            baseline_wape - metric_wape
        )

        print(
            f"CatBoost лучше baseline "
            f"на {improvement:.2f} процентных пункта."
        )

    else:
        print(
            "Baseline пока лучше CatBoost — "
            "нужно улучшать features/model."
        )

    # -------------------------------------------------
    # Save model
    # -------------------------------------------------

    model.save_model(MODEL_PATH)

    print("\nМодель сохранена:")
    print(MODEL_PATH)

    # -------------------------------------------------
    # Сохраняем validation predictions
    # -------------------------------------------------

    result = valid[
        [
            "supplier",
            "sku",
            "product_name",
            "month",
            "sales",
            "target_next_month",
        ]
    ].copy()

    result["prediction"] = predictions

    result["absolute_error"] = np.abs(
        result["target_next_month"]
        - result["prediction"]
    )

    prediction_path = (
        ROOT
        / "data"
        / "processed"
        / "validation_predictions.csv"
    )

    result.to_csv(
        prediction_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nValidation predictions:")
    print(prediction_path)

    # -------------------------------------------------
    # Feature importance
    # -------------------------------------------------

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance": model.get_feature_importance(),
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False,
    )

    print("\nTOP FEATURES:\n")

    print(
        importance.head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()