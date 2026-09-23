from pathlib import Path

import numpy as np
import pandas as pd

from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error


ROOT = Path(__file__).resolve().parent.parent

DATASET = (
    ROOT
    / "data"
    / "processed"
    / "training_dataset_v2.csv"
)

OUTPUT = (
    ROOT
    / "data"
    / "processed"
    / "walk_forward_v2_results.csv"
)


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


def wape(actual, prediction):
    actual = np.asarray(
        actual,
        dtype=float,
    )

    prediction = np.asarray(
        prediction,
        dtype=float,
    )

    denominator = np.abs(
        actual
    ).sum()

    if denominator == 0:
        return np.nan

    return (
        np.abs(
            actual - prediction
        ).sum()
        / denominator
        * 100
    )


def prepare_x(df):
    x = df[
        FEATURES
    ].copy()

    for col in CATEGORICAL:
        x[col] = (
            x[col]
            .fillna("UNKNOWN")
            .astype(str)
        )

    return x


def main():
    print(
        "\nQOR / ProcureAI",
        flush=True,
    )

    print(
        "WALK-FORWARD V2",
        flush=True,
    )

    print(
        "Outlier + Stockout + Seasonality\n",
        flush=True,
    )

    # ========================================================
    # LOAD DATA
    # ========================================================

    df = pd.read_csv(
        DATASET
    )

    df["month"] = pd.to_datetime(
        df["month"]
    )

    print(
        f"Dataset rows: {len(df):,}",
        flush=True,
    )

    print(
        f"SKU: {df['sku'].nunique():,}",
        flush=True,
    )

    # ========================================================
    # MONTHS
    # ========================================================

    test_months = [
        pd.Timestamp("2026-04-01"),
        pd.Timestamp("2026-05-01"),
        pd.Timestamp("2026-06-01"),
        pd.Timestamp("2026-07-01"),
        pd.Timestamp("2026-08-01"),
    ]

    results = []

    # ========================================================
    # WALK FORWARD
    # ========================================================

    for test_month in test_months:
        print(
            "\n" + "=" * 70,
            flush=True,
        )

        print(
            f"TEST MONTH: "
            f"{test_month.strftime('%Y-%m')}",
            flush=True,
        )

        print(
            "=" * 70,
            flush=True,
        )

        # ----------------------------------------------------
        # STRICT TEMPORAL SPLIT
        # ----------------------------------------------------

        train = df[
            df["month"] < test_month
        ].copy()

        test = df[
            df["month"] == test_month
        ].copy()

        if train.empty or test.empty:
            print(
                "Нет данных — пропускаем.",
                flush=True,
            )
            continue

        print(
            f"Train period: "
            f"{train['month'].min().date()} "
            f"→ "
            f"{train['month'].max().date()}",
            flush=True,
        )

        print(
            f"Train rows: {len(train):,}",
            flush=True,
        )

        print(
            f"Test rows: {len(test):,}",
            flush=True,
        )

        # ----------------------------------------------------
        # X / Y
        # ----------------------------------------------------

        X_train = prepare_x(
            train
        )

        y_train = (
            train[
                "target_next_month"
            ]
            .astype(float)
        )

        X_test = prepare_x(
            test
        )

        y_test = (
            test[
                "target_next_month"
            ]
            .astype(float)
            .to_numpy()
        )

        # ----------------------------------------------------
        # MODEL
        # ----------------------------------------------------

        model = CatBoostRegressor(
            iterations=1200,
            learning_rate=0.04,
            depth=8,

            loss_function="MAE",
            eval_metric="MAE",

            l2_leaf_reg=6,

            random_seed=42,

            verbose=False,

            allow_writing_files=False,
        )

        print(
            "Обучаем CatBoost V2...",
            flush=True,
        )

        model.fit(
            X_train,
            y_train,

            cat_features=CATEGORICAL,

            verbose=False,
        )

        # ----------------------------------------------------
        # CATBOOST
        # ----------------------------------------------------

        prediction = model.predict(
            X_test
        )

        prediction = np.clip(
            prediction,
            0,
            None,
        )

        # ----------------------------------------------------
        # PREVIOUS MONTH BASELINE
        # ----------------------------------------------------

        previous = (
            test["demand_lag_1"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        # ----------------------------------------------------
        # ROLLING 3 BASELINE
        # ----------------------------------------------------

        rolling3 = (
            test["rolling_mean_3"]
            .fillna(0)
            .clip(lower=0)
            .to_numpy()
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # SPECIAL GROUP METRICS
        # ----------------------------------------------------

        stockout_mask = (
            test[
                "stockout_flag_v2"
            ].to_numpy()
            == 1
        )

        outlier_mask = (
            test[
                "outlier_flag"
            ].to_numpy()
            == 1
        )

        stockout_wape = np.nan

        if stockout_mask.sum() > 0:
            stockout_wape = wape(
                y_test[
                    stockout_mask
                ],
                prediction[
                    stockout_mask
                ],
            )

        outlier_wape = np.nan

        if outlier_mask.sum() > 0:
            outlier_wape = wape(
                y_test[
                    outlier_mask
                ],
                prediction[
                    outlier_mask
                ],
            )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        print(
            "\nRESULT:",
            flush=True,
        )

        print(
            f"CatBoost V2 WAPE:       "
            f"{cb_wape:.2f}%",
            flush=True,
        )

        print(
            f"Previous month WAPE:    "
            f"{previous_wape:.2f}%",
            flush=True,
        )

        print(
            f"Rolling-3 WAPE:         "
            f"{rolling_wape:.2f}%",
            flush=True,
        )

        print(
            f"MAE:                    "
            f"{cb_mae:.2f}",
            flush=True,
        )

        print(
            f"Stockout rows:          "
            f"{stockout_mask.sum():,}",
            flush=True,
        )

        if not np.isnan(
            stockout_wape
        ):
            print(
                f"Stockout WAPE:          "
                f"{stockout_wape:.2f}%",
                flush=True,
            )

        print(
            f"Outlier rows:           "
            f"{outlier_mask.sum():,}",
            flush=True,
        )

        if not np.isnan(
            outlier_wape
        ):
            print(
                f"Outlier WAPE:           "
                f"{outlier_wape:.2f}%",
                flush=True,
            )

        # ----------------------------------------------------
        # STORE
        # ----------------------------------------------------

        results.append(
            {
                "test_month": test_month,
                "train_until":
                    train["month"].max(),

                "train_rows":
                    len(train),

                "test_rows":
                    len(test),

                "catboost_v2_wape":
                    cb_wape,

                "previous_wape":
                    previous_wape,

                "rolling3_wape":
                    rolling_wape,

                "catboost_v2_mae":
                    cb_mae,

                "stockout_rows":
                    int(
                        stockout_mask.sum()
                    ),

                "stockout_wape":
                    stockout_wape,

                "outlier_rows":
                    int(
                        outlier_mask.sum()
                    ),

                "outlier_wape":
                    outlier_wape,
            }
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result = pd.DataFrame(
        results
    )

    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\n\n" + "=" * 70,
        flush=True,
    )

    print(
        "FINAL WALK-FORWARD V2",
        flush=True,
    )

    print(
        "=" * 70,
        flush=True,
    )

    print(
        result.to_string(
            index=False
        ),
        flush=True,
    )

    # ========================================================
    # AVERAGES
    # ========================================================

    cb_average = (
        result[
            "catboost_v2_wape"
        ].mean()
    )

    previous_average = (
        result[
            "previous_wape"
        ].mean()
    )

    rolling_average = (
        result[
            "rolling3_wape"
        ].mean()
    )

    print(
        "\nAVERAGE:",
        flush=True,
    )

    print(
        f"CatBoost V2:    "
        f"{cb_average:.2f}%",
        flush=True,
    )

    print(
        f"Previous month: "
        f"{previous_average:.2f}%",
        flush=True,
    )

    print(
        f"Rolling 3:      "
        f"{rolling_average:.2f}%",
        flush=True,
    )

    print(
        "\nImprovement:",
        flush=True,
    )

    print(
        f"vs previous: "
        f"{previous_average - cb_average:.2f} п.п.",
        flush=True,
    )

    print(
        f"vs rolling-3: "
        f"{rolling_average - cb_average:.2f} п.п.",
        flush=True,
    )

    # ========================================================
    # V1 REFERENCE
    # ========================================================

    print(
        "\nV1 REFERENCE:",
        flush=True,
    )

    print(
        "V1 walk-forward WAPE: 36.65%",
        flush=True,
    )

    print(
        f"V2 walk-forward WAPE: "
        f"{cb_average:.2f}%",
        flush=True,
    )

    print(
        "\nВнимание: V1 и V2 имеют разные targets, "
        "поэтому прямое сравнение WAPE является "
        "диагностическим, а не строгим A/B тестом.",
        flush=True,
    )

    # ========================================================
    # SPECIAL METRICS
    # ========================================================

    print(
        "\nSPECIAL GROUPS:",
        flush=True,
    )

    if (
        "stockout_wape"
        in result.columns
    ):
        print(
            f"Average stockout WAPE: "
            f"{result['stockout_wape'].mean():.2f}%",
            flush=True,
        )

    if (
        "outlier_wape"
        in result.columns
    ):
        print(
            f"Average outlier WAPE: "
            f"{result['outlier_wape'].mean():.2f}%",
            flush=True,
        )

    # ========================================================
    # SAVE
    # ========================================================

    print(
        "\nСохранено:",
        flush=True,
    )

    print(
        OUTPUT,
        flush=True,
    )


if __name__ == "__main__":
    main()