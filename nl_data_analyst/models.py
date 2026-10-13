"""
Pydantic data models for structured query planning, validation, and safe execution.
"""

from typing import Any, List, Literal, Optional, Union
from pydantic import BaseModel, Field


FilterOperator = Literal["==", "!=", ">", ">=", "<", "<=", "in", "contains"]
AggregationFunc = Literal["sum", "mean", "median", "min", "max", "count", "nunique", "std"]
SortDirection = Literal["asc", "desc"]
ChartType = Literal["bar", "line", "scatter", "histogram", "box", "pie", "heatmap"]
OperationType = Literal[
    "summary",
    "aggregate",
    "filter",
    "sort",
    "value_counts",
    "correlation",
    "unsupported",
]


class FilterCondition(BaseModel):
    """Specifies a deterministic filter predicate on a column."""
    column: str = Field(description="Column name to filter on")
    operator: FilterOperator = Field(description="Comparison operator")
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        description="Filter target value or list of values"
    )


class Aggregation(BaseModel):
    """Specifies an aggregation function applied to a column."""
    column: str = Field(description="Column to aggregate")
    func: AggregationFunc = Field(description="Aggregation function (e.g. sum, mean, count)")
    alias: Optional[str] = Field(default=None, description="Optional result column label")


class SortOrder(BaseModel):
    """Specifies sorting preferences."""
    column: str = Field(description="Column to sort by")
    direction: SortDirection = Field(default="desc", description="Sort direction: 'asc' or 'desc'")


class ChartSpec(BaseModel):
    """Specifies chart generation requirements."""
    needed: bool = Field(default=False, description="Whether a chart meaningfully aids understanding")
    chart_type: Optional[ChartType] = Field(default=None, description="Type of visual chart")
    x: Optional[str] = Field(default=None, description="X-axis column")
    y: Optional[str] = Field(default=None, description="Y-axis column or metric")
    color: Optional[str] = Field(default=None, description="Optional categorical dimension for color/grouping")
    title: Optional[str] = Field(default=None, description="Descriptive title for chart")


class AnalysisPlan(BaseModel):
    """
    Validated analysis plan produced by the planning engine or LLM.
    Strictly constrained to prevent code injection or unverified execution.
    """
    operation: OperationType = Field(
        description="High-level analysis operation"
    )
    columns: List[str] = Field(
        default_factory=list,
        description="Columns strictly required for this analysis"
    )
    filters: List[FilterCondition] = Field(
        default_factory=list,
        description="List of filter conditions to apply before aggregation/sorting"
    )
    group_by: List[str] = Field(
        default_factory=list,
        description="Categorical columns to group by (for 'aggregate')"
    )
    aggregations: List[Aggregation] = Field(
        default_factory=list,
        description="Aggregations to compute"
    )
    sort_by: List[SortOrder] = Field(
        default_factory=list,
        description="Sorting requirements"
    )
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of rows to return (e.g. Top N)"
    )
    chart: ChartSpec = Field(
        default_factory=ChartSpec,
        description="Chart specification"
    )
    explanation: str = Field(
        default="",
        description="Brief plain-language summary of how the question is answered"
    )
    unsupported_reason: Optional[str] = Field(
        default=None,
        description="Explanation if the request cannot be answered from the dataset"
    )
    follow_up_suggestion: Optional[str] = Field(
        default=None,
        description="Focused follow-up suggestion to guide the user"
    )


class DatasetProfile(BaseModel):
    """Safe, compact metadata profile of an uploaded dataset."""
    row_count: int
    column_count: int
    columns: List[str]
    column_types: dict[str, str]
    null_counts: dict[str, int]
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    sample_values: dict[str, List[str]] = Field(
        description="Strictly bounded sample values (2-3 distinct items max per column for schema hints)"
    )
    file_size_bytes: int
    memory_usage_bytes: int


class ExecutionResult(BaseModel):
    """Result of safe deterministic analysis execution."""
    success: bool
    direct_answer: str
    method_explanation: str
    data_records: Optional[List[dict[str, Any]]] = None
    chart_spec: Optional[ChartSpec] = None
    notes: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    is_unsupported: bool = False
