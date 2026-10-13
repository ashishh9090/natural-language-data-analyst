import pandas as pd
import pytest
from nl_data_analyst.executor import execute_analysis_plan
from nl_data_analyst.models import (
    Aggregation,
    AnalysisPlan,
    ChartSpec,
    FilterCondition,
    SortOrder,
)


@pytest.fixture
def ecommerce_df():
    return pd.DataFrame({
        "product": ["Keyboard", "Mouse", "Monitor", "Keyboard", "Laptop"],
        "region": ["North", "North", "South", "East", "West"],
        "sales": [100.0, 50.0, 300.0, 150.0, 1200.0],
        "discount": [0.05, 0.10, 0.20, 0.05, 0.15],
        "profit": [20.0, 10.0, 50.0, 35.0, 250.0],
        "quantity": [2, 1, 1, 3, 1],
    })


def test_execute_highest_revenue(ecommerce_df):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["product", "sales"],
        group_by=["product"],
        aggregations=[Aggregation(column="sales", func="sum")],
        sort_by=[SortOrder(column="sales", direction="desc")],
        limit=1,
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    assert "Laptop" in result.direct_answer
    assert result.data_records[0]["product"] == "Laptop"
    assert result.data_records[0]["sales"] == 1200.0


def test_execute_group_by_region(ecommerce_df):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["region", "sales"],
        group_by=["region"],
        aggregations=[Aggregation(column="sales", func="sum")],
        sort_by=[SortOrder(column="sales", direction="desc")],
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    assert len(result.data_records) == 4
    # Top region should be West (1200) or North (150)
    assert result.data_records[0]["region"] == "West"


def test_execute_value_counts(ecommerce_df):
    plan = AnalysisPlan(
        operation="value_counts",
        columns=["product"],
        limit=5,
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    assert "Keyboard" in result.direct_answer
    assert result.data_records[0]["product"] == "Keyboard"
    assert result.data_records[0]["count"] == 2


def test_execute_correlation_with_disclaimer(ecommerce_df):
    plan = AnalysisPlan(
        operation="correlation",
        columns=["discount", "profit"],
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    assert "correlation" in result.direct_answer.lower()
    # Ensure scientific causation disclaimer is present in notes
    disclaimers = [n for n in result.notes if "does not imply causation" in n.lower()]
    assert len(disclaimers) > 0


def test_execute_correlation_zero_variance():
    df = pd.DataFrame({
        "constant_col": [5.0, 5.0, 5.0, 5.0],
        "varying_col": [10.0, 20.0, 30.0, 40.0],
    })
    plan = AnalysisPlan(
        operation="correlation",
        columns=["constant_col", "varying_col"],
    )
    result = execute_analysis_plan(df, plan)
    assert result.success is True
    assert "zero variance" in result.direct_answer


def test_execute_filters(ecommerce_df):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["product", "sales"],
        filters=[FilterCondition(column="region", operator="==", value="North")],
        group_by=["product"],
        aggregations=[Aggregation(column="sales", func="sum")],
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    products = [r["product"] for r in result.data_records]
    assert "Monitor" not in products  # Monitor is South
    assert "Keyboard" in products
    assert "Mouse" in products


def test_execute_filter_no_results(ecommerce_df):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["product", "sales"],
        filters=[FilterCondition(column="region", operator="==", value="NonExistentRegion")],
        group_by=["product"],
        aggregations=[Aggregation(column="sales", func="sum")],
    )
    result = execute_analysis_plan(ecommerce_df, plan)
    assert result.success is True
    assert "No records matched" in result.direct_answer


def test_execute_missing_values():
    df = pd.DataFrame({
        "category": ["A", "A", "B", None],
        "amount": [10.0, None, 30.0, 40.0],
    })
    plan = AnalysisPlan(
        operation="summary",
        columns=["amount"],
        aggregations=[Aggregation(column="amount", func="mean")],
    )
    result = execute_analysis_plan(df, plan)
    assert result.success is True
    # Average of 10, 30, 40 is 80/3 ≈ 26.67
    assert any("missing value" in note for note in result.notes)


def test_execute_unsupported():
    plan = AnalysisPlan(
        operation="unsupported",
        unsupported_reason="Columns requested are not in dataset.",
        follow_up_suggestion="Ask about sales.",
    )
    result = execute_analysis_plan(pd.DataFrame({"x": [1]}), plan)
    assert result.success is False
    assert result.is_unsupported is True
    assert "cannot answer" in result.direct_answer.lower()
