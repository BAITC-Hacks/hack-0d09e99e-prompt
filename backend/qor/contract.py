"""Feature contract of ml/models/demand_model.cbm.

The file was trained by scripts/train_model.py on data/processed/training_dataset.csv
(prepare_dataset.py, v1). prepare_dataset_v2.py builds a different column set and
must not be fed to this model.
"""

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

MODEL_NAME = "demand_model.cbm"
