from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

DATA_DIRS = {
    "IEK": ROOT / "data" / "IEK",
    "Systeme": ROOT / "data" / "Systeme",
}


def inspect_excel(supplier: str, path: Path):
    print("\n" + "=" * 100)
    print(f"Поставщик: {supplier}")
    print(f"Файл: {path.name}")
    print("=" * 100)

    try:
        excel = pd.ExcelFile(path)

        print("Листы:", excel.sheet_names)

        for sheet in excel.sheet_names:
            print(f"\n--- Лист: {sheet} ---")

            # Пока читаем только первые 5 строк
            df = pd.read_excel(path, sheet_name=sheet, nrows=5)

            print(f"Колонки ({len(df.columns)}):")
            for column in df.columns:
                print(f"  - {column}")

            print("\nПервые строки:")
            print(df.head().to_string(index=False))

    except Exception as e:
        print(f"ОШИБКА: {e}")


def main():
    print("\nQOR / ProcureAI — проверка исходных данных\n")

    total_files = 0

    for supplier, directory in DATA_DIRS.items():

        print(f"\nПроверяем папку: {directory}")

        if not directory.exists():
            print("ПАПКА НЕ НАЙДЕНА")
            continue

        files = list(directory.glob("*.xlsx"))

        print(f"Найдено Excel: {len(files)}")

        total_files += len(files)

        for file in files:
            inspect_excel(supplier, file)

    print("\n" + "=" * 100)
    print(f"Всего найдено Excel-файлов: {total_files}")
    print("=" * 100)


if __name__ == "__main__":
    main()