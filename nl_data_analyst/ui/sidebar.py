"""
Sidebar component for configuration, file upload, dataset switching, and safety audit details.
"""

from pathlib import Path
import streamlit as st

from nl_data_analyst.data import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DataLoadError,
    load_csv_safely,
    profile_dataset,
)
from nl_data_analyst.llm import get_llm_provider


def render_sidebar():
    """Renders the sidebar with provider status, dataset selection, and architecture disclosures."""
    with st.sidebar:
        st.markdown("### ⚙️ Analyst Workspace")

        provider, provider_name = get_llm_provider()
        st.caption(f"**Planner Engine:** {provider_name}")

        if "No API key" in provider_name:
            st.info(
                "💡 **Built-in Offline Engine Active:** The app uses local heuristics and pattern-matching. "
                "To connect Gemini, OpenAI, or Claude, set `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`."
            )

        st.divider()

        # Dataset Management
        st.markdown("### 📁 Dataset Management")

        sample_dir = Path(__file__).parent.parent.parent / "sample_data"
        ecom_path = sample_dir / "ecommerce_orders.csv"
        saas_path = sample_dir / "saas_metrics.csv"

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("🛍️ E-Commerce", use_container_width=True, help="Load e-commerce orders sample dataset"):
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

        with col_s2:
            if st.button("💻 SaaS Metrics", use_container_width=True, help="Load SaaS subscription sample dataset"):
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

        # Upload new CSV
        sidebar_uploader = st.file_uploader(
            "Upload new CSV file",
            type=["csv"],
            key="sidebar_file_uploader",
            help=f"Limit: {DEFAULT_MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB. Read locally in memory.",
        )
        if sidebar_uploader is not None and st.session_state.filename != sidebar_uploader.name:
            try:
                raw_bytes = sidebar_uploader.getvalue()
                df, size = load_csv_safely(raw_bytes)
                st.session_state.df = df
                st.session_state.profile = profile_dataset(df, file_size_bytes=size)
                st.session_state.filename = sidebar_uploader.name
                st.session_state.last_result = None
                st.session_state.last_plan = None
                st.session_state.last_question = ""
                st.session_state.chart_override = None
                st.rerun()
            except DataLoadError as e:
                st.error(f"Error: {e}")
            except Exception as e:
                st.error(f"Upload error: {e}")

        # Clear dataset button if loaded
        if st.session_state.df is not None:
            if st.button("🗑️ Unload Current Dataset", use_container_width=True):
                st.session_state.df = None
                st.session_state.profile = None
                st.session_state.filename = None
                st.session_state.last_result = None
                st.session_state.last_plan = None
                st.session_state.last_question = ""
                st.session_state.chart_override = None
                st.rerun()

        st.divider()

        # Safety & Architectural Guarantees
        st.markdown("### 🛡️ Safety & Guarantees")
        st.markdown(
            """
            - **No Arbitrary Code:** 0% `eval()`, `exec()`, or generated scripts.
            - **Allowlist Only:** Aggregations and filters run exclusively through verified Pandas operations.
            - **Zero Row Leakage:** Raw table data is never sent to remote LLMs. Only schema and compact column types are shared.
            - **Honest Statistics:** Non-causal disclaimers and missing-data caveats are automatically attached.
            """
        )

        return provider
