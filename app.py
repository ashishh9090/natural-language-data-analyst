"""
Natural-Language Data Analyst - Streamlit Web Application.
A safe, transparent, and approachable data exploration workspace.
"""

import streamlit as st
from dotenv import load_dotenv

# Load local environment variables (.env) if present
load_dotenv()

from nl_data_analyst.executor import execute_analysis_plan
from nl_data_analyst.planner import validate_plan_against_schema
from nl_data_analyst.ui import (
    inject_custom_styles,
    render_ask_bar,
    render_dataset_overview,
    render_empty_state,
    render_header,
    render_results_view,
    render_sidebar,
)

# Page configuration
st.set_page_config(
    page_title="Natural-Language Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply accessible modern styles and tokens
inject_custom_styles()


def init_session_state():
    """Initializes persistent session state variables."""
    if "df" not in st.session_state:
        st.session_state.df = None
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "filename" not in st.session_state:
        st.session_state.filename = None
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "last_plan" not in st.session_state:
        st.session_state.last_plan = None
    if "last_question" not in st.session_state:
        st.session_state.last_question = ""
    if "chart_override" not in st.session_state:
        st.session_state.chart_override = None


init_session_state()

# Sidebar: Provider status, dataset switches, safety disclosures
provider = render_sidebar()

# Compact Top Header with active dataset status indicator
render_header(st.session_state.profile, st.session_state.filename)

# Empty State: Friendly welcome, privacy disclosures, sample datasets, and upload dropzone
if st.session_state.df is None or st.session_state.profile is None:
    render_empty_state()
    st.stop()
else:
    # Callback to process natural-language questions through planning, schema validation, and safe execution
    def handle_query_analysis(query_text: str):
        clean_query = query_text.strip()
        if not clean_query:
            return

        st.session_state.last_question = clean_query
        st.session_state.chart_override = None

        with st.spinner("Analyzing question, generating structured plan, and verifying safety allowlist..."):
            # Step 1: Generate plan from schema profile (no raw rows sent to LLM)
            raw_plan = provider.generate_plan(clean_query, st.session_state.profile)

            # Step 2: Validate plan strictly against schema allowlist
            is_valid, validation_err = validate_plan_against_schema(raw_plan, st.session_state.profile)

            if not is_valid:
                st.session_state.last_plan = raw_plan
                st.session_state.last_result = execute_analysis_plan(
                    st.session_state.df,
                    raw_plan.model_copy(
                        update={
                            "operation": "unsupported",
                            "unsupported_reason": validation_err,
                            "follow_up_suggestion": "Please check the available column names in the dataset overview and retry your question.",
                        }
                    ),
                    st.session_state.profile,
                )
            else:
                # Step 3: Deterministic safe execution via Pandas allowlist
                st.session_state.last_plan = raw_plan
                st.session_state.last_result = execute_analysis_plan(
                    st.session_state.df,
                    raw_plan,
                    st.session_state.profile,
                )

    # Dataset Overview: Dimensions, quality metrics, column schema, and 5-row preview
    render_dataset_overview(
        df=st.session_state.df,
        profile=st.session_state.profile,
        filename=st.session_state.filename or "Uploaded Dataset",
    )

    # Prominent "Ask Your Data" input with dynamic question suggestions
    render_ask_bar(
        profile=st.session_state.profile,
        on_submit=handle_query_analysis,
    )

    # Results Display: Answer card, chart switcher, plan explainers, data health disclaimers, and records table
    if st.session_state.last_result is not None:
        render_results_view(
            result=st.session_state.last_result,
            plan=st.session_state.last_plan,
            original_df=st.session_state.df,
            question=st.session_state.last_question,
        )
