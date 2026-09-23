from pathlib import Path
import re

import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTPUT_DIR / "training_dataset_v2.csv"

SUPPLIERS = {
    "IEK": DATA_DIR / "IEK",
    "Systeme": DATA_DIR / "Systeme",
}

MONTHS = {
    "янв": 1,
    "фев": 2,
    "мар": 3,
    "апр": 4,
    "май": 5,
    "июн": 6,
    "июл": 7,
    "авг": 8,
    "сен": 9,
    "окт": 10,
    "ноя": 11,
    "дек": 12,
}


# ============================================================
# HELPERS
# ============================================================

def find_file(directory: Path, keyword: str) -> Path:
    for path in directory.glob("*.xlsx"):
        if keyword.lower() in path.name.lower():
            return path

    raise FileNotFoundError(
        f"Не найден Excel '{keyword}' в {directory}"
    )


def parse_month_column(column):
    text = str(column).lower().strip()

    year_match = re.search(r"(20\d{2})", text)

    if not year_match:
        return None

    year = int(year_match.group(1))

    for prefix, month in MONTHS.items():
        if prefix in text:
            return pd.Timestamp(
                year=year,
                month=month,
                day=1,
            )

    return None


def detect_code_column(df):
    candidates = [
        "Номенклатура.Код",
        "Код 1с",
        "Код 1С",
        "Код",
    ]

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    for col in df.columns:
        text = str(col).lower()

        if "код" in text and "номенклат" in text:
            return col

    raise ValueError(
        f"Не найдена колонка SKU: {list(df.columns)}"
    )


def detect_name_column(df):
    for col in df.columns:
        text = str(col).lower()

        if "номенклатура" in text and "код" not in text:
            return col

    return None


# ============================================================
# LOAD MONTHLY DATA
# ============================================================

def load_monthly(path: Path, value_name: str):
    print(f"Читаем: {path.name}", flush=True)

    df = pd.read_excel(
        path,
        sheet_name=0,
    )

    code_col = detect_code_column(df)
    name_col = detect_name_column(df)

    month_columns = {}

    for col in df.columns:
        parsed = parse_month_column(col)

        if parsed is not None:
            month_columns[col] = parsed

    if not month_columns:
        raise ValueError(
            f"Не найдены месячные колонки: {path.name}"
        )

    id_vars = [code_col]

    if name_col:
        id_vars.append(name_col)

    long_df = df.melt(
        id_vars=id_vars,
        value_vars=list(month_columns.keys()),
        var_name="month_original",
        value_name=value_name,
    )

    long_df["month"] = (
        long_df["month_original"]
        .map(month_columns)
    )

    long_df = long_df.rename(
        columns={
            code_col: "sku",
        }
    )

    if name_col:
        long_df = long_df.rename(
            columns={
                name_col: "product_name",
            }
        )
    else:
        long_df["product_name"] = ""

    long_df["sku"] = (
        long_df["sku"]
        .astype(str)
        .str.strip()
    )

    long_df = long_df[
        (long_df["sku"] != "")
        & (long_df["sku"].str.lower() != "nan")
    ].copy()

    long_df[value_name] = pd.to_numeric(
        long_df[value_name],
        errors="coerce",
    ).fillna(0)

    return long_df[
        [
            "sku",
            "product_name",
            "month",
            value_name,
        ]
    ]


# ============================================================
# LOAD SUPPLIER
# ============================================================

def load_supplier(supplier: str, directory: Path):
    print("\n" + "=" * 70, flush=True)
    print(f"SUPPLIER: {supplier}", flush=True)
    print("=" * 70, flush=True)

    sales_file = find_file(
        directory,
        "ежемесячные продажи",
    )

    stock_file = find_file(
        directory,
        "ежемесячные остатки",
    )

    sales = load_monthly(
        sales_file,
        "sales_raw",
    )

    stock = load_monthly(
        stock_file,
        "stock",
    )

    sales = (
        sales.groupby(
            [
                "sku",
                "product_name",
                "month",
            ],
            as_index=False,
        )["sales_raw"]
        .sum()
    )

    stock = (
        stock.groupby(
            [
                "sku",
                "month",
            ],
            as_index=False,
        )["stock"]
        .sum()
    )

    df = sales.merge(
        stock,
        on=[
            "sku",
            "month",
        ],
        how="left",
    )

    df["supplier"] = supplier

    # Отрицательные значения сохраняем как возвраты.
    df["return_qty"] = np.where(
        df["sales_raw"] < 0,
        np.abs(df["sales_raw"]),
        0,
    )

    # Отрицательного спроса для forecast быть не может.
    df["sales_positive"] = (
        df["sales_raw"]
        .clip(lower=0)
        .astype(float)
    )

    df["stock"] = pd.to_numeric(
        df["stock"],
        errors="coerce",
    )

    return df


# ============================================================
# OUTLIER CORRECTION
# ============================================================

def correct_outliers(group):
    group = (
        group
        .sort_values("month")
        .copy()
    )

    sales = (
        group["sales_positive"]
        .astype(float)
    )

    # Используем только прошлое.
    previous = sales.shift(1)

    rolling_median = (
        previous
        .rolling(
            window=6,
            min_periods=3,
        )
        .median()
    )

    def mad(values):
        median = np.median(values)

        return np.median(
            np.abs(
                values - median
            )
        )

    rolling_mad = (
        previous
        .rolling(
            window=6,
            min_periods=3,
        )
        .apply(
            mad,
            raw=True,
        )
    )

    # Основной robust threshold.
    mad_threshold = (
        rolling_median
        + 6 * rolling_mad
    )

    # Если MAD == 0.
    fallback_threshold = np.maximum(
        rolling_median * 4,
        rolling_median + 10,
    )

    threshold = mad_threshold.copy()

    fallback_mask = (
        rolling_mad.isna()
        | (rolling_mad <= 0)
    )

    threshold.loc[fallback_mask] = (
        fallback_threshold.loc[fallback_mask]
    )

    group["outlier_threshold"] = threshold

    group["outlier_flag"] = (
        threshold.notna()
        & (sales > threshold)
    ).astype(int)

    corrected = sales.copy()

    outlier_mask = (
        group["outlier_flag"] == 1
    )

    # Аномальную продажу заменяем robust median.
    corrected.loc[outlier_mask] = (
        rolling_median.loc[outlier_mask]
    )

    group["sales_clean"] = (
        corrected
        .fillna(sales)
        .clip(lower=0)
    )

    return group


# ============================================================
# STOCKOUT CORRECTION
# ============================================================

def correct_stockouts(group):
    group = (
        group
        .sort_values("month")
        .copy()
    )

    # Ожидаемый спрос по предыдущим 3 месяцам.
    expected_demand = (
        group["sales_clean"]
        .shift(1)
        .rolling(
            window=3,
            min_periods=2,
        )
        .median()
    )

    stock = (
        group["stock"]
        .fillna(0)
    )

    group["stockout_flag_v2"] = (
        stock <= 0
    ).astype(int)

    expected_demand = (
        expected_demand
        .fillna(
            group["sales_clean"]
        )
        .clip(lower=0)
    )

    potential_lost = (
        expected_demand
        - group["sales_clean"]
    ).clip(lower=0)

    group["lost_demand_estimate"] = 0.0

    mask = (
        group["stockout_flag_v2"] == 1
    )

    group.loc[
        mask,
        "lost_demand_estimate",
    ] = potential_lost.loc[mask]

    group["demand_adjusted"] = (
        group["sales_clean"]
        + group["lost_demand_estimate"]
    )

    return group


# ============================================================
# SAFE GROUP PROCESSOR
# ============================================================

def process_groups(df, function):
    parts = []

    grouped = df.groupby(
        [
            "supplier",
            "sku",
        ],
        sort=False,
    )

    for (supplier, sku), group_df in grouped:
        result = function(
            group_df.copy()
        )

        # pandas 3.x safe:
        # явно возвращаем группировочные ключи.
        result["supplier"] = supplier
        result["sku"] = sku

        parts.append(result)

    if not parts:
        return df.copy()

    return pd.concat(
        parts,
        ignore_index=True,
    )


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def add_features(df):
    # --------------------------------------------------------
    # OUTLIERS
    # --------------------------------------------------------

    print(
        "\nOutlier correction...",
        flush=True,
    )

    df = process_groups(
        df,
        correct_outliers,
    )

    outliers = int(
        df["outlier_flag"].sum()
    )

    print(
        f"Найдено outlier-месяцев: {outliers:,}",
        flush=True,
    )

    print(
        f"Доля outliers: "
        f"{outliers / len(df) * 100:.2f}%",
        flush=True,
    )

    # --------------------------------------------------------
    # STOCKOUT
    # --------------------------------------------------------

    print(
        "\nStockout correction...",
        flush=True,
    )

    df = process_groups(
        df,
        correct_stockouts,
    )

    stockouts = int(
        df["stockout_flag_v2"].sum()
    )

    lost_demand = (
        df["lost_demand_estimate"]
        .sum()
    )

    print(
        f"Stockout observations: {stockouts:,}",
        flush=True,
    )

    print(
        f"Доля stockouts: "
        f"{stockouts / len(df) * 100:.2f}%",
        flush=True,
    )

    print(
        f"Estimated lost demand: "
        f"{lost_demand:,.2f}",
        flush=True,
    )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df = (
        df.sort_values(
            [
                "supplier",
                "sku",
                "month",
            ]
        )
        .reset_index(drop=True)
    )

    group = df.groupby(
        [
            "supplier",
            "sku",
        ],
        group_keys=False,
    )

    # --------------------------------------------------------
    # LAGS
    # --------------------------------------------------------

    print(
        "\nСоздаём lag features...",
        flush=True,
    )

    for lag in [
        1,
        2,
        3,
        6,
        12,
    ]:
        df[f"demand_lag_{lag}"] = (
            group["demand_adjusted"]
            .shift(lag)
        )

    # --------------------------------------------------------
    # ROLLING
    # --------------------------------------------------------

    print(
        "Создаём rolling features...",
        flush=True,
    )

    df["rolling_mean_3"] = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                3,
                min_periods=1,
            )
            .mean()
        )
    )

    df["rolling_mean_6"] = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                6,
                min_periods=1,
            )
            .mean()
        )
    )

    df["rolling_mean_12"] = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                12,
                min_periods=1,
            )
            .mean()
        )
    )

    df["rolling_std_3"] = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                3,
                min_periods=2,
            )
            .std()
        )
    )

    df["rolling_std_6"] = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .rolling(
                6,
                min_periods=2,
            )
            .std()
        )
    )

    # --------------------------------------------------------
    # GROWTH
    # --------------------------------------------------------

    print(
        "Создаём growth features...",
        flush=True,
    )

    denominator = (
        df["demand_lag_3"]
        .replace(
            0,
            np.nan,
        )
    )

    df["growth_3m"] = (
        (
            df["demand_lag_1"]
            - df["demand_lag_3"]
        )
        / denominator
    )

    df["growth_3m"] = (
        df["growth_3m"]
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .clip(
            lower=-5,
            upper=5,
        )
    )

    # --------------------------------------------------------
    # CALENDAR
    # --------------------------------------------------------

    print(
        "Создаём calendar features...",
        flush=True,
    )

    df["year"] = (
        df["month"].dt.year
    )

    df["month_num"] = (
        df["month"].dt.month
    )

    df["quarter"] = (
        df["month"].dt.quarter
    )

    df["month_sin"] = np.sin(
        2
        * np.pi
        * df["month_num"]
        / 12
    )

    df["month_cos"] = np.cos(
        2
        * np.pi
        * df["month_num"]
        / 12
    )

    # --------------------------------------------------------
    # SEASONALITY
    # --------------------------------------------------------

    print(
        "Создаём seasonality features...",
        flush=True,
    )

    # Среднее по предыдущей истории SKU.
    historical_mean = (
        group["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .expanding(
                min_periods=1
            )
            .mean()
        )
    )

    # История конкретного месяца года.
    month_history = (
        df.groupby(
            [
                "supplier",
                "sku",
                "month_num",
            ]
        )["demand_adjusted"]
        .transform(
            lambda x:
            x.shift(1)
            .expanding(
                min_periods=1
            )
            .mean()
        )
    )

    df["seasonality_index"] = (
        month_history
        / historical_mean.replace(
            0,
            np.nan,
        )
    )

    df["seasonality_index"] = (
        df["seasonality_index"]
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )
        .clip(
            lower=0.25,
            upper=4.0,
        )
        .fillna(1.0)
    )

    # --------------------------------------------------------
    # PREVIOUS FLAGS
    # --------------------------------------------------------

    df["outlier_lag_1"] = (
        group["outlier_flag"]
        .shift(1)
        .fillna(0)
    )

    df["stockout_lag_1"] = (
        group["stockout_flag_v2"]
        .shift(1)
        .fillna(0)
    )

    df["lost_demand_lag_1"] = (
        group["lost_demand_estimate"]
        .shift(1)
        .fillna(0)
    )

    # --------------------------------------------------------
    # TARGET
    # --------------------------------------------------------

    df["target_next_month"] = (
        group["demand_adjusted"]
        .shift(-1)
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "\nQOR / ProcureAI",
        flush=True,
    )

    print(
        "PREPARE DATASET V2\n",
        flush=True,
    )

    frames = []

    # --------------------------------------------------------
    # LOAD SUPPLIERS
    # --------------------------------------------------------

    for supplier, directory in SUPPLIERS.items():
        if not directory.exists():
            raise FileNotFoundError(
                f"Не найдена папка: {directory}"
            )

        supplier_df = load_supplier(
            supplier,
            directory,
        )

        frames.append(
            supplier_df
        )

    # --------------------------------------------------------
    # COMBINE
    # --------------------------------------------------------

    df = pd.concat(
        frames,
        ignore_index=True,
    )

    print(
        f"\nИсходных строк: {len(df):,}",
        flush=True,
    )

    print(
        f"Уникальных SKU: "
        f"{df['sku'].nunique():,}",
        flush=True,
    )

    # --------------------------------------------------------
    # FEATURES
    # --------------------------------------------------------

    df = add_features(df)

    # --------------------------------------------------------
    # TRAINING DATASET
    # --------------------------------------------------------

    training = df[        df["target_next_month"].notna()
    ].copy()

    # Для обучения требуем минимум 3 месяца истории.
    training = training[
        training["demand_lag_3"].notna()
    ].copy()

    training = (
        training
        .sort_values(
            [
                "supplier",
                "sku",
                "month",
            ]
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # SAVE DATASET
    # --------------------------------------------------------

    training.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70,
        flush=True,
    )

    print(
        "DATASET V2 ГОТОВ",
        flush=True,
    )

    print(
        "=" * 70,
        flush=True,
    )

    print(
        f"Rows: {len(training):,}",
        flush=True,
    )

    print(
        f"SKU: {training['sku'].nunique():,}",
        flush=True,
    )

    print(
        f"Период: "
        f"{training['month'].min().date()} "
        f"→ "
        f"{training['month'].max().date()}",
        flush=True,
    )

    # --------------------------------------------------------
    # OUTLIERS
    # --------------------------------------------------------

    outliers = int(
        training["outlier_flag"].sum()
    )

    print(
        f"\nOutliers: {outliers:,}",
        flush=True,
    )

    print(
        f"Outlier rate: "
        f"{outliers / len(training) * 100:.2f}%",
        flush=True,
    )

    # --------------------------------------------------------
    # STOCKOUTS
    # --------------------------------------------------------

    stockouts = int(
        training["stockout_flag_v2"].sum()
    )

    print(
        f"Stockouts: {stockouts:,}",
        flush=True,
    )

    print(
        f"Stockout rate: "
        f"{stockouts / len(training) * 100:.2f}%",
        flush=True,
    )

    # --------------------------------------------------------
    # LOST DEMAND
    # --------------------------------------------------------

    lost_demand = (
        training["lost_demand_estimate"]
        .sum()
    )

    print(
        f"Estimated lost demand: "
        f"{lost_demand:,.2f}",
        flush=True,
    )

    # --------------------------------------------------------
    # SUPPLIER STATS
    # --------------------------------------------------------

    print(
        "\nПо поставщикам:",
        flush=True,
    )

    supplier_stats = (
        training
        .groupby("supplier")
        .agg(
            rows=("sku", "size"),
            skus=("sku", "nunique"),
            raw_sales=("sales_positive", "sum"),
            adjusted_demand=("demand_adjusted", "sum"),
            outliers=("outlier_flag", "sum"),
            stockouts=("stockout_flag_v2", "sum"),
            lost_demand=("lost_demand_estimate", "sum"),
        )
    )

    print(
        supplier_stats.to_string(),
        flush=True,
    )

    # --------------------------------------------------------
    # DEMAND STATISTICS
    # --------------------------------------------------------

    print(
        "\nAdjusted demand statistics:",
        flush=True,
    )

    print(
        training[
            "demand_adjusted"
        ]
        .describe()
        .to_string(),
        flush=True,
    )

    # --------------------------------------------------------
    # TARGET STATISTICS
    # --------------------------------------------------------

    print(
        "\nTarget statistics:",
        flush=True,
    )

    print(
        training[
            "target_next_month"
        ]
        .describe()
        .to_string(),
        flush=True,
    )

    # --------------------------------------------------------
    # TOP OUTLIERS
    # --------------------------------------------------------

    print(
        "\nTOP-10 OUTLIERS:",
        flush=True,
    )

    top_outliers = training[
        training["outlier_flag"] == 1
    ].copy()

    if not top_outliers.empty:

        top_outliers[
            "outlier_difference"
        ] = (
            top_outliers["sales_positive"]
            - top_outliers["sales_clean"]
        )

        top_outliers = (
            top_outliers
            .sort_values(
                "outlier_difference",
                ascending=False,
            )
            .head(10)
        )

        print(
            top_outliers[
                [
                    "supplier",
                    "sku",
                    "month",
                    "sales_positive",
                    "sales_clean",
                    "outlier_threshold",
                ]
            ]
            .to_string(
                index=False
            ),
            flush=True,
        )

    else:

        print(
            "Outliers не найдены.",
            flush=True,
        )

    # --------------------------------------------------------
    # TOP LOST DEMAND
    # --------------------------------------------------------

    print(
        "\nTOP-10 LOST DEMAND:",
        flush=True,
    )

    top_lost = (
        training
        .sort_values(
            "lost_demand_estimate",
            ascending=False,
        )
        .head(10)
    )

    print(
        top_lost[
            [
                "supplier",
                "sku",
                "month",
                "sales_clean",
                "stock",
                "lost_demand_estimate",
                "demand_adjusted",
            ]
        ]
        .to_string(
            index=False
        ),
        flush=True,
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print(
        "\nФайл сохранён:",
        flush=True,
    )

    print(
        OUTPUT,
        flush=True,
    )

    print(
        "\nСледующий этап: CatBoost V2 training",
        flush=True,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()