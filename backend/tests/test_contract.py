"""The live pipeline must feed the v2 model exactly the columns it was trained on."""

from __future__ import annotations

from catboost import CatBoostRegressor

from qor.contract import CATEGORICAL, FEATURES, MODEL_NAME
from qor.pipeline import MODEL_PATH


def test_model_file_exists():
    assert MODEL_PATH.is_file(), f"нет файла модели {MODEL_PATH}"
    assert MODEL_PATH.name == MODEL_NAME


def test_model_features_match_contract():
    model = CatBoostRegressor()
    model.load_model(str(MODEL_PATH))
    assert set(model.feature_names_) == set(FEATURES)
    assert len(model.feature_names_) == len(FEATURES)


def test_categorical_columns_are_part_of_features():
    assert set(CATEGORICAL) <= set(FEATURES)


def test_v2_columns_not_v1():
    """Guard against feeding the v1 dataset into the v2 model again."""
    assert "demand_lag_3" in FEATURES
    assert "sales_lag_3" not in FEATURES
    assert "stockout_flag" not in FEATURES
