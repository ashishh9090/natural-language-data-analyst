"""
Header component for Natural-Language Data Analyst workspace.
Displays the title, value statement, and dataset status badge.
"""

from typing import Optional
import streamlit as st
from nl_data_analyst.models import DatasetProfile


def render_header(profile: Optional[DatasetProfile], filename: Optional[str]):
    """Renders the top application header with active dataset status indicator."""
    if profile is not None and filename:
        status_html = f"""
        <div class="status-badge active" title="Dataset successfully loaded into local memory">
            <span class="status-dot"></span>
            <span>Dataset Active: <strong>{filename}</strong> ({profile.row_count:,} rows, {profile.column_count} cols)</span>
        </div>
        """
    else:
        status_html = """
        <div class="status-badge inactive" title="Upload a CSV or load a sample dataset to begin">
            <span class="status-dot"></span>
            <span>No dataset loaded</span>
        </div>
        """

    st.markdown(
        f"""
        <header class="workspace-header">
            <div class="header-title-group">
                <h1>📊 Natural-Language Data Analyst</h1>
                <p>Ask questions about your data in plain English. Get verified answers, transparent methods, and interactive charts.</p>
            </div>
            <div>
                {status_html}
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )
