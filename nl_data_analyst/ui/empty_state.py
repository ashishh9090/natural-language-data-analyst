"""
Empty state component displayed when no dataset is currently loaded.
Provides clear drag-and-drop file upload, privacy disclosures, sample datasets, and starter questions.
"""

from pathlib import Path
import streamlit as st
from nl_data_analyst.data import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DataLoadError,
    load_csv_safely,
    profile_dataset,
)


def render_empty_state():
    """Renders the welcoming empty state with sample datasets and upload dropzone."""
    st.markdown(
        """
        <div class="empty-hero-card">
            <div class="hero-title">Welcome to your Data Exploration Workspace</div>
            <div class="hero-desc">
                Upload your CSV file to start asking analytical questions in natural language.
                Get deterministic calculations, verified charts, and full audit transparency—with zero code execution risks.
            </div>
            <div class="feature-grid">
                <div class="feature-item">
                    <h4>🔒 100% Safe Execution</h4>
                    <p>No arbitrary code, eval(), or SQL generated. All analyses execute via strict Pandas allowlists.</p>
                </div>
                <div class="feature-item">
                    <h4>🛡️ Privacy First</h4>
                    <p>Raw table rows are never sent to the LLM. Only column schema and bounded structure are shared.</p>
                </div>
                <div class="feature-item">
                    <h4>📈 Verified Insights</h4>
                    <p>Answers are computed directly from your data—never hallucinated or guessed by the model.</p>
                </div>
            </div>
            <div class="privacy-banner">
                <span>🛡️</span>
                <span><strong>Privacy Note:</strong> Your data is processed entirely in your local memory. File limit: 100 MB.</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🚀 Quick Start: Try a Sample Dataset")
    st.caption("Select a pre-loaded dataset below to test the analyst immediately:")

    col_sample1, col_sample2 = st.columns(2)

    sample_dir = Path(__file__).parent.parent.parent / "sample_data"
    ecom_path = sample_dir / "ecommerce_orders.csv"
    saas_path = sample_dir / "saas_metrics.csv"

    with col_sample1:
        st.markdown(
            """
            **🛍️ E-Commerce Orders & Sales**  
            *Columns: product_name, category, region, sales, discount, profit, quantity*  
            *Example questions:*
            - "Which product had the highest revenue?"
            - "Show monthly sales for each region"
            - "Are higher discounts associated with lower profit?"
            """
        )
        if st.button("Load E-Commerce Dataset", key="load_ecom_btn", type="primary", use_container_width=True):
            if ecom_path.exists():
                df, size = load_csv_safely(str(ecom_path))
                st.session_state.df = df
                st.session_state.profile = profile_dataset(df, file_size_bytes=size)
                st.session_state.filename = "ecommerce_orders.csv (Sample)"
                st.session_state.last_result = None
                st.session_state.last_plan = None
                st.session_state.last_question = ""
                st.session_state.chart_override = None
                st.rerun()

    with col_sample2:
        st.markdown(
            """
            **💻 SaaS Customer Metrics & Retention**  
            *Columns: plan_tier, monthly_fee, usage_hours, support_tickets, churned, satisfaction_score*  
            *Example questions:*
            - "What is the average satisfaction score by plan tier?"
            - "Is usage hours correlated with customer satisfaction?"
            - "How many customers churned per plan?"
            """
        )
        if st.button("Load SaaS Metrics Dataset", key="load_saas_btn", use_container_width=True):
            if saas_path.exists():
                df, size = load_csv_safely(str(saas_path))
                st.session_state.df = df
                st.session_state.profile = profile_dataset(df, file_size_bytes=size)
                st.session_state.filename = "saas_metrics.csv (Sample)"
                st.session_state.last_result = None
                st.session_state.last_plan = None
                st.session_state.last_question = ""
                st.session_state.chart_override = None
                st.rerun()

    st.markdown("---")
    st.subheader("📂 Or Upload Your Own CSV File")
    uploaded = st.file_uploader(
        "Choose a CSV file from your computer",
        type=["csv"],
        key="main_file_uploader",
        help=f"Maximum file size: {DEFAULT_MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB.",
    )

    if uploaded is not None and st.session_state.filename != uploaded.name:
        try:
            raw_bytes = uploaded.getvalue()
            df, size = load_csv_safely(raw_bytes)
            st.session_state.df = df
            st.session_state.profile = profile_dataset(df, file_size_bytes=size)
            st.session_state.filename = uploaded.name
            st.session_state.last_result = None
            st.session_state.last_plan = None
            st.session_state.last_question = ""
            st.session_state.chart_override = None
            st.rerun()
        except DataLoadError as e:
            st.error(f"Upload error: {e}")
        except Exception as e:
            st.error(f"Unexpected error reading file: {e}")
