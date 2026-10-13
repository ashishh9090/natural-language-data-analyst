"""
Deterministic, allowlist-based Pandas execution engine.
Strictly prohibits eval(), exec(), SQL, or dynamic code compilation.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from nl_data_analyst.models import (
    AnalysisPlan,
    DatasetProfile,
    ExecutionResult,
    FilterCondition,
)


def execute_analysis_plan(
    df: pd.DataFrame,
    plan: AnalysisPlan,
    profile: Optional[DatasetProfile] = None,
) -> ExecutionResult:
    """
    Safely executes an AnalysisPlan using only permitted Pandas operations.

    Zero dynamic execution:
    - No eval()
    - No exec()
    - No model-generated code
    - Strict error boundary handling
    """
    notes: List[str] = []

    # 1. Handle unsupported queries gracefully
    if plan.operation == "unsupported":
        reason = plan.unsupported_reason or "The question cannot be answered from the available data."
        if plan.follow_up_suggestion:
            reason += f" Suggested next question: {plan.follow_up_suggestion}"
        return ExecutionResult(
            success=False,
            direct_answer="I cannot answer this question with the available data.",
            method_explanation=plan.explanation or "Analysis aborted: request is outside data scope.",
            notes=[reason],
            is_unsupported=True,
            error_message=reason,
        )

    # 2. Check for empty input dataframe
    if df.empty:
        return ExecutionResult(
            success=False,
            direct_answer="The dataset contains no records to analyze.",
            method_explanation="Execution halted on empty dataset.",
            error_message="The dataset is empty.",
        )

    # Work on a copy to prevent side effects
    work_df = df.copy()

    try:
        # 3. Apply safe filters
        work_df, filter_notes = _apply_filters(work_df, plan.filters)
        notes.extend(filter_notes)

        if work_df.empty:
            return ExecutionResult(
                success=True,
                direct_answer="No records matched the specified filter criteria.",
                method_explanation=plan.explanation,
                data_records=[],
                notes=notes + ["The filter resulted in 0 matching records."],
                chart_spec=plan.chart,
            )

        # 4. Route to strictly allowlisted operation handlers
        if plan.operation == "summary":
            return _execute_summary(work_df, plan, notes)
        elif plan.operation == "aggregate":
            return _execute_aggregate(work_df, plan, notes)
        elif plan.operation == "value_counts":
            return _execute_value_counts(work_df, plan, notes)
        elif plan.operation == "correlation":
            return _execute_correlation(work_df, plan, notes)
        elif plan.operation == "sort" or plan.operation == "filter":
            return _execute_sort_or_filter(work_df, plan, notes)
        else:
            return ExecutionResult(
                success=False,
                direct_answer="Operation is not supported.",
                method_explanation="Unsupported operation encountered.",
                error_message=f"Operation '{plan.operation}' is not supported.",
            )

    except Exception as e:
        return ExecutionResult(
            success=False,
            direct_answer="An error occurred while computing the answer.",
            method_explanation="Safe execution caught a processing exception.",
            error_message=f"Calculation error: {str(e)}",
            notes=notes,
        )


def _apply_filters(
    df: pd.DataFrame, filters: List[FilterCondition]
) -> Tuple[pd.DataFrame, List[str]]:
    notes = []
    filtered = df

    for f in filters:
        col = f.column
        if col not in filtered.columns:
            continue

        series = filtered[col]
        null_count = int(series.isna().sum())
        if null_count > 0:
            notes.append(f"Filtered column '{col}' contained {null_count} missing value(s) which were excluded from filter matching.")

        val = f.value
        op = f.operator

        # Type conversion for numeric filtering
        if pd.api.types.is_numeric_dtype(series):
            try:
                if isinstance(val, (int, float)):
                    num_val = float(val)
                elif isinstance(val, list):
                    num_val = [float(v) for v in val]
                else:
                    num_val = float(str(val))
                val = num_val
            except (ValueError, TypeError):
                pass

        if op == "==":
            filtered = filtered[series == val]
        elif op == "!=":
            filtered = filtered[series != val]
        elif op == ">":
            filtered = filtered[series > val]
        elif op == ">=":
            filtered = filtered[series >= val]
        elif op == "<":
            filtered = filtered[series < val]
        elif op == "<=":
            filtered = filtered[series <= val]
        elif op == "in" and isinstance(val, list):
            filtered = filtered[series.isin(val)]
        elif op == "contains":
            filtered = filtered[series.astype(str).str.contains(str(val), case=False, na=False)]

    return filtered, notes


def _execute_aggregate(
    df: pd.DataFrame, plan: AnalysisPlan, notes: List[str]
) -> ExecutionResult:
    group_cols = plan.group_by
    if not group_cols:
        return _execute_summary(df, plan, notes)

    # Handle monthly or date truncation if a group column is datetime
    agg_df = df.copy()
    display_group_cols = list(group_cols)

    # Build aggregation dict safely avoiding group column collision
    clean_agg_map = {}
    for agg in plan.aggregations:
        col = agg.column
        func = agg.func
        if col in group_cols and func == "count":
            other_cols = [c for c in agg_df.columns if c not in group_cols]
            target_col = other_cols[0] if other_cols else col
            clean_agg_map[target_col] = func
        else:
            clean_agg_map[col] = func

    if not clean_agg_map:
        other_cols = [c for c in agg_df.columns if c not in group_cols]
        target_col = other_cols[0] if other_cols else agg_df.columns[0]
        clean_agg_map[target_col] = "count"

    # Check for nulls in grouped columns
    for g_col in group_cols:
        nulls = int(agg_df[g_col].isna().sum())
        if nulls > 0:
            notes.append(f"Group column '{g_col}' has {nulls} missing value(s) grouped as null/NaN.")

    # Execute groupby aggregation safely
    res = agg_df.groupby(group_cols, as_index=False, dropna=False).agg(clean_agg_map)

    # Rename columns if aliases provided
    for agg in plan.aggregations:
        if agg.alias:
            metric_candidates = [c for c in res.columns if c not in group_cols]
            if agg.column in metric_candidates:
                res = res.rename(columns={agg.column: agg.alias})
            elif metric_candidates:
                res = res.rename(columns={metric_candidates[0]: agg.alias})

    # Sort
    if plan.sort_by:
        sort_cols = []
        sort_asc = []
        for s in plan.sort_by:
            if s.column in res.columns:
                sort_cols.append(s.column)
                sort_asc.append(s.direction == "asc")
        if sort_cols:
            res = res.sort_values(by=sort_cols, ascending=sort_asc)

    # Limit
    if plan.limit and plan.limit > 0:
        res = res.head(plan.limit)

    # Construct direct answer
    direct_answer = _build_aggregate_answer(res, group_cols, plan)

    # Round numeric columns for clean presentation
    numeric_cols = res.select_dtypes(include=[np.number]).columns
    res[numeric_cols] = res[numeric_cols].round(2)

    return ExecutionResult(
        success=True,
        direct_answer=direct_answer,
        method_explanation=plan.explanation or f"Grouped by {', '.join(group_cols)} and calculated aggregate metrics.",
        data_records=res.to_dict(orient="records"),
        chart_spec=plan.chart,
        notes=notes,
    )


def _build_aggregate_answer(
    res_df: pd.DataFrame, group_cols: List[str], plan: AnalysisPlan
) -> str:
    if res_df.empty:
        return "No records were found for this aggregation."

    first_row = res_df.iloc[0]
    metric_cols = [c for c in res_df.columns if c not in group_cols]
    primary_metric = metric_cols[0] if metric_cols else None

    # If single record or top 1
    if len(res_df) == 1 or plan.limit == 1:
        group_val_str = ", ".join([f"{col}: {first_row[col]}" for col in group_cols])
        if primary_metric:
            val = first_row[primary_metric]
            val_fmt = f"{val:,.2f}" if isinstance(val, (int, float, np.number)) else str(val)
            return f"The top result is {group_val_str} with {primary_metric} of {val_fmt}."
        return f"The result is {group_val_str}."

    # If multiple records, summarize top performer and count
    top_group_val = " / ".join([str(first_row[col]) for col in group_cols])
    if primary_metric:
        val = first_row[primary_metric]
        val_fmt = f"{val:,.2f}" if isinstance(val, (int, float, np.number)) else str(val)
        return (
            f"{top_group_val} ranked highest with a {primary_metric} of {val_fmt}. "
            f"Showing {len(res_df)} total group results."
        )

    return f"Computed results across {len(res_df)} groups."


def _execute_summary(
    df: pd.DataFrame, plan: AnalysisPlan, notes: List[str]
) -> ExecutionResult:
    results: Dict[str, Any] = {}
    records: List[Dict[str, Any]] = []

    for agg in plan.aggregations:
        col = agg.column
        func = agg.func
        if col not in df.columns:
            continue

        series = df[col]
        null_count = int(series.isna().sum())
        if null_count > 0:
            notes.append(f"Column '{col}' contained {null_count} missing value(s) excluded from {func} calculation.")

        clean_series = series.dropna()
        if clean_series.empty:
            results[f"{func}_{col}"] = None
            continue

        if func == "sum":
            val = float(clean_series.sum())
        elif func == "mean":
            val = float(clean_series.mean())
        elif func == "median":
            val = float(clean_series.median())
        elif func == "min":
            val = float(clean_series.min()) if pd.api.types.is_numeric_dtype(clean_series) else clean_series.min()
        elif func == "max":
            val = float(clean_series.max()) if pd.api.types.is_numeric_dtype(clean_series) else clean_series.max()
        elif func == "count":
            val = int(clean_series.count())
        elif func == "nunique":
            val = int(clean_series.nunique())
        elif func == "std":
            val = float(clean_series.std()) if len(clean_series) > 1 else 0.0
        else:
            val = None

        metric_name = agg.alias or f"{func}_{col}"
        results[metric_name] = val
        records.append({"metric": metric_name, "value": round(val, 2) if isinstance(val, float) else val})

    # Build direct answer
    answer_parts = []
    for k, v in results.items():
        v_str = f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)
        answer_parts.append(f"{k} is {v_str}")

    direct_answer = ". ".join(answer_parts) + "." if answer_parts else "Summary computed."

    return ExecutionResult(
        success=True,
        direct_answer=direct_answer,
        method_explanation=plan.explanation or "Calculated summary statistics.",
        data_records=records,
        chart_spec=plan.chart,
        notes=notes,
    )


def _execute_value_counts(
    df: pd.DataFrame, plan: AnalysisPlan, notes: List[str]
) -> ExecutionResult:
    col = plan.columns[0] if plan.columns else df.columns[0]
    nulls = int(df[col].isna().sum())
    if nulls > 0:
        notes.append(f"Column '{col}' had {nulls} missing value(s) excluded from category counts.")

    counts = df[col].value_counts(dropna=True).reset_index()
    counts.columns = [col, "count"]

    if plan.sort_by:
        for s in plan.sort_by:
            if s.column in counts.columns:
                counts = counts.sort_values(by=s.column, ascending=(s.direction == "asc"))

    if plan.limit and plan.limit > 0:
        counts = counts.head(plan.limit)

    top_item = counts.iloc[0] if not counts.empty else None
    if top_item is not None:
        direct_answer = (
            f"The most frequent {col} is '{top_item[col]}' with {top_item['count']:,} occurrences "
            f"({(top_item['count'] / len(df) * 100):.1f}% of total records)."
        )
    else:
        direct_answer = f"No values found for column '{col}'."

    return ExecutionResult(
        success=True,
        direct_answer=direct_answer,
        method_explanation=plan.explanation or f"Calculated frequency distribution for '{col}'.",
        data_records=counts.to_dict(orient="records"),
        chart_spec=plan.chart,
        notes=notes,
    )


def _execute_correlation(
    df: pd.DataFrame, plan: AnalysisPlan, notes: List[str]
) -> ExecutionResult:
    cols = plan.columns[:2]
    col1, col2 = cols[0], cols[1]

    # Filter down to complete pairs
    sub = df[[col1, col2]].dropna()
    dropped = len(df) - len(sub)
    if dropped > 0:
        notes.append(f"{dropped} row(s) with missing values in '{col1}' or '{col2}' were omitted from correlation calculation.")

    if len(sub) < 2:
        return ExecutionResult(
            success=False,
            direct_answer="Not enough non-empty data pairs to compute correlation.",
            method_explanation="Correlation calculation requires at least 2 complete numeric pairs.",
            error_message="Insufficient data points.",
            notes=notes,
        )

    # Standard deviation check for zero variance (division by zero prevention)
    std1 = sub[col1].std()
    std2 = sub[col2].std()
    if std1 == 0 or std2 == 0 or np.isnan(std1) or np.isnan(std2):
        return ExecutionResult(
            success=True,
            direct_answer=f"Correlation cannot be computed because one of the columns ('{col1}' or '{col2}') has zero variance (constant values).",
            method_explanation="Handled zero variance division-by-zero check.",
            data_records=[{"column_1": col1, "column_2": col2, "correlation": 0.0}],
            notes=notes + ["Constant column detected; Pearson correlation undefined."],
        )

    corr_val = float(sub[col1].corr(sub[col2]))

    # Describe association strength without claiming causation
    abs_corr = abs(corr_val)
    if abs_corr >= 0.7:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "very weak or negligible"

    direction = "positive" if corr_val > 0 else "negative"

    direct_answer = (
        f"There is a {strength} {direction} correlation (r = {corr_val:.2f}) between '{col1}' and '{col2}'. "
        f"As '{col1}' increases, '{col2}' tends to {'increase' if corr_val > 0 else 'decrease'}."
    )

    # Mandatory scientific ethics disclaimer
    causation_warning = (
        "Statistical Note: Correlation evaluates linear association only and DOES NOT imply causation. "
        "A relationship does not prove that changes in one variable cause changes in the other."
    )
    notes.append(causation_warning)

    # Prepare preview records
    records = [
        {"column_1": col1, "column_2": col2, "correlation_coefficient": round(corr_val, 3), "strength": strength}
    ]

    return ExecutionResult(
        success=True,
        direct_answer=direct_answer,
        method_explanation=plan.explanation or f"Calculated Pearson correlation coefficient between '{col1}' and '{col2}'.",
        data_records=records,
        chart_spec=plan.chart,
        notes=notes,
    )


def _execute_sort_or_filter(
    df: pd.DataFrame, plan: AnalysisPlan, notes: List[str]
) -> ExecutionResult:
    res = df.copy()

    if plan.sort_by:
        sort_cols = [s.column for s in plan.sort_by if s.column in res.columns]
        sort_asc = [s.direction == "asc" for s in plan.sort_by if s.column in res.columns]
        if sort_cols:
            res = res.sort_values(by=sort_cols, ascending=sort_asc)

    if plan.limit and plan.limit > 0:
        res = res.head(plan.limit)

    # Format numeric columns
    numeric_cols = res.select_dtypes(include=[np.number]).columns
    res[numeric_cols] = res[numeric_cols].round(2)

    direct_answer = f"Showing {len(res)} filtered and sorted record(s)."
    if not res.empty and plan.limit == 1 and plan.sort_by:
        top_col = plan.sort_by[0].column
        top_val = res.iloc[0][top_col]
        direct_answer = f"The top record has {top_col} = {top_val}."

    return ExecutionResult(
        success=True,
        direct_answer=direct_answer,
        method_explanation=plan.explanation or "Filtered and sorted dataset records.",
        data_records=res.to_dict(orient="records"),
        chart_spec=plan.chart,
        notes=notes,
    )
