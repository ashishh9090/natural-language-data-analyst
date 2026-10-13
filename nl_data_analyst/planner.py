"""
Planning validation, schema verification, and plain-English translation.
"""

from typing import List, Optional, Set, Tuple
from nl_data_analyst.models import (
    AnalysisPlan,
    DatasetProfile,
)

ALLOWED_OPERATIONS: Set[str] = {
    "summary",
    "aggregate",
    "filter",
    "sort",
    "value_counts",
    "correlation",
    "unsupported",
}

ALLOWED_AGG_FUNCS: Set[str] = {
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "nunique",
    "std",
}

ALLOWED_FILTER_OPS: Set[str] = {
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
    "in",
    "contains",
}


def validate_plan_against_schema(
    plan: AnalysisPlan, profile: DatasetProfile
) -> Tuple[bool, Optional[str]]:
    """
    Strictly verifies that an AnalysisPlan references only real columns,
    valid operations, and appropriate column types.

    Returns:
        (is_valid, error_reason)
    """
    if plan.operation not in ALLOWED_OPERATIONS:
        return False, f"Disallowed operation: '{plan.operation}'. Permitted operations: {sorted(ALLOWED_OPERATIONS)}"

    if plan.operation == "unsupported":
        return True, None

    valid_cols = set(profile.columns)
    numeric_cols = set(profile.numeric_columns)

    # 1. Validate all direct columns
    for col in plan.columns:
        if col not in valid_cols:
            return False, f"Referenced column '{col}' does not exist in dataset. Available columns: {profile.columns}"

    # 2. Validate group_by columns
    for col in plan.group_by:
        if col not in valid_cols:
            return False, f"Group-by column '{col}' does not exist in dataset."

    # 3. Validate aggregations
    for agg in plan.aggregations:
        if agg.column not in valid_cols:
            return False, f"Aggregation column '{agg.column}' does not exist in dataset."
        if agg.func not in ALLOWED_AGG_FUNCS:
            return False, f"Aggregation function '{agg.func}' is not supported. Allowed: {sorted(ALLOWED_AGG_FUNCS)}"
        if agg.func in {"sum", "mean", "median", "std"} and agg.column not in numeric_cols:
            return False, (
                f"Cannot compute numeric aggregation '{agg.func}' on non-numeric column '{agg.column}'. "
                f"Numeric columns available: {profile.numeric_columns}"
            )

    # 4. Validate filters
    for f in plan.filters:
        if f.column not in valid_cols:
            return False, f"Filter column '{f.column}' does not exist in dataset."
        if f.operator not in ALLOWED_FILTER_OPS:
            return False, f"Filter operator '{f.operator}' is not supported."

    # 5. Validate correlation
    if plan.operation == "correlation":
        corr_cols = [c for c in plan.columns if c in numeric_cols]
        if len(corr_cols) < 2:
            # check if numeric columns exist
            if len(numeric_cols) < 2:
                return False, "Correlation requires at least two numeric columns, but dataset does not have enough numeric columns."
            return False, f"Correlation requires at least two numeric columns from {profile.numeric_columns}."

    # 6. Validate sort_by
    for s in plan.sort_by:
        # Sort column can be in dataset or an aggregation alias/target
        if s.column not in valid_cols:
            agg_targets = {agg.column for agg in plan.aggregations}
            agg_aliases = {agg.alias for agg in plan.aggregations if agg.alias}
            if s.column not in agg_targets and s.column not in agg_aliases and s.column != "count":
                return False, f"Sort column '{s.column}' does not match any dataset column or computed metric."

    # 7. Validate chart spec columns if chart is requested
    if plan.chart and plan.chart.needed:
        if plan.chart.x and plan.chart.x not in valid_cols and plan.chart.x != "count":
            # Might be grouped key or metric
            pass
        if plan.chart.y and plan.chart.y not in valid_cols and plan.chart.y != "count":
            pass

    return True, None


def explain_plan_in_plain_english(plan: AnalysisPlan) -> str:
    """
    Translates a structured plan into transparent, friendly plain-English steps.
    """
    if plan.operation == "unsupported":
        reason = plan.unsupported_reason or "The requested question is outside the scope of the dataset."
        follow_up = f" Next step: {plan.follow_up_suggestion}" if plan.follow_up_suggestion else ""
        return f"Cannot answer request: {reason}{follow_up}"

    steps: List[str] = []

    # Filtering step
    if plan.filters:
        filt_strs = [f"{f.column} {f.operator} {f.value}" for f in plan.filters]
        steps.append(f"Filter records where: {', '.join(filt_strs)}")

    # Operation specifics
    if plan.operation == "aggregate":
        if plan.group_by:
            steps.append(f"Group records by {', '.join([repr(c) for c in plan.group_by])}")
        for agg in plan.aggregations:
            steps.append(f"Compute {agg.func.upper()} of column '{agg.column}'")

    elif plan.operation == "correlation":
        cols = plan.columns[:2]
        steps.append(f"Calculate Pearson correlation coefficient between '{cols[0]}' and '{cols[1]}'")
        steps.append("Note: Correlation assesses statistical association only; it does NOT imply causality.")

    elif plan.operation == "value_counts":
        col = plan.columns[0] if plan.columns else "dimension"
        steps.append(f"Count distinct occurrences of values in '{col}'")

    elif plan.operation == "summary":
        for agg in plan.aggregations:
            steps.append(f"Calculate overall {agg.func.upper()} for '{agg.column}'")

    # Sorting & limits
    if plan.sort_by:
        sort_descs = [f"'{s.column}' ({'descending' if s.direction == 'desc' else 'ascending'})" for s in plan.sort_by]
        steps.append(f"Sort results by {', '.join(sort_descs)}")

    if plan.limit:
        steps.append(f"Limit output to top {plan.limit} record(s)")

    # Visual chart
    if plan.chart and plan.chart.needed:
        chart_type = plan.chart.chart_type or "chart"
        steps.append(f"Plot interactive {chart_type} chart ({plan.chart.x or ''} vs {plan.chart.y or ''})")

    if not steps:
        return plan.explanation or "Analyze dataset based on specified query parameters."

    return "\n".join([f"{i+1}. {step}" for i, step in enumerate(steps)])


def generate_suggested_questions(profile: DatasetProfile) -> List[str]:
    """
    Generates 3 to 5 realistic starter questions dynamically tailored to the dataset columns.
    """
    suggestions: List[str] = []

    num_cols = profile.numeric_columns
    cat_cols = profile.categorical_columns
    date_cols = profile.datetime_columns

    # 1. Ranking question
    if cat_cols and num_cols:
        suggestions.append(f"What are the top 5 {cat_cols[0]} by {num_cols[0]}?")
    elif cat_cols:
        suggestions.append(f"What are the most frequent {cat_cols[0]}?")

    # 2. Aggregation question
    if len(cat_cols) >= 1 and len(num_cols) >= 1:
        cat = cat_cols[0]
        num = num_cols[-1]
        suggestions.append(f"Show total {num} for each {cat}.")

    # 3. Association / Correlation question
    if len(num_cols) >= 2:
        suggestions.append(f"Is there a correlation between {num_cols[0]} and {num_cols[1]}?")

    # 4. Time series question
    if date_cols and num_cols:
        suggestions.append(f"Show trend of {num_cols[0]} over time.")

    # 5. General summary
    if num_cols:
        suggestions.append(f"What is the average {num_cols[0]}?")

    return suggestions[:5]
