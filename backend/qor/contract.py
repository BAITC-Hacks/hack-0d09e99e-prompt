"""Feature contract of ml/models/demand_model_v2.cbm.

Trained by scripts/train_model_v2.py on data/processed/training_dataset_v2.csv.
Live orders must be built with scripts/prepare_dataset_v2.py — the v1 columns
do not match this file.
"""

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

CATEGORICAL = ["supplier", "sku"]

MODEL_NAME = "demand_model_v2.cbm"
