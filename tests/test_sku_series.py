"""Per-SKU monthly sales for the mobile mini chart."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from qor.pipeline import monthly_series  # noqa: E402


def _frame() -> pd.DataFrame:
    months = pd.date_range("2025-01-01", periods=14, freq="MS")
    rows = []
    for month in months:
        rows.append({"sku": "A", "month": month, "sales_positive": float(month.month * 10)})
        rows.append({"sku": "B", "month": month, "sales_positive": 1.0})
    return pd.DataFrame(rows)


def test_monthly_series_keeps_last_twelve_months_for_requested_skus():
    series = monthly_series(_frame(), {"A"})

    assert list(series) == ["A"]
    points = series["A"]
    assert len(points) == 12
    assert points[0] == {"label": "мар 25", "value": 30.0}
    assert points[-1] == {"label": "фев 26", "value": 20.0}


def test_monthly_series_skips_unknown_skus():
    assert monthly_series(_frame(), {"missing"}) == {}
