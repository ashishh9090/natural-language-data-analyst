import pandas as pd
import pytest
from nl_data_analyst.data import profile_dataset
from nl_data_analyst.models import (
    Aggregation,
    AnalysisPlan,
    ChartSpec,
    FilterCondition,
    SortOrder,
)
from nl_data_analyst.planner import (
    explain_plan_in_plain_english,
    validate_plan_against_schema,
)
from nl_data_analyst.llm import HeuristicMockProvider


@pytest.fixture
def sample_profile():
    df = pd.DataFrame({
        "product": ["A", "B", "C"],
        "region": ["North", "South", "East"],
        "sales": [100.0, 200.0, 300.0],
        "discount": [0.1, 0.2, 0.3],
        "profit": [20.0, 40.0, 60.0],
    })
    return profile_dataset(df)


def test_validate_valid_plan(sample_profile):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["region", "sales"],
        group_by=["region"],
        aggregations=[Aggregation(column="sales", func="sum")],
        sort_by=[SortOrder(column="sales", direction="desc")],
    )
    is_valid, err = validate_plan_against_schema(plan, sample_profile)
    assert is_valid is True
    assert err is None


def test_validate_invalid_column(sample_profile):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["non_existent_column"],
        group_by=["non_existent_column"],
        aggregations=[Aggregation(column="sales", func="sum")],
    )
    is_valid, err = validate_plan_against_schema(plan, sample_profile)
    assert is_valid is False
    assert "non_existent_column" in err


def test_validate_non_numeric_sum(sample_profile):
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["region"],
        group_by=["region"],
        aggregations=[Aggregation(column="region", func="sum")],
    )
    is_valid, err = validate_plan_against_schema(plan, sample_profile)
    assert is_valid is False
    assert "non-numeric" in err


def test_validate_unsupported_operation(sample_profile):
    plan = AnalysisPlan.model_construct(
        operation="arbitrary_exec_hack",
        columns=["sales"],
    )
    is_valid, err = validate_plan_against_schema(plan, sample_profile)
    assert is_valid is False
    assert "Disallowed operation" in err


def test_explain_plan():
    plan = AnalysisPlan(
        operation="aggregate",
        columns=["region", "sales"],
        group_by=["region"],
        aggregations=[Aggregation(column="sales", func="sum")],
        sort_by=[SortOrder(column="sales", direction="desc")],
        limit=5,
        chart=ChartSpec(needed=True, chart_type="bar", x="region", y="sales"),
    )
    explanation = explain_plan_in_plain_english(plan)
    assert "Group records by 'region'" in explanation
    assert "Compute SUM" in explanation
    assert "Limit output to top 5" in explanation


def test_heuristic_planner_top_revenue(sample_profile):
    planner = HeuristicMockProvider()
    plan = planner.generate_plan("Which product had the highest revenue?", sample_profile)
    assert plan.operation == "aggregate"
    assert "product" in plan.group_by
    assert plan.sort_by[0].direction == "desc"
    assert plan.limit == 1


def test_heuristic_planner_correlation(sample_profile):
    planner = HeuristicMockProvider()
    plan = planner.generate_plan("Are higher discounts associated with lower profit?", sample_profile)
    assert plan.operation == "correlation"
    assert "discount" in plan.columns
    assert "profit" in plan.columns
    assert "causation" in plan.explanation.lower()


def test_heuristic_planner_unsupported(sample_profile):
    planner = HeuristicMockProvider()
    plan = planner.generate_plan("What is the weather in Paris tomorrow?", sample_profile)
    assert plan.operation == "unsupported"
    assert plan.unsupported_reason is not None
