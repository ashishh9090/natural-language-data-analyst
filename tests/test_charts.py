import pandas as pd
from nl_data_analyst.charts import create_result_chart
from nl_data_analyst.models import ChartSpec, ExecutionResult


def test_create_result_chart_bar():
    result = ExecutionResult(
        success=True,
        direct_answer="Sample answer",
        method_explanation="Sample explanation",
        data_records=[
            {"category": "Electronics", "sales": 500.0},
            {"category": "Furniture", "sales": 300.0},
        ],
        chart_spec=ChartSpec(
            needed=True,
            chart_type="bar",
            x="category",
            y="sales",
            title="Sales by Category",
        ),
    )
    fig = create_result_chart(result)
    assert fig is not None
    assert fig.layout.title.text == "Sales by Category"


def test_create_result_chart_not_needed():
    result = ExecutionResult(
        success=True,
        direct_answer="Sample answer",
        method_explanation="Sample explanation",
        chart_spec=ChartSpec(needed=False),
    )
    fig = create_result_chart(result)
    assert fig is None
