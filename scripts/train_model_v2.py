from pathlib import Path

import numpy as np
import pandas as pd

from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATASET = (
    ROOT
    / "data"
    / "processed"
    / "training_dataset_v2.csv"
)

MODEL_DIR = (
    ROOT
    / "ml"
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_PATH = (
    MODEL_DIR
    / "demand_model_v2.cbm"
)

PREDICTIONS_PATH = (
    ROOT
    / "data"
    / "processed"
    / "validation_predictions_v2.csv"
)


# ============================================================
# FEATURES
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
# METRICS
# ============================================================

def wape(y_true, y_pred):

    y_true = np.asarray(
        y_true,
        dtype=float,
    )

    y_pred = np.asarray(
        y_pred,
        dtype=float,
    )

    denominator = (
        np.abs(y_true).sum()
    )

    if denominator == 0:
        return np.nan

    return (
        np.abs(
            y_true - y_pred
        ).sum()
        / denominator
        * 100
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nQOR / ProcureAI",
        flush=True,
    )

    print(
        "CatBoost V2 Training\n",
        flush=True,
    )

    # --------------------------------------------------------
    # LOAD DATASET
    # --------------------------------------------------------

    print(
        "Читаем dataset V2...",
        flush=True,
    )

    df = pd.read_csv(
        DATASET
    )

    df["month"] = pd.to_datetime(
        df["month"]
    )

    print(
        f"Всего строк: "
        f"{len(df):,}",
        flush=True,
    )

    print(
        f"SKU: "
        f"{df['sku'].nunique():,}",
        flush=True,
    )

    # --------------------------------------------------------
    # TEMPORAL SPLIT
    # --------------------------------------------------------

    split_date = pd.Timestamp(
        "2026-07-01"
    )

    train = df[
        df["month"] < split_date
    ].copy()

    valid = df[
        df["month"] >= split_date
    ].copy()

    print(
        "\nTemporal split:",
        flush=True,
    )

    print(
        f"TRAIN: "
        f"{train['month'].min().date()} "
        f"→ "
        f"{train['month'].max().date()}",
        flush=True,
    )

    print(
        f"VALID: "
        f"{valid['month'].min().date()} "
        f"→ "
        f"{valid['month'].max().date()}",
        flush=True,
    )

    print(
        f"\nTrain rows: "
        f"{len(train):,}",
        flush=True,
    )

    print(
        f"Valid rows: "
        f"{len(valid):,}",
        flush=True,
    )

    # --------------------------------------------------------
    # X / Y
    # --------------------------------------------------------

    X_train = (
        train[FEATURES]
        .copy()
    )

    y_train = (
        train["target_next_month"]
        .astype(float)
    )

    X_valid = (
        valid[FEATURES]
        .copy()
    )

    y_valid = (
        valid["target_next_month"]
        .astype(float)
    )

    # --------------------------------------------------------
    # CATEGORICAL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # MODEL
    # --------------------------------------------------------

    print(
        "\nОбучаем CatBoost V2...\n",
        flush=True,
    )

    model = CatBoostRegressor(
        iterations=1800,
        learning_rate=0.035,
        depth=8,

        loss_function="MAE",
        eval_metric="MAE",

        l2_leaf_reg=6,

        random_seed=42,

        allow_writing_files=False,
    )

    model.fit(
        X_train,
        y_train,

        cat_features=CATEGORICAL,

        eval_set=(
            X_valid,
            y_valid,
        ),

        early_stopping_rounds=180,

        verbose=100,
    )

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    predictions = (
        model.predict(
            X_valid
        )
    )

    predictions = np.clip(
        predictions,
        0,
        None,
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

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

    model_wape = wape(
        y_valid,
        predictions,
    )

    # --------------------------------------------------------
    # BASELINE 1
    # --------------------------------------------------------

    previous = (
        X_valid["demand_lag_1"]
        .fillna(0)
        .clip(lower=0)
        .to_numpy()
    )

    previous_mae = (
        mean_absolute_error(
            y_valid,
            previous,
        )
    )

    previous_wape = wape(
        y_valid,
        previous,
    )

    # --------------------------------------------------------
    # BASELINE 2
    # --------------------------------------------------------

    rolling3 = (
        X_valid["rolling_mean_3"]
        .fillna(0)
        .clip(lower=0)
        .to_numpy()
    )

    rolling_wape = wape(
        y_valid,
        rolling3,
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70,
        flush=True,
    )

    print(
        "CATBOOST V2 RESULT",
        flush=True,
    )

    print(
        "=" * 70,
        flush=True,
    )

    print(
        f"MAE:  {mae:,.2f}",
        flush=True,
    )

    print(
        f"RMSE: {rmse:,.2f}",
        flush=True,
    )

    print(
        f"WAPE: {model_wape:.2f}%",
        flush=True,
    )

    print(
        "\nBASELINE — previous month:",
        flush=True,
    )

    print(
        f"MAE:  {previous_mae:,.2f}",
        flush=True,
    )

    print(
        f"WAPE: {previous_wape:.2f}%",
        flush=True,
    )

    print(
        "\nBASELINE — rolling 3:",
        flush=True,
    )

    print(
        f"WAPE: {rolling_wape:.2f}%",
        flush=True,
    )

    # --------------------------------------------------------
    # OLD V1 REFERENCE
    # --------------------------------------------------------

    print(
        "\nV1 reference:",
        flush=True,
    )

    print(
        "WAPE V1 temporal validation: 39.84%",
        flush=True,
    )

    print(
        f"WAPE V2 temporal validation: "
        f"{model_wape:.2f}%",
        flush=True,
    )

    # Важно:
    # V1 и V2 targets отличаются,
    # поэтому это только диагностическое сравнение.
    print(
        "\nВажно: V2 прогнозирует adjusted demand, "
        "а V1 прогнозировала raw demand.",
        flush=True,
    )

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    model.save_model(
        MODEL_PATH
    )

    print(
        "\nМодель сохранена:",
        flush=True,
    )

    print(
        MODEL_PATH,
        flush=True,
    )

    # --------------------------------------------------------
    # SAVE PREDICTIONS
    # --------------------------------------------------------

    result = valid[
        [
            "supplier",
            "sku",
            "product_name",
            "month",

            "sales_raw",
            "sales_clean",

            "outlier_flag",

            "stockout_flag_v2",
            "lost_demand_estimate",

            "demand_adjusted",

            "target_next_month",
        ]
    ].copy()

    result["prediction"] = (
        predictions
    )

    result["absolute_error"] = np.abs(
        result["target_next_month"]
        - result["prediction"]
    )

    result.to_csv(
        PREDICTIONS_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\nPredictions:",
        flush=True,
    )

    print(
        PREDICTIONS_PATH,
        flush=True,
    )

    # --------------------------------------------------------
    # FEATURE IMPORTANCE
    # --------------------------------------------------------

    importance = pd.DataFrame(
        {
            "feature": FEATURES,
            "importance":
                model.get_feature_importance(),
        }
    )

    importance = (
        importance
        .sort_values(
            "importance",
            ascending=False,
        )
    )

    print(
        "\nTOP FEATURES:\n",
        flush=True,
    )

    print(
        importance
        .head(20)
        .to_string(
            index=False
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()