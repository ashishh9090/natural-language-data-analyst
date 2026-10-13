import io
import pytest
import pandas as pd
from nl_data_analyst.data import load_csv_safely, profile_dataset, DataLoadError


def test_load_csv_safely_valid():
    csv_content = b"name,age,salary\nAlice,30,85000\nBob,25,60000\nCharlie,35,95000"
    df, size = load_csv_safely(csv_content)
    assert len(df) == 3
    assert list(df.columns) == ["name", "age", "salary"]
    assert size == len(csv_content)


def test_load_csv_safely_empty_fails():
    with pytest.raises(DataLoadError, match="empty"):
        load_csv_safely(b"")


def test_load_csv_safely_size_limit():
    content = b"a,b\n1,2"
    with pytest.raises(DataLoadError, match="exceeds maximum"):
        load_csv_safely(content, max_size_bytes=4)


def test_profile_dataset():
    df = pd.DataFrame({
        "product": ["Widget A", "Widget B", "Widget A", None],
        "sales": [100.0, 250.5, 300.0, 50.0],
        "quantity": [1, 2, 3, 4],
    })
    profile = profile_dataset(df, file_size_bytes=500)
    assert profile.row_count == 4
    assert profile.column_count == 3
    assert profile.null_counts["product"] == 1
    assert "sales" in profile.numeric_columns
    assert "product" in profile.categorical_columns
    # Ensure sample values are bounded (<= 3)
    assert len(profile.sample_values["product"]) <= 3
