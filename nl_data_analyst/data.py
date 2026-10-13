"""
Safe data ingestion, validation, and profiling for untrusted CSV inputs.
"""

import io
from typing import BinaryIO, Optional, Tuple, Union
import pandas as pd

from nl_data_analyst.models import DatasetProfile

# Configurable safety bounds
DEFAULT_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_SAMPLE_DISTINCT_VALUES = 3
MAX_SAMPLE_STRING_LENGTH = 40


class DataLoadError(Exception):
    """Raised when CSV loading or validation fails."""
    pass


def load_csv_safely(
    file_source: Union[bytes, BinaryIO, str],
    max_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
) -> Tuple[pd.DataFrame, int]:
    """
    Safely loads and validates an untrusted CSV input.

    Enforces:
    - File size validation before memory parsing
    - Clean column normalization (strips whitespace, de-duplicates)
    - Fallback encoding attempts (utf-8, utf-8-sig, latin-1)
    - Prevention of malformed or completely empty dataframes

    Returns:
        (DataFrame, file_size_in_bytes)
    """
    # 1. Size check
    raw_bytes: bytes
    if isinstance(file_source, bytes):
        raw_bytes = file_source
    elif isinstance(file_source, str):
        # file path
        try:
            with open(file_source, "rb") as f:
                raw_bytes = f.read(max_size_bytes + 1)
        except Exception as e:
            raise DataLoadError(f"Could not open file at '{file_source}': {e}")
    elif hasattr(file_source, "read"):
        raw_bytes = file_source.read(max_size_bytes + 1)
        if hasattr(file_source, "seek"):
            file_source.seek(0)
    else:
        raise DataLoadError("Unsupported file source type.")

    file_size = len(raw_bytes)
    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        raise DataLoadError(
            f"File exceeds maximum allowed size of {max_mb:.1f} MB. "
            f"Uploaded file is {file_size / (1024 * 1024):.1f} MB."
        )

    if file_size == 0:
        raise DataLoadError("The uploaded CSV file is completely empty.")

    # 2. Encoding fallback & safe parsing
    encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    df: Optional[pd.DataFrame] = None
    last_err: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            buffer = io.BytesIO(raw_bytes)
            # Use Python's c-engine with low_memory=False to catch parser issues upfront
            parsed_df = pd.read_csv(buffer, encoding=enc, engine="c")
            df = parsed_df
            break
        except Exception as e:
            last_err = e
            continue

    if df is None:
        raise DataLoadError(
            f"Failed to parse CSV file. Please verify that the file is a valid CSV. "
            f"Parser error: {last_err}"
        )

    if df.empty and len(df.columns) == 0:
        raise DataLoadError("The CSV contains no headers or tabular data.")

    # 3. Clean and sanitize column names
    clean_columns = []
    seen = {}
    for col in df.columns:
        col_str = str(col).strip()
        if not col_str:
            col_str = "unnamed_column"
        if col_str in seen:
            seen[col_str] += 1
            col_str = f"{col_str}_{seen[col_str]}"
        else:
            seen[col_str] = 0
        clean_columns.append(col_str)

    df.columns = clean_columns

    # 4. Attempt automatic datetime inference for ISO-like string columns without breaking
    for col in df.select_dtypes(include=["object", "string"]).columns:
        # Check if non-null values look like dates (YYYY-MM-DD)
        sample = df[col].dropna().head(10)
        if not sample.empty:
            # If all samples match date pattern length, try to convert
            all_date_like = sample.astype(str).str.match(r"^\d{4}-\d{2}-\d{2}").all()
            if all_date_like:
                try:
                    df[col] = pd.to_datetime(df[col], errors="ignore")
                except Exception:
                    pass

    return df, file_size


def profile_dataset(df: pd.DataFrame, file_size_bytes: int = 0) -> DatasetProfile:
    """
    Computes a safe, compact structural profile of the dataset.

    PRIVACY & TOKEN BOUNDARY DISCLOSURE:
    - This profile does NOT send raw table rows to any external model.
    - Only column names, inferred data types, null counts, and a bounded set
      of 2-3 sample distinct string representations (truncated to 40 chars)
      are extracted so the LLM knows what kind of values live in each column.
    """
    row_count = len(df)
    column_count = len(df.columns)
    columns = list(df.columns)

    column_types: dict[str, str] = {}
    null_counts: dict[str, int] = {}
    numeric_columns: list[str] = []
    categorical_columns: list[str] = []
    datetime_columns: list[str] = []
    sample_values: dict[str, list[str]] = {}

    memory_usage = int(df.memory_usage(deep=True).sum())

    for col in columns:
        series = df[col]
        dtype = str(series.dtype)
        column_types[col] = dtype
        null_counts[col] = int(series.isna().sum())

        # Classify column semantics
        if pd.api.types.is_numeric_dtype(series):
            numeric_columns.append(col)
        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime_columns.append(col)
        else:
            categorical_columns.append(col)

        # Extract strictly bounded sample values for LLM schema context
        valid_items = series.dropna().unique()[:MAX_SAMPLE_DISTINCT_VALUES]
        bounded_samples = []
        for val in valid_items:
            val_str = str(val)[:MAX_SAMPLE_STRING_LENGTH].replace("\n", " ").strip()
            bounded_samples.append(val_str)
        sample_values[col] = bounded_samples

    return DatasetProfile(
        row_count=row_count,
        column_count=column_count,
        columns=columns,
        column_types=column_types,
        null_counts=null_counts,
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        datetime_columns=datetime_columns,
        sample_values=sample_values,
        file_size_bytes=file_size_bytes,
        memory_usage_bytes=memory_usage,
    )
