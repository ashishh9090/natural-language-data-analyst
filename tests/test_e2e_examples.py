from pathlib import Path
import pytest
from nl_data_analyst.data import load_csv_safely, profile_dataset
from nl_data_analyst.executor import execute_analysis_plan
from nl_data_analyst.charts import create_result_chart
from nl_data_analyst.llm import HeuristicMockProvider
from nl_data_analyst.planner import validate_plan_against_schema, explain_plan_in_plain_english


@pytest.fixture
def ecommerce_dataset():
    sample_path = Path(__file__).parent.parent / "sample_data" / "ecommerce_orders.csv"
    df, size = load_csv_safely(str(sample_path))
    profile = profile_dataset(df, file_size_bytes=size)
    return df, profile


def test_e2e_highest_revenue_product(ecommerce_dataset):
    df, profile = ecommerce_dataset
    planner = HeuristicMockProvider()
    question = "Which product had the highest revenue?"

    plan = planner.generate_plan(question, profile)
    valid, err = validate_plan_against_schema(plan, profile)
    assert valid is True
    assert err is None

    result = execute_analysis_plan(df, plan, profile)
    assert result.success is True
    assert "UltraSharp 4K Monitor" in result.direct_answer
    assert round(result.data_records[0]["sales"], 2) == 3999.92

    chart = create_result_chart(result, original_df=df)
    assert chart is not None


def test_e2e_monthly_sales_by_region(ecommerce_dataset):
    df, profile = ecommerce_dataset
    planner = HeuristicMockProvider()
    question = "Show monthly sales for each region."

    plan = planner.generate_plan(question, profile)
    valid, err = validate_plan_against_schema(plan, profile)
    assert valid is True

    result = execute_analysis_plan(df, plan, profile)
    assert result.success is True
    assert len(result.data_records) > 0

    chart = create_result_chart(result, original_df=df)
    assert chart is not None


def test_e2e_discounts_and_profit_correlation(ecommerce_dataset):
    df, profile = ecommerce_dataset
    planner = HeuristicMockProvider()
    question = "Are higher discounts associated with lower profit?"

    plan = planner.generate_plan(question, profile)
    valid, err = validate_plan_against_schema(plan, profile)
    assert valid is True

    result = execute_analysis_plan(df, plan, profile)
    assert result.success is True
    assert "correlation" in result.direct_answer.lower()
    # Check scientific causation disclaimer is explicitly present
    assert any("does not imply causation" in note.lower() for note in result.notes)

    chart = create_result_chart(result, original_df=df)
    assert chart is not None


def test_e2e_top_five_categories_order_count(ecommerce_dataset):
    df, profile = ecommerce_dataset
    planner = HeuristicMockProvider()
    question = "What are the top five categories by order count?"

    plan = planner.generate_plan(question, profile)
    valid, err = validate_plan_against_schema(plan, profile)
    assert valid is True

    result = execute_analysis_plan(df, plan, profile)
    assert result.success is True
    assert len(result.data_records) <= 5
    assert result.data_records[0]["category"] == "Electronics"

    chart = create_result_chart(result, original_df=df)
    assert chart is not None
