"""
Ask bar component providing prominent question input, dynamic suggestions, and run trigger.
"""

from typing import Callable, Optional
import streamlit as st
from nl_data_analyst.models import DatasetProfile
from nl_data_analyst.planner import generate_suggested_questions


def render_ask_bar(
    profile: DatasetProfile,
    on_submit: Callable[[str], None],
):
    """
    Renders the prominent question input area with tailored example question chips.
    """
    st.markdown("### 💬 Ask Your Data")
    st.caption("Ask questions in plain English—from simple aggregations to group comparisons and correlations.")

    # Tailored question suggestions based on profile columns
    suggested = generate_suggested_questions(profile)

    if suggested:
        st.markdown("**Suggested questions for this dataset:**")
        cols = st.columns(min(len(suggested), 4))
        for idx, q_text in enumerate(suggested[:4]):
            col_target = cols[idx % len(cols)]
            if col_target.button(
                f"💡 {q_text}",
                key=f"suggestion_chip_{idx}",
                use_container_width=True,
            ):
                st.session_state.query_input = q_text
                st.session_state.chart_override = None
                on_submit(q_text)
                st.rerun()

    # Form with text input and run button
    with st.form("ask_form", clear_on_submit=False):
        user_query = st.text_input(
            "Enter your question:",
            value=st.session_state.get("query_input", ""),
            placeholder="e.g. Which product had the highest revenue? or Show monthly sales for each region.",
            key="user_text_input",
            label_visibility="collapsed",
        )
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            submitted = st.form_submit_button(
                "⚡ Analyze Data",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            if user_query.strip():
                st.session_state.chart_override = None
                on_submit(user_query.strip())
                st.rerun()
            else:
                st.warning("Please enter a question before analyzing.")
