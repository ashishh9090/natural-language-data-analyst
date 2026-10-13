"""
Natural-Language Data Analyst - Streamlit Web Application.
A safe, transparent, and approachable data analysis assistant.
"""

import os
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

from nl_data_analyst.data import (
    DEFAULT_MAX_FILE_SIZE_BYTES,
    DataLoadError,
    load_csv_safely,
    profile_dataset,
)
from nl_data_analyst.executor import execute_analysis_plan
from nl_data_analyst.charts import create_result_chart
from nl_data_analyst.llm import get_llm_provider
from nl_data_analyst.planner import (
    explain_plan_in_plain_english,
    generate_suggested_questions,
    validate_plan_against_schema,
)

# Page configuration
st.set_page_config(
    page_title="Natural-Language Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling for high visual polish
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .answer-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border: 1px solid #a7f3d0;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
    }
    .answer-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #065f46;
        margin-bottom: 0.35rem;
    }
    .answer-text {
        font-size: 1.25rem;
        font-weight: 600;
        color: #064e3b;
        line-height: 1.4;
    }
    .unsupported-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 10px;
        padding: 1.25rem;
        color: #92400e;
        margin-bottom: 1rem;
    }
    .badge-pill {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #e2e8f0;
        color: #334155;
        margin-right: 0.4rem;
    }
    .stButton>button {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session_state():
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


init_session_state()

# Sidebar: Configuration, File Ingestion & Architecture Info
with st.sidebar:
    st.title("⚙️ Data Analyst Settings")

    provider, provider_name = get_llm_provider()
    st.info(f"**Planning Provider:** {provider_name}")

    if "No API key" in provider_name:
        st.caption(
            "💡 Running with the built-in Heuristic Engine. "
            "To use Gemini, OpenAI, or Claude, set `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`."
        )

    st.divider()

    st.subheader("📁 Dataset Source")
    sample_btn = st.button("📊 Load Sample E-Commerce Data", use_container_width=True)

    sample_path = Path(__file__).parent / "sample_data" / "ecommerce_orders.csv"
    if sample_btn and sample_path.exists():
        try:
            df, size = load_csv_safely(str(sample_path))
            st.session_state.df = df
            st.session_state.profile = profile_dataset(df, file_size_bytes=size)
            st.session_state.filename = "ecommerce_orders.csv (Sample)"
            st.session_state.last_result = None
            st.session_state.last_plan = None
            st.session_state.last_question = ""
            st.rerun()
        except Exception as e:
            st.error(f"Error loading sample dataset: {e}")

    uploaded_file = st.file_uploader(
        "Or upload a CSV file",
        type=["csv"],
        help=f"File limit: {DEFAULT_MAX_FILE_SIZE_BYTES / (1024*1024):.0f} MB. Data is processed locally in memory.",
    )

    if uploaded_file is not None and (
        st.session_state.filename != uploaded_file.name
    ):
        try:
            raw_bytes = uploaded_file.getvalue()
            df, size = load_csv_safely(raw_bytes)
            st.session_state.df = df
            st.session_state.profile = profile_dataset(df, file_size_bytes=size)
            st.session_state.filename = uploaded_file.name
            st.session_state.last_result = None
            st.session_state.last_plan = None
            st.session_state.last_question = ""
            st.rerun()
        except DataLoadError as e:
            st.error(f"Upload error: {e}")
        except Exception as e:
            st.error(f"Unexpected error loading file: {e}")

    st.divider()
    st.markdown("### 🛡️ Safety & Architecture")
    st.markdown(
        """
        - **Zero Arbitrary Execution:** No `eval()`, `exec()`, or generated code.
        - **Allowlist Execution:** Operations run only through verified Pandas routines.
        - **Data Privacy:** Raw table rows are not sent to the LLM. Only schema metadata and bounded format hints are shared.
        - **Correlation != Causation:** Statistical caveats are automatically applied.
        """
    )


# Header
st.markdown('<div class="main-title">Natural-Language Data Analyst</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ask questions about your data in plain English. Get verified answers, transparent methods, and interactive charts.</div>',
    unsafe_allow_html=True,
)

if st.session_state.df is None:
    st.info(
        "👋 Welcome! Get started by uploading a CSV file in the sidebar or clicking **'Load Sample E-Commerce Data'**."
    )
    st.stop()

# Dataset Overview Section
profile = st.session_state.profile
df = st.session_state.df

with st.expander(f"📋 Dataset Overview: {st.session_state.filename} ({profile.row_count:,} rows, {profile.column_count} columns)", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{profile.row_count:,}")
    col2.metric("Total Columns", profile.column_count)
    total_nulls = sum(profile.null_counts.values())
    col3.metric("Missing Values", f"{total_nulls:,}")
    col4.metric("Memory Footprint", f"{profile.memory_usage_bytes / 1024:.1f} KB")

    st.markdown("#### Column Structure & Schema")
    schema_rows = []
    for col in profile.columns:
        schema_rows.append({
            "Column": col,
            "Inferred Type": profile.column_types.get(col, ""),
            "Missing Values": profile.null_counts.get(col, 0),
            "Sample Values": ", ".join([f"'{s}'" for s in profile.sample_values.get(col, [])]),
        })
    st.dataframe(pd.DataFrame(schema_rows), use_container_width=True, hide_index=True)

    st.markdown("#### Data Preview (First 5 Rows)")
    st.dataframe(df.head(5), use_container_width=True)

# Question Suggestions Section
suggested_questions = generate_suggested_questions(profile)

st.markdown("##### 💡 Suggested Questions for this Dataset:")
chips = st.columns(len(suggested_questions))
for idx, q_text in enumerate(suggested_questions):
    if chips[idx].button(q_text, key=f"chip_{idx}", use_container_width=True):
        st.session_state.query_input = q_text
        st.rerun()

# User Query Input
with st.form("query_form", clear_on_submit=False):
    user_query = st.text_input(
        "Enter your question in plain English:",
        value=st.session_state.query_input,
        placeholder="e.g. Which product had the highest revenue? or Are higher discounts associated with lower profit?",
    )
    submit_btn = st.form_submit_button("🔍 Analyze Data", type="primary")

if submit_btn and user_query.strip():
    st.session_state.last_question = user_query.strip()
    with st.spinner("Analyzing data and verifying plan..."):
        # Step 1: Generate plan from schema profile
        raw_plan = provider.generate_plan(user_query.strip(), profile)

        # Step 2: Validate plan against strict schema allowlist
        is_valid, validation_err = validate_plan_against_schema(raw_plan, profile)

        if not is_valid:
            st.session_state.last_plan = raw_plan
            st.session_state.last_result = execute_analysis_plan(
                df,
                raw_plan.model_copy(
                    update={
                        "operation": "unsupported",
                        "unsupported_reason": validation_err,
                        "follow_up_suggestion": "Please verify column names and ask about existing columns.",
                    }
                ),
                profile,
            )
        else:
            # Step 3: Deterministic safe execution
            st.session_state.last_plan = raw_plan
            st.session_state.last_result = execute_analysis_plan(df, raw_plan, profile)


# Display Analysis Results
if st.session_state.last_result is not None:
    result = st.session_state.last_result
    plan = st.session_state.last_plan

    st.markdown("---")
    st.markdown(f"### Analysis for: *\"{st.session_state.last_question}\"*")

    # 1. Plain-English Transparent Analysis Plan
    with st.expander("🔍 Interpreted Analysis Plan (Verified & Safe)", expanded=True):
        plain_plan = explain_plan_in_plain_english(plan)
        st.markdown(plain_plan)
        st.caption(f"**Operation Type:** `{plan.operation}` | **Strict Allowlist:** Verified ✅")

    # 2. Unsupported or Ambiguous Query Handling
    if result.is_unsupported or not result.success:
        st.markdown(
            f"""
            <div class="unsupported-card">
                <h4>⚠️ Cannot Complete Analysis</h4>
                <p>{result.error_message or result.direct_answer}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if plan.follow_up_suggestion:
            st.info(f"💡 **Suggested Next Step:** {plan.follow_up_suggestion}")

    else:
        # 3. Direct Computed Answer Card
        st.markdown(
            f"""
            <div class="answer-card">
                <div class="answer-title">Direct Answer (Computed from Data)</div>
                <div class="answer-text">{result.direct_answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4. Interactive Visualization
        chart = create_result_chart(result, original_df=df)
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)

        # 5. Method Explanation & Data Integrity Notes
        col_exp, col_notes = st.columns([3, 2])
        with col_exp:
            st.markdown("#### 📖 Method & Columns Used")
            st.markdown(result.method_explanation)
            if plan.columns:
                pills = " ".join([f'<span class="badge-pill">{c}</span>' for c in plan.columns])
                st.markdown(f"**Referenced Columns:** {pills}", unsafe_allow_html=True)

        with col_notes:
            st.markdown("#### ℹ️ Data Health & Disclaimers")
            if result.notes:
                for note in result.notes:
                    if "causation" in note.lower():
                        st.warning(f"⚖️ {note}")
                    elif "missing" in note.lower() or "omitted" in note.lower():
                        st.info(f"⚠️ {note}")
                    else:
                        st.write(f"- {note}")
            else:
                st.success("✅ Complete data used (0 missing values omitted).")

        # 6. Result Data Table
        if result.data_records and len(result.data_records) > 0:
            with st.expander("📊 View Result Records Table", expanded=False):
                res_df = pd.DataFrame(result.data_records)
                st.dataframe(res_df, use_container_width=True)
                csv_bytes = res_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download Result as CSV",
                    data=csv_bytes,
                    file_name="analysis_result.csv",
                    mime="text/csv",
                )
