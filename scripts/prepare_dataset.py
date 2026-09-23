from pathlib import Path
import re
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
OUTPUT_DIR = DATA_DIR / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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


def find_file(directory: Path, keyword: str) -> Path:
    """Находит Excel по части названия."""
    keyword = keyword.lower()

    for path in directory.glob("*.xlsx"):
        if keyword in path.name.lower():
            return path

    raise FileNotFoundError(
        f"Не найден файл с ключевым словом '{keyword}' в {directory}"
    )


def parse_month_column(column):
    """
    Преобразует:
    янв. 2024
    февр. 2025
    сент. 2026

    в Timestamp.
    """

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

    # fallback
    for col in df.columns:
        text = str(col).lower()

        if "код" in text and "номенклат" in text:
            return col

    raise ValueError(
        f"Не удалось найти колонку SKU. Колонки: {list(df.columns)}"
    )


def detect_name_column(df):
    for col in df.columns:
        text = str(col).lower()

        if "номенклатура" in text and "код" not in text:
            return col

    return None


def load_monthly_file(path: Path, value_name: str):
    print(f"Читаем: {path.name}")

    # В нужных файлах основная таблица находится на первом листе.
    df = pd.read_excel(path, sheet_name=0)

    code_col = detect_code_column(df)
    name_col = detect_name_column(df)

    month_columns = {}

    for col in df.columns:
        parsed = parse_month_column(col)

        if parsed is not None:
            month_columns[col] = parsed

    if not month_columns:
        raise ValueError(
            f"Не найдены месячные колонки в {path.name}"
        )

    print(f"  SKU колонка: {code_col}")
    print(f"  Найдено месяцев: {len(month_columns)}")

    id_vars = [code_col]

    if name_col:
        id_vars.append(name_col)

    long_df = df.melt(
        id_vars=id_vars,
        value_vars=list(month_columns.keys()),
        var_name="month_original",
        value_name=value_name,
    )

    long_df["month"] = long_df["month_original"].map(
        month_columns
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

    # Удаляем мусорные строки.
    long_df = long_df[
        long_df["sku"].notna()
        & (long_df["sku"] != "")
        & (long_df["sku"].str.lower() != "nan")
    ]

    long_df[value_name] = pd.to_numeric(
        long_df[value_name],
        errors="coerce",
    )

    long_df[value_name] = long_df[value_name].fillna(0)

    return long_df[
        [
            "sku",
            "product_name",
            "month",
            value_name,
        ]
    ]


def load_supplier(supplier, directory):
    print("\n" + "=" * 80)
    print(f"ПОСТАВЩИК: {supplier}")
    print("=" * 80)

    sales_file = find_file(
        directory,
        "ежемесячные продажи",
    )

    stock_file = find_file(
        directory,
        "ежемесячные остатки",
    )

    sales = load_monthly_file(
        sales_file,
        "sales_raw",
    )

    stock = load_monthly_file(
        stock_file,
        "stock",
    )

    # Иногда SKU может повторяться.
    sales = (
        sales.groupby(
            ["sku", "product_name", "month"],
            as_index=False,
        )["sales_raw"]
        .sum()
    )

    stock = (
        stock.groupby(
            ["sku", "month"],
            as_index=False,
        )["stock"]
        .sum()
    )

    df = sales.merge(
        stock,
        on=["sku", "month"],
        how="left",
    )

    df["supplier"] = supplier

    # ---------------------------------------------------------
    # Возвраты / отрицательные продажи
    # ---------------------------------------------------------

    # Не уничтожаем исходное значение.
    df["return_qty"] = np.where(
        df["sales_raw"] < 0,
        abs(df["sales_raw"]),
        0,
    )

    # Для модели спроса отрицательный спрос невозможен.
    # Поэтому demand = max(net sales, 0).
    df["sales"] = df["sales_raw"].clip(lower=0)

    df["stock"] = pd.to_numeric(
        df["stock"],
        errors="coerce",
    )

    return df


def add_features(df):
    print("\nСоздаём ML features...")

    df = df.sort_values(
        ["supplier", "sku", "month"]
    ).reset_index(drop=True)

    group = df.groupby(
        ["supplier", "sku"],
        group_keys=False,
    )

    # ---------------------------------------------------------
    # Lag features
    # ---------------------------------------------------------

    for lag in [1, 2, 3, 6, 12]:
        df[f"sales_lag_{lag}"] = group["sales"].shift(lag)

    # ---------------------------------------------------------
    # Rolling features
    # shift(1), чтобы модель НЕ видела текущий target.
    # ---------------------------------------------------------

    df["rolling_mean_3"] = group["sales"].transform(
        lambda x: x.shift(1).rolling(3).mean()
    )

    df["rolling_mean_6"] = group["sales"].transform(
        lambda x: x.shift(1).rolling(6).mean()
    )

    df["rolling_mean_12"] = group["sales"].transform(
        lambda x: x.shift(1).rolling(12).mean()
    )

    df["rolling_std_3"] = group["sales"].transform(
        lambda x: x.shift(1).rolling(3).std()
    )

    df["rolling_std_6"] = group["sales"].transform(
        lambda x: x.shift(1).rolling(6).std()
    )

    # ---------------------------------------------------------
    # Growth
    # ---------------------------------------------------------

    denominator = df["sales_lag_3"].replace(0, np.nan)

    df["growth_3m"] = (
        df["sales_lag_1"] - df["sales_lag_3"]
    ) / denominator

    df["growth_3m"] = (
        df["growth_3m"]
        .replace([np.inf, -np.inf], np.nan)
        .clip(-5, 5)
    )

    # ---------------------------------------------------------
    # Calendar
    # ---------------------------------------------------------

    df["year"] = df["month"].dt.year
    df["month_num"] = df["month"].dt.month
    df["quarter"] = df["month"].dt.quarter

    # Циклическое представление сезона.
    df["month_sin"] = np.sin(
        2 * np.pi * df["month_num"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month_num"] / 12
    )

    # ---------------------------------------------------------
    # Stockout proxy
    # ---------------------------------------------------------

    df["stockout_flag"] = (
        df["stock"].fillna(0) <= 0
    ).astype(int)

    # ---------------------------------------------------------
    # Target
    #
    # Предсказываем следующий месяц.
    # ---------------------------------------------------------

    df["target_next_month"] = group["sales"].shift(-1)

    return df


def main():
    print("\nQOR / ProcureAI")
    print("Подготовка training dataset\n")

    frames = []

    for supplier, directory in SUPPLIERS.items():

        if not directory.exists():
            raise FileNotFoundError(
                f"Нет директории: {directory}"
            )

        supplier_df = load_supplier(
            supplier,
            directory,
        )

        frames.append(supplier_df)

    df = pd.concat(
        frames,
        ignore_index=True,
    )

    print("\nИсходных строк:", len(df))

    df = add_features(df)

    # Для обучения target должен существовать.
    training = df[
        df["target_next_month"].notna()
    ].copy()

    # Нужно хотя бы несколько месяцев истории.
    training = training[
        training["sales_lag_3"].notna()
    ].copy()

    training = training.sort_values(
        ["supplier", "sku", "month"]
    )

    output = OUTPUT_DIR / "training_dataset.csv"

    training.to_csv(
        output,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n" + "=" * 80)
    print("DATASET ГОТОВ")
    print("=" * 80)

    print(f"Строк: {len(training):,}")
    print(
        f"Уникальных SKU: "
        f"{training['sku'].nunique():,}"
    )

    print(
        f"Период: "
        f"{training['month'].min().date()} "
        f"→ "
        f"{training['month'].max().date()}"
    )

    print("\nПо поставщикам:")

    print(
        training.groupby("supplier")
        .agg(
            rows=("sku", "size"),
            skus=("sku", "nunique"),
            sales=("sales", "sum"),
        )
    )

    print("\nTarget statistics:")

    print(
        training["target_next_month"]
        .describe()
    )

    print("\nФайл:")
    print(output)

    print("\nСледующий этап:")
    print("CatBoost training")


if __name__ == "__main__":
    main()