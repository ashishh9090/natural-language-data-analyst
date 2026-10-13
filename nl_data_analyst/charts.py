"""
Interactive Plotly chart generation for analysis execution results.
"""

from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from nl_data_analyst.models import ChartSpec, ExecutionResult


def create_result_chart(
    result: ExecutionResult,
    original_df: Optional[pd.DataFrame] = None,
) -> Optional[go.Figure]:
    """
    Generates a polished, interactive Plotly visualization for an ExecutionResult.
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

    chart_type = spec.chart_type
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

    # Color palette
    colorscale = "Tealgrn"

    try:
        fig: go.Figure

        if chart_type == "bar":
            fig = px.bar(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col or x_col,
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
                markers=True,
                title=title,
            )

        elif chart_type == "scatter":
            # For scatter, if we have original_df and spec columns, prefer plotting the full dataset points
            scatter_df = chart_df
            if original_df is not None and x_col in original_df.columns and y_col in original_df.columns:
                scatter_df = original_df.dropna(subset=[x_col, y_col])

            fig = px.scatter(
                scatter_df,
                x=x_col,
                y=y_col,
                color=color_col,
                trendline="ols" if len(scatter_df) >= 3 else None,
                title=title,
                hover_data=[c for c in scatter_df.columns if c not in [x_col, y_col]][:3],
            )

        elif chart_type == "histogram":
            fig = px.histogram(
                chart_df,
                x=x_col or y_col,
                color=color_col,
                marginal="box",
                title=title,
            )

        elif chart_type == "box":
            fig = px.box(
                chart_df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=title,
            )

        elif chart_type == "pie":
            fig = px.pie(
                chart_df,
                names=x_col,
                values=y_col if y_col in chart_df.columns else None,
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
            fig = px.bar(chart_df, x=x_col, y=y_col, title=title)

        # Polish aesthetics
        fig.update_layout(
            template="plotly_white",
            title_font=dict(size=16, family="Inter, sans-serif"),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="closest",
        )
        fig.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
        fig.update_yaxes(showgrid=True, gridcolor="#f0f0f0")

        return fig

    except Exception:
        # Graceful fallback: return None if plotting fails
        return None
