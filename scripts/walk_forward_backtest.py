from pathlib import Path
import numpy as np
import pandas as pd

from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error


ROOT = Path(__file__).resolve().parent.parent

DATASET = ROOT / "data" / "processed" / "training_dataset.csv"
OUTPUT = ROOT / "data" / "processed" / "walk_forward_results.csv"

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


def prepare_x(df):
    x = df[FEATURES].copy()

    for col in CATEGORICAL:
        x[col] = (
            x[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

    return x


def main():

    print("\nQOR / ProcureAI")
    print("WALK-FORWARD BACKTEST")
    print("Без утечки будущих данных\n")

    df = pd.read_csv(DATASET)

    df["month"] = pd.to_datetime(df["month"])

    test_months = [
        pd.Timestamp("2026-04-01"),
        pd.Timestamp("2026-05-01"),
        pd.Timestamp("2026-06-01"),
        pd.Timestamp("2026-07-01"),
        pd.Timestamp("2026-08-01"),
    ]

    results = []

    for test_month in test_months:

        print("\n" + "=" * 70)
        print(f"TEST MONTH: {test_month.strftime('%Y-%m')}")
        print("=" * 70)

        # Только прошлое.
        train = df[
            df["month"] < test_month
        ].copy()

        # Только текущий тестовый месяц.
        test = df[
            df["month"] == test_month
        ].copy()

        if train.empty or test.empty:
            print("Нет данных — пропускаем")
            continue

        print(
            f"Train period: "
            f"{train['month'].min().date()} → "
            f"{train['month'].max().date()}"
        )

        print(f"Train rows: {len(train):,}")
        print(f"Test rows:  {len(test):,}")

        X_train = prepare_x(train)
        y_train = train["target_next_month"]

        X_test = prepare_x(test)
        y_test = test["target_next_month"].to_numpy()

        # ---------------------------------------
        # Новая модель для КАЖДОГО месяца.
        # ---------------------------------------

        model = CatBoostRegressor(
            iterations=900,
            learning_rate=0.05,
            depth=8,
            loss_function="MAE",
            eval_metric="MAE",
            l2_leaf_reg=5,
            random_seed=42,
            verbose=False,
            allow_writing_files=False,
        )

        print("Обучаем CatBoost...")

        model.fit(
            X_train,
            y_train,
            cat_features=CATEGORICAL,
            verbose=False,
        )

        prediction = model.predict(X_test)

        prediction = np.clip(
            prediction,
            0,
            None,
        )

        # ---------------------------------------
        # Baseline: прошлый месяц
        # ---------------------------------------

        previous = (
            test["sales_lag_1"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        # ---------------------------------------
        # Baseline: среднее 3 месяца
        # ---------------------------------------

        rolling3 = (
            test["rolling_mean_3"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        cb_wape = wape(
            y_test,
            prediction,
        )

        previous_wape = wape(
            y_test,
            previous,
        )

        rolling_wape = wape(
            y_test,
            rolling3,
        )

        cb_mae = mean_absolute_error(
            y_test,
            prediction,
        )

        print("\nRESULT:")

        print(
            f"CatBoost WAPE:       "
            f"{cb_wape:.2f}%"
        )

        print(
            f"Previous month WAPE: "
            f"{previous_wape:.2f}%"
        )

        print(
            f"Rolling-3 WAPE:      "
            f"{rolling_wape:.2f}%"
        )

        results.append(
            {
                "test_month": test_month,
                "train_until": train["month"].max(),
                "train_rows": len(train),
                "test_rows": len(test),
                "catboost_wape": cb_wape,
                "previous_wape": previous_wape,
                "rolling3_wape": rolling_wape,
                "catboost_mae": cb_mae,
            }
        )

    result = pd.DataFrame(results)

    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n\n" + "=" * 70)
    print("FINAL WALK-FORWARD RESULT")
    print("=" * 70)

    print(
        result.to_string(
            index=False
        )
    )

    print("\nAVERAGE:")

    catboost_average = (
        result["catboost_wape"].mean()
    )

    previous_average = (
        result["previous_wape"].mean()
    )

    rolling_average = (
        result["rolling3_wape"].mean()
    )

    print(
        f"CatBoost:       "
        f"{catboost_average:.2f}%"
    )

    print(
        f"Previous month: "
        f"{previous_average:.2f}%"
    )

    print(
        f"Rolling 3:      "
        f"{rolling_average:.2f}%"
    )

    print("\nУлучшение относительно baseline:")

    print(
        f"vs previous month: "
        f"{previous_average - catboost_average:.2f} п.п."
    )

    print(
        f"vs rolling-3: "
        f"{rolling_average - catboost_average:.2f} п.п."
    )

    print("\nРезультат сохранён:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
    