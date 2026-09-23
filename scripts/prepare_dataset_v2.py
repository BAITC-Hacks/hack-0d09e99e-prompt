from pathlib import Path
import re

import numpy as np
import pandas as pd


# ============================================================
# PATHS
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


# ============================================================
# MONTHS
# ============================================================

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
# FILE HELPERS
# ============================================================

def find_file(directory: Path, keyword: str) -> Path:
    for path in directory.glob("*.xlsx"):
        if keyword.lower() in path.name.lower():
            return path

    raise FileNotFoundError(
        f"Не найден файл '{keyword}' в {directory}"
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
        f"Не удалось найти SKU колонку. "
        f"Колонки: {list(df.columns)}"
    )


def detect_name_column(df):
    for col in df.columns:
        text = str(col).lower()

        if "номенклатура" in text and "код" not in text:
            return col

    return None


# ============================================================
# LOAD MONTHLY EXCEL
# ============================================================

def load_monthly(path: Path, value_name: str):

    print(f"Читаем: {path.name}")

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
            code_col: "sku"
        }
    )

    if name_col:

        long_df = long_df.rename(
            columns={
                name_col: "product_name"
            }
        )

    else:

        long_df["product_name"] = ""

    long_df["sku"] = (
        long_df["sku"]
        .astype(str)
        .str.strip()
    )

    # Убираем мусорные SKU
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

def load_supplier(supplier, directory):

    print("\n" + "=" * 70)
    print(f"SUPPLIER: {supplier}")
    print("=" * 70)

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

    # --------------------------------------------------------
    # Sales aggregation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Stock aggregation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    df = sales.merge(
        stock,
        on=[
            "sku",
            "month",
        ],
        how="left",
    )

    df["supplier"] = supplier

    # --------------------------------------------------------
    # Returns
    # --------------------------------------------------------

    df["return_qty"] = np.where(
        df["sales_raw"] < 0,
        np.abs(df["sales_raw"]),
        0,
    )

    # Отрицательный спрос невозможен.
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

    # --------------------------------------------------------
    # Rolling median
    #
    # Только прошлые месяцы.
    # --------------------------------------------------------

    rolling_median = (
        sales
        .shift(1)
        .rolling(
            window=6,
            min_periods=3,
        )
        .median()
    )

    # --------------------------------------------------------
    # Rolling MAD
    # --------------------------------------------------------

    def mad(values):

        median = np.median(values)

        return np.median(
            np.abs(
                values - median
            )
        )

    rolling_mad = (
        sales
        .shift(1)
        .rolling(
            window=6,
            min_periods=3,
        )
        .apply(
            mad,
            raw=True,
        )
    )

    # --------------------------------------------------------
    # Outlier threshold
    # --------------------------------------------------------

    mad_limit = (
        rolling_median
        + 6 * rolling_mad
    )

    # Если MAD равен 0, нужен fallback.
    fallback_limit = np.maximum(
        rolling_median * 4,
        rolling_median + 10,
    )

    upper_limit = mad_limit.copy()

    bad_mad = (
        rolling_mad.isna()
        | (rolling_mad <= 0)
    )

    upper_limit.loc[bad_mad] = (
        fallback_limit.loc[bad_mad]
    )

    # --------------------------------------------------------
    # Flag
    # --------------------------------------------------------

    group["outlier_threshold"] = (
        upper_limit
    )

    group["outlier_flag"] = (
        upper_limit.notna()
        & (sales > upper_limit)
    ).astype(int)

    # --------------------------------------------------------
    # Correct
    # --------------------------------------------------------

    corrected = sales.copy()

    outlier_mask = (
        group["outlier_flag"] == 1
    )

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

    # --------------------------------------------------------
    # Expected demand
    #
    # Используем median последних 3 месяцев.
    # Только прошлые месяцы.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Stockout flag
    # --------------------------------------------------------

    group["stockout_flag_v2"] = (
        stock <= 0
    ).astype(int)

    # --------------------------------------------------------
    # Lost demand
    # --------------------------------------------------------

    expected_demand = (
        expected_demand
        .fillna(
            group["sales_clean"]
        )
        .clip(lower=0)
    )

    lost_demand = (
        expected_demand
        - group["sales_clean"]
    ).clip(lower=0)

    stockout_mask = (
        group["stockout_flag_v2"] == 1
    )

    group["lost_demand_estimate"] = 0.0

    group.loc[
        stockout_mask,
        "lost_demand_estimate"
    ] = lost_demand.loc[
        stockout_mask
    ]

    # --------------------------------------------------------
    # Adjusted demand
    # --------------------------------------------------------

    group["demand_adjusted"] = (
        group["sales_clean"]
        + group["lost_demand_estimate"]
    )

    return group


# ============================================================
# SAFE GROUP PROCESSING
#
# Вместо groupby.apply(include_groups=False)
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

        corrected = function(
            group_df.copy()
        )

        # Гарантированно возвращаем ключи.
        corrected["supplier"] = supplier
        corrected["sku"] = sku

        parts.append(
            corrected
        )

    if not parts:
        return df.copy()

    return pd.concat(
        parts,
        ignore_index=True,
    )


# ============================================================
# FEATURES
# ============================================================

def add_features(df):

    # ========================================================
    # OUTLIERS
    # ========================================================

    print("\nOutlier correction...")

    df = process_groups(
        df,
        correct_outliers,
    )

    outlier_count = int(
        df["outlier_flag"].sum()
    )

    outlier_percent = (
        outlier_count
        / len(df)
        * 100
    )

    print(
        f"Найдено outlier-месяцев: "
        f"{outlier_count:,}"
    )

    print(
        f"Доля outliers: "
        f"{outlier_percent:.2f}%"
    )

    # ========================================================
    # STOCKOUT
    # ========================================================

    print("\nStockout correction...")

    df = process_groups(
        df,
        correct_stockouts,
    )

    stockout_count = int(
        df["stockout_flag_v2"].sum()
    )

    stockout_percent = (
        stockout_count
        / len(df)
        * 100
    )

    lost_demand_total = (
        df["lost_demand_estimate"]
        .sum()
    )

    print(
        f"Stockout observations: "
        f"{stockout_count:,}"
    )

    print(
        f"Доля stockouts: "
        f"{stockout_percent:.2f}%"
    )

    print(
        f"Estimated lost demand: "
        f"{lost_demand_total:,.2f}"
    )

    # ========================================================
    # SORT
    # ========================================================

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

    # ========================================================
    # LAGS
    # ========================================================

    print("\nСоздаём lag features...")

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

    # ========================================================
    # ROLLING FEATURES
    # ========================================================

    print("Создаём rolling features...")

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

    # ========================================================
    # GROWTH
    # ========================================================

    print("Создаём growth features...")

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

    # ========================================================
    # CALENDAR
    # ========================================================

    print("Создаём calendar features...")

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

    # ========================================================
    # SKU SEASONALITY
    # ========================================================

    print("Создаём seasonality features...")

    # Среднее по всей предыдущей истории SKU.
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

    # Среднее по конкретному месяцу года.
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

    # ========================================================
    # OUTLIER HISTORY FEATURES
    # ========================================================

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

    # ========================================================
    # TARGET
    #
    # ВАЖНО:
    # модель учится прогнозировать скорректированный
    # регулярный спрос следующего месяца.
    # ========================================================

    df["target_next_month"] = (
        group["demand_adjusted"]
        .shift(-1)
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("\nQOR / ProcureAI")
    print("PREPARE DATASET V2\n")

    frames = []

    # ========================================================