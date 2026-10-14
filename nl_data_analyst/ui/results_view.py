"""
Results view component displaying answers, interactive charts with type switchers,
transparent plan explanations, data health caveats, and result tables.
"""

from typing import Optional
import pandas as pd
import streamlit as st

from nl_data_analyst.charts import create_result_chart, get_suitable_chart_types
from nl_data_analyst.models import AnalysisPlan, ExecutionResult
from nl_data_analyst.planner import explain_plan_in_plain_english


def render_results_view(
    result: ExecutionResult,
    plan: Optional[AnalysisPlan],
    original_df: pd.DataFrame,
    question: str,
):
    """
    Renders analysis results in a structured, accessible, and user-friendly flow.
    """
    st.markdown("---")
    st.markdown(f"### 🎯 Results for: *\"{question}\"*")

    # 1. Compact Expandable Interpreted Plan
    if plan is not None:
        with st.expander("🔍 Interpreted Analysis Plan (Verified & Safe)", expanded=False):
            plain_plan = explain_plan_in_plain_english(plan)
            st.markdown(plain_plan)
            st.caption(
                f"**Operation Type:** `{plan.operation}` • "
                f"**Allowlist Execution:** Verified Safe ✅ • "
                f"**Columns:** `{', '.join(plan.columns or ['(all)']) if plan.columns else '(none)'}`"
            )

    # 2. Unsupported, Ambiguous, or Failed Query Handling
    if result.is_unsupported or not result.success:
        st.markdown(
            f"""
            <div class="unsupported-card">
                <h4>⚠️ Cannot Complete Requested Analysis</h4>
                <p>{result.error_message or result.direct_answer}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        follow_up = plan.follow_up_suggestion if plan else None
        if follow_up:
            st.info(f"💡 **Suggested Next Step:** {follow_up}")
        else:
            st.info("💡 **Suggested Next Step:** Try rephrasing your question using column names from the dataset overview.")
        return

    # 3. Direct Computed Answer Card
    st.markdown(
        f"""
        <div class="answer-card">
            <div class="answer-tag">
                <span>⚡ Direct Answer (Computed from Data)</span>
            </div>
            <div class="answer-text">{result.direct_answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Interactive Chart with Type Switcher
    if result.chart_spec and result.chart_spec.needed:
        suitable_types = get_suitable_chart_types(result)
        current_chart_type = st.session_state.get("chart_override") or result.chart_spec.chart_type

        # Chart controls bar if multiple chart types are suitable
        if len(suitable_types) > 1:
            col_chart_header, col_chart_ctrl = st.columns([3, 2])
            with col_chart_header:
                st.markdown("#### 📊 Interactive Visualization")
            with col_chart_ctrl:
                default_idx = suitable_types.index(current_chart_type) if current_chart_type in suitable_types else 0
                chosen_type = st.selectbox(
                    "Switch Chart Type",
                    options=suitable_types,
                    index=default_idx,
                    key="chart_type_selector",
                    label_visibility="collapsed",
                    help="Switch between suitable visual encodings for this data",
                )
                if chosen_type != current_chart_type:
                    st.session_state.chart_override = chosen_type
                    current_chart_type = chosen_type
        else:
            st.markdown("#### 📊 Interactive Visualization")

        fig = create_result_chart(
            result,
            original_df=original_df,
            override_chart_type=current_chart_type,
        )
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    # 5. Method Explanation & Data Integrity Collapsible Section
    with st.expander("📖 How this was calculated & Data Health Notes", expanded=True):
        col_calc, col_health = st.columns([3, 2])

        with col_calc:
            st.markdown("##### ⚙️ Method & Referenced Columns")
            st.markdown(result.method_explanation)

            if plan and plan.columns:
                pills = " ".join([f'<span class="badge-pill">{c}</span>' for c in plan.columns])
                st.markdown(f"**Referenced Columns:** {pills}", unsafe_allow_html=True)

        with col_health:
            st.markdown("##### 🛡️ Data Health & Disclaimers")
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

    # 6. Result Data Records Table with CSV Download
    if result.data_records and len(result.data_records) > 0:
        with st.expander(f"📋 View Result Records ({len(result.data_records)} items)", expanded=False):
            res_df = pd.DataFrame(result.data_records)
            st.dataframe(res_df, use_container_width=True, hide_index=True)

            csv_bytes = res_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Result as CSV",
                data=csv_bytes,
                file_name="analysis_result.csv",
                mime="text/csv",
                key="download_result_csv_btn",
            )
