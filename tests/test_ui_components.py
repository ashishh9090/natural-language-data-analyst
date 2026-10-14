"""
Unit tests for modular UI component functions.
"""

import pandas as pd
from nl_data_analyst.models import (
    Aggregation,
    AnalysisPlan,
    ChartSpec,
    DatasetProfile,
    ExecutionResult,
)
from nl_data_analyst.charts import get_suitable_chart_types, create_result_chart


def test_chart_suitable_types_bar():
    result = ExecutionResult(
        success=True,
        direct_answer="Top product is Laptop",
        method_explanation="Summed revenue by product",
        data_records=[
            {"product": "Laptop", "sales": 1200.0},
            {"product": "Monitor", "sales": 800.0},
        ],
        chart_spec=ChartSpec(
            needed=True,
            chart_type="bar",
            x="product",
            y="sales",
            title="Sales by Product",
        ),
    )
    types = get_suitable_chart_types(result)
    assert "bar" in types
    assert "line" in types
    assert "pie" in types

    # Verify switching chart type to pie works
    fig_pie = create_result_chart(result, override_chart_type="pie")
    assert fig_pie is not None


def test_chart_suitable_types_scatter():
    df = pd.DataFrame({
        "discount": [0.05, 0.10, 0.20],
        "profit": [20.0, 10.0, 50.0],
    })
    result = ExecutionResult(
        success=True,
        direct_answer="Correlation is 0.85",
        method_explanation="Calculated Pearson r",
        data_records=df.to_dict(orient="records"),
        chart_spec=ChartSpec(
            needed=True,
            chart_type="scatter",
            x="discount",
            y="profit",
            title="Discount vs Profit",
        ),
    )
    types = get_suitable_chart_types(result)
    assert "scatter" in types
    assert "line" in types

    fig_scatter = create_result_chart(result, original_df=df)
    assert fig_scatter is not None
