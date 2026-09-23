from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "processed" / "training_dataset.csv"
MODEL_PATH = ROOT / "ml" / "models" / "demand_model.cbm"

OUTPUT = ROOT / "data" / "processed" / "backtest_results.csv"


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


def wape(actual, prediction):

    actual = np.asarray(actual)
    prediction = np.asarray(prediction)

    denominator = np.abs(actual).sum()

    if denominator == 0:
        return np.nan

    return (
        np.abs(actual - prediction).sum()
        / denominator
        * 100
    )


def main():

    print("\nQOR / ProcureAI")
    print("Backtesting\n")

    # ------------------------------------------
    # LOAD
    # ------------------------------------------

    df = pd.read_csv(DATASET)

    df["month"] = pd.to_datetime(df["month"])

    model = CatBoostRegressor()

    model.load_model(MODEL_PATH)

    print("✓ Dataset загружен")
    print("✓ CatBoost загружен")

    # Проверяем последние месяцы.
    test_months = [
        pd.Timestamp("2026-04-01"),
        pd.Timestamp("2026-05-01"),
        pd.Timestamp("2026-06-01"),
        pd.Timestamp("2026-07-01"),
        pd.Timestamp("2026-08-01"),
    ]

    results = []

    for month in test_months:

        test = df[
            df["month"] == month
        ].copy()

        if test.empty:
            continue

        X = test[FEATURES].copy()

        for col in CATEGORICAL:

            X[col] = (
                X[col]
                .fillna("UNKNOWN")
                .astype(str)
            )

        # ------------------------------------------
        # CATBOOST
        # ------------------------------------------

        prediction = model.predict(X)

        prediction = np.clip(
            prediction,
            0,
            None
        )

        actual = (
            test["target_next_month"]
            .to_numpy()
        )

        # ------------------------------------------
        # BASELINE 1
        # Previous month
        # ------------------------------------------

        baseline_previous = (
            test["sales_lag_1"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        # ------------------------------------------
        # BASELINE 2
        # Rolling 3 months
        # ------------------------------------------

        baseline_rolling = (
            test["rolling_mean_3"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        # ------------------------------------------
        # METRICS
        # ------------------------------------------

        catboost_wape = wape(
            actual,
            prediction
        )

        previous_wape = wape(
            actual,
            baseline_previous
        )

        rolling_wape = wape(
            actual,
            baseline_rolling
        )

        catboost_mae = mean_absolute_error(
            actual,
            prediction
        )

        print("\n" + "-" * 60)

        print(
            f"Forecast month: "
            f"{month.strftime('%Y-%m')}"
        )

        print(f"Rows: {len(test):,}")

        print(
            f"CatBoost WAPE: "
            f"{catboost_wape:.2f}%"
        )

        print(
            f"Previous month WAPE: "
            f"{previous_wape:.2f}%"
        )

        print(
            f"Rolling-3 WAPE: "
            f"{rolling_wape:.2f}%"
        )

        results.append(
            {
                "month": month,
                "rows": len(test),

                "catboost_wape": catboost_wape,
                "previous_month_wape": previous_wape,
                "rolling_3_wape": rolling_wape,

                "catboost_mae": catboost_mae,
            }
        )

    # ------------------------------------------
    # RESULT
    # ------------------------------------------

    result = pd.DataFrame(results)

    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 70)
    print("BACKTEST RESULT")
    print("=" * 70)

    print(
        result.to_string(
            index=False
        )
    )

    print("\nAVERAGE:")

    print(
        f"CatBoost WAPE: "
        f"{result['catboost_wape'].mean():.2f}%"
    )

    print(
        f"Previous month: "
        f"{result['previous_month_wape'].mean():.2f}%"
    )

    print(
        f"Rolling 3 months: "
        f"{result['rolling_3_wape'].mean():.2f}%"
    )

    print("\nФайл:")
    print(OUTPUT)


if __name__ == "__main__":
    main()