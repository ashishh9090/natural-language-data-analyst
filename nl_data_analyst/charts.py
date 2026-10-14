"""
Interactive Plotly chart generation for analysis execution results.
"""

from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from nl_data_analyst.models import ChartSpec, ExecutionResult

try:
    import statsmodels.api  # noqa: F401
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


def get_suitable_chart_types(result: ExecutionResult) -> List[str]:
    """
    Returns a list of plausible alternate chart types for an ExecutionResult.
    """
    spec = result.chart_spec
    if not spec or not spec.needed or not spec.chart_type:
        return []

    default_type = spec.chart_type.lower()
    if default_type == "bar":
        # If records exist and are non-negative, pie is also suitable
        if result.data_records:
            return ["bar", "line", "pie"]
        return ["bar", "line"]
    elif default_type == "line":
        return ["line", "bar", "scatter"]
    elif default_type == "scatter":
        return ["scatter", "line"]
    elif default_type == "histogram":
        return ["histogram", "box"]
    elif default_type == "box":
        return ["box", "histogram"]
    elif default_type == "pie":
        return ["pie", "bar"]
    elif default_type == "heatmap":
        return ["heatmap"]
    return [default_type]


def create_result_chart(
    result: ExecutionResult,
    original_df: Optional[pd.DataFrame] = None,
    override_chart_type: Optional[str] = None,
) -> Optional[go.Figure]:
    """
    Generates a polished, interactive Plotly visualization for an ExecutionResult.
    Optionally allows overriding the chart type with a user-selected choice.
    Returns None if chart is not needed or data cannot support plotting.
    """
    spec = result.chart_spec
    if not spec or not spec.needed or not spec.chart_type:
        return None

    # Determine data source for charting
    chart_df: pd.DataFrame
    if result.data_records and len(result.data_records) > 0:
        chart_df = pd.DataFrame(result.data_records)
    elif original_df is not None and not original_df.empty:
        chart_df = original_df
    else:
        return None

    if chart_df.empty:
        return None

    chart_type = (override_chart_type or spec.chart_type).lower()
    x_col = spec.x
    y_col = spec.y
    color_col = spec.color if spec.color in chart_df.columns else None
    title = spec.title or f"{y_col or ''} by {x_col or ''}".strip()

    # If specified columns are not directly in chart_df, attempt smart fallback
    cols = chart_df.columns.tolist()
    if x_col and x_col not in cols:
        x_col = cols[0]
    if y_col and y_col not in cols and len(cols) > 1:
        y_col = cols[1]

    # Accessible, polished color palette: Primary indigo/teal accent with high readability
    color_palette = [
        "#4f46e5",  # Indigo 600
        "#06b6d4",  # Cyan 500
        "#10b981",  # Emerald 500
        "#f59e0b",  # Amber 500
        "#ec4899",  # Pink 500
        "#8b5cf6",  # Violet 500
        "#3b82f6",  # Blue 500
    ]

    try:
        fig: go.Figure

        if chart_type == "bar":
            fig = px.bar(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col or (x_col if len(chart_df) <= 10 else None),
                color_discrete_sequence=color_palette,
                title=title,
                text_auto=".2s" if y_col and pd.api.types.is_numeric_dtype(chart_df.get(y_col)) else False,
            )
            fig.update_layout(showlegend=bool(color_col))

        elif chart_type == "line":
            fig = px.line(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col,
                color_discrete_sequence=color_palette,
                markers=True,
                title=title,
            )

        elif chart_type == "scatter":
            # For scatter, if we have original_df and spec columns, prefer plotting full dataset points
            scatter_df = chart_df
            if original_df is not None and x_col in original_df.columns and y_col in original_df.columns:
                scatter_df = original_df.dropna(subset=[x_col, y_col])

            use_trendline = (
                HAS_STATSMODELS
                and len(scatter_df) >= 3
                and pd.api.types.is_numeric_dtype(scatter_df.get(x_col))
                and pd.api.types.is_numeric_dtype(scatter_df.get(y_col))
            )

            fig = px.scatter(
                scatter_df,
                x=x_col,
                y=y_col,
                color=color_col,
                color_discrete_sequence=color_palette,
                trendline="ols" if use_trendline else None,
                title=title,
                hover_data=[c for c in scatter_df.columns if c not in [x_col, y_col]][:3],
            )

        elif chart_type == "histogram":
            fig = px.histogram(
                chart_df,
                x=x_col or y_col,
                color=color_col,
                color_discrete_sequence=color_palette,
                marginal="box",
                title=title,
            )

        elif chart_type == "box":
            fig = px.box(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col,
                color_discrete_sequence=color_palette,
                title=title,
            )

        elif chart_type == "pie":
            fig = px.pie(
                chart_df,
                names=x_col,
                values=y_col if y_col in chart_df.columns else None,
                color_discrete_sequence=color_palette,
                title=title,
                hole=0.4,
            )

        elif chart_type == "heatmap":
            # Correlation heatmap
            numeric_cols = chart_df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) >= 2:
                corr_matrix = chart_df[numeric_cols].corr()
                fig = px.imshow(
                    corr_matrix,
                    text_auto=".2f",
                    color_continuous_scale="RdBu_r",
                    zmin=-1,
                    zmax=1,
                    title="Correlation Heatmap",
                )
            else:
                return None
        else:
            # Fallback bar chart
            fig = px.bar(
                chart_df,
                x=x_col,
                y=y_col,
                title=title,
                color_discrete_sequence=color_palette,
            )

        # Polished, clean styling
        fig.update_layout(
            template="plotly_white",
            title_font=dict(size=16, family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#0f172a"),
            font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", color="#334155"),
            margin=dict(l=40, r=40, t=55, b=45),
            hovermode="closest",
            plot_bgcolor="rgba(248, 250, 252, 0.5)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)

        return fig

    except Exception:
        # Graceful fallback: return None if plotting fails
        return None
