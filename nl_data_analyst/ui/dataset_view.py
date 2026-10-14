"""
Dataset overview component displaying dimensions, health metrics, and data preview.
"""

import pandas as pd
import streamlit as st
from nl_data_analyst.models import DatasetProfile


def render_dataset_overview(df: pd.DataFrame, profile: DatasetProfile, filename: str):
    """
    Renders an expandable overview of the active dataset with row/column counts,
    missing-value diagnostics, column schema dictionary, and a 5-row preview.
    """
    total_nulls = sum(profile.null_counts.values())
    total_cells = profile.row_count * profile.column_count
    null_pct = (total_nulls / total_cells * 100) if total_cells > 0 else 0

    with st.expander(
        f"📋 Dataset Overview: {filename} • {profile.row_count:,} rows × {profile.column_count} columns",
        expanded=False,
    ):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Rows", f"{profile.row_count:,}")
        m2.metric("Total Columns", profile.column_count)
        m3.metric("Missing Values", f"{total_nulls:,}", delta=f"{null_pct:.1f}% missing" if total_nulls > 0 else "0.0% clean", delta_color="inverse")
        m4.metric("Memory Footprint", f"{profile.memory_usage_bytes / 1024:.1f} KB")

        st.markdown("#### 🔎 Column Schema & Inferred Types")
        schema_rows = []
        for col in profile.columns:
            null_count = profile.null_counts.get(col, 0)
            col_null_pct = (null_count / profile.row_count * 100) if profile.row_count > 0 else 0
            samples = profile.sample_values.get(col, [])
            sample_preview = ", ".join([f"'{s}'" for s in samples[:3]])
            schema_rows.append({
                "Column Name": col,
                "Inferred Type": profile.column_types.get(col, "unknown"),
                "Missing Values": f"{null_count} ({col_null_pct:.1f}%)",
                "Sample Values": sample_preview or "(empty)",
            })

        st.dataframe(
            pd.DataFrame(schema_rows),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### 📄 Data Preview (First 5 Rows)")
        st.dataframe(
            df.head(5),
            use_container_width=True,
            hide_index=False,
        )
