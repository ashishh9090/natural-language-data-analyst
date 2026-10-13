"""
Pluggable LLM interface with support for Gemini, OpenAI, Anthropic,
and an offline HeuristicMockProvider for testing and zero-key local usage.
"""

from abc import ABC, abstractmethod
import json
import os
import re
from typing import Any, Dict, Optional, Tuple
import httpx
from pydantic import ValidationError

from nl_data_analyst.models import (
    Aggregation,
    AnalysisPlan,
    ChartSpec,
    DatasetProfile,
    FilterCondition,
    SortOrder,
)

PLAN_SYSTEM_PROMPT = """You are a senior data analyst. Your job is to convert natural language questions about a dataset into a safe, structured analysis plan.

CRITICAL CONSTRAINTS:
1. ONLY refer to columns that exist in the provided schema. If a requested concept does not map to any column, set operation to "unsupported" and explain why in "unsupported_reason".
2. NEVER write Python code, SQL, shell commands, or expressions.
3. Allowed operations:
   - "summary": overall dataset statistics or single-column summary.
   - "aggregate": group by one or more categorical columns and compute metrics (sum, mean, median, min, max, count, nunique, std).
   - "filter": filter rows matching explicit conditions.
   - "sort": rank/sort rows or aggregated values (e.g. top N, lowest N).
   - "value_counts": count occurrences of distinct categories.
   - "correlation": compute pairwise linear correlation between numeric columns.
   - "unsupported": if the question cannot be answered from the dataset, is ambiguous, or requests unsupported calculations.
4. Chart guidelines:
   - If a chart helps the user understand the answer, set chart.needed = true, specify chart_type ("bar", "line", "scatter", "histogram", "box", "pie", "heatmap") and specify x, y, and optional color.
   - For correlation, use chart_type "scatter" or "heatmap".
   - For categorical comparisons/rankings, use "bar".
   - For time series, use "line".
5. In "explanation", write a concise 1-2 sentence description of the method and columns.
6. If the question implies causation (e.g., "does X cause Y?"), plan a correlation or comparison, but note in the explanation that correlation does not establish causation.
7. Return ONLY a valid JSON object matching the requested schema. No markdown formatting, no backticks.
"""


def format_schema_for_llm(profile: DatasetProfile) -> str:
    """Formats the compact schema profile for model consumption."""
    col_details = []
    for col in profile.columns:
        samples = ", ".join([f"'{s}'" for s in profile.sample_values.get(col, [])])
        col_type = profile.column_types.get(col, "unknown")
        nulls = profile.null_counts.get(col, 0)
        col_details.append(
            f"- {col} (dtype: {col_type}, nulls: {nulls}, samples: [{samples}])"
        )

    return (
        f"DATASET PROFILE:\n"
        f"Total rows: {profile.row_count}\n"
        f"Columns ({profile.column_count}):\n"
        + "\n".join(col_details)
        + f"\n\nNumeric columns: {profile.numeric_columns}\n"
        f"Categorical columns: {profile.categorical_columns}\n"
        f"Datetime columns: {profile.datetime_columns}\n"
    )


class LLMProvider(ABC):
    """Abstract interface for LLM planning providers."""

    @abstractmethod
    def generate_plan(self, question: str, profile: DatasetProfile) -> AnalysisPlan:
        """Translates a user question into a validated AnalysisPlan."""
        pass


def normalize_word(w: str) -> str:
    """Normalizes word for singular/plural matching."""
    clean = re.sub(r"[^\w]", "", w.lower())
    if clean.endswith("ies") and len(clean) > 4:
        return clean[:-3] + "y"
    if clean.endswith("es") and len(clean) > 4:
        return clean[:-2]
    if clean.endswith("s") and len(clean) > 3 and not clean.endswith("ss"):
        return clean[:-1]
    return clean


def find_matching_columns(columns: list[str], text: str) -> list[str]:
    """Finds dataset columns that match concepts in user query."""
    text_lower = text.lower()
    q_words = {normalize_word(w) for w in text.split() if len(w) > 1}
    matches = []

    for col in columns:
        col_lower = col.lower()
        if col_lower in text_lower:
            matches.append(col)
            continue
        col_tokens = [normalize_word(t) for t in col_lower.replace("_", " ").split()]
        if any(t in q_words for t in col_tokens if len(t) > 2):
            matches.append(col)
            continue
        if normalize_word(col_lower) in q_words:
            matches.append(col)

    return matches


class HeuristicMockProvider(LLMProvider):
    """
    Offline heuristic rule-based planner.
    Enables instant zero-dependency testing and evaluation of standard analytics queries
    without needing an external API key.
    """

    def generate_plan(self, question: str, profile: DatasetProfile) -> AnalysisPlan:
        q_lower = question.lower().strip()
        cols_lower_map = {c.lower(): c for c in profile.columns}

        # 1. Check for correlation questions
        if any(term in q_lower for term in ["associated", "correlated", "correlation", "relationship between"]):
            matched_nums = find_matching_columns(profile.numeric_columns, question)
            if len(matched_nums) >= 2:
                col1, col2 = matched_nums[0], matched_nums[1]
                return AnalysisPlan(
                    operation="correlation",
                    columns=[col1, col2],
                    chart=ChartSpec(
                        needed=True,
                        chart_type="scatter",
                        x=col1,
                        y=col2,
                        title=f"{col1} vs {col2} Association",
                    ),
                    explanation=f"Calculated Pearson correlation between '{col1}' and '{col2}'. Note: correlation evaluates linear association and does not imply causation.",
                )
            elif len(profile.numeric_columns) >= 2:
                col1, col2 = profile.numeric_columns[0], profile.numeric_columns[1]
                return AnalysisPlan(
                    operation="correlation",
                    columns=[col1, col2],
                    chart=ChartSpec(
                        needed=True,
                        chart_type="scatter",
                        x=col1,
                        y=col2,
                        title=f"{col1} vs {col2} Association",
                    ),
                    explanation=f"Calculated correlation between '{col1}' and '{col2}'. Note: correlation does not imply causation.",
                )

        # 2. Check for Top / Highest / Maximum queries
        is_top = any(term in q_lower for term in ["highest", "top", "most", "maximum", "best", "greatest"])
        is_bottom = any(term in q_lower for term in ["lowest", "bottom", "least", "minimum", "worst"])

        # Extract limit
        limit = None
        num_match = re.search(r"\b(top|bottom)\s+(\d+)\b", q_lower)
        word_num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10}
        if num_match:
            limit = int(num_match.group(2))
        else:
            for word, val in word_num_map.items():
                if f"top {word}" in q_lower or f"bottom {word}" in q_lower:
                    limit = val
                    break
        if limit is None and (is_top or is_bottom):
            if "which " in q_lower or "what " in q_lower:
                limit = 1 if ("highest" in q_lower or "lowest" in q_lower) else 5

        # Detect columns mentioned
        mentioned_cat = find_matching_columns(profile.categorical_columns, question)
        metric_col = None
        agg_func = "sum"
        alias = None

        if "revenue" in q_lower or "sales" in q_lower:
            for cand in ["sales", "revenue", "amount", "total"]:
                if cand in cols_lower_map:
                    metric_col = cols_lower_map[cand]
                    break
        elif "profit" in q_lower:
            for cand in ["profit", "net_profit", "earnings"]:
                if cand in cols_lower_map:
                    metric_col = cols_lower_map[cand]
                    break
        elif "discount" in q_lower:
            for cand in ["discount", "discounts"]:
                if cand in cols_lower_map:
                    metric_col = cols_lower_map[cand]
                    break
        elif "count" in q_lower or "order count" in q_lower or "orders" in q_lower or "number of" in q_lower:
            agg_func = "count"
            alias = "order_count"
            # Prefer id column or first column
            id_cols = [c for c in profile.columns if "id" in c.lower()]
            metric_col = id_cols[0] if id_cols else profile.columns[0]

        # If not found by keywords, search exact numeric columns
        if not metric_col:
            for c in profile.numeric_columns:
                if c.lower() in q_lower:
                    metric_col = c
                    break

        # Check for average / mean
        if any(term in q_lower for term in ["average", "avg", "mean"]):
            agg_func = "mean"
        elif any(term in q_lower for term in ["median"]):
            agg_func = "median"

        # Check for time-based / monthly questions: "Show monthly sales for each region"
        if ("monthly" in q_lower or "by month" in q_lower) and profile.datetime_columns:
            date_col = profile.datetime_columns[0]
            region_col = mentioned_cat[0] if mentioned_cat else (profile.categorical_columns[0] if profile.categorical_columns else None)
            target_metric = metric_col or (profile.numeric_columns[0] if profile.numeric_columns else None)
            if target_metric:
                group_cols = [date_col]
                if region_col and region_col != date_col:
                    group_cols.append(region_col)
                return AnalysisPlan(
                    operation="aggregate",
                    columns=group_cols + [target_metric],
                    group_by=group_cols,
                    aggregations=[Aggregation(column=target_metric, func=agg_func)],
                    sort_by=[SortOrder(column=date_col, direction="asc")],
                    chart=ChartSpec(
                        needed=True,
                        chart_type="line",
                        x=date_col,
                        y=target_metric,
                        color=region_col if region_col else None,
                        title=f"Monthly {target_metric} by {region_col or 'Date'}",
                    ),
                    explanation=f"Grouped dataset by month from '{date_col}' and aggregated '{target_metric}' ({agg_func}).",
                )

        # Handle Top / Bottom by Group
        candidate_cats = [
            c for c in mentioned_cat 
            if c != metric_col and not c.lower().endswith("_id") and "date" not in c.lower()
        ]
        if not candidate_cats:
            candidate_cats = [c for c in mentioned_cat if c != metric_col and not c.lower().endswith("_id")]
        if not candidate_cats:
            candidate_cats = [c for c in mentioned_cat if c != metric_col]
        if not candidate_cats:
            candidate_cats = mentioned_cat

        # Check if query specifically targets an entity word right after top/bottom (e.g. "top five categories")
        target_entity_match = re.search(r"\b(?:top|bottom|highest|lowest)\s+(?:\w+\s+)?([a-z_]+)", q_lower)
        if target_entity_match:
            entity_word = normalize_word(target_entity_match.group(1))
            for cat in candidate_cats:
                if normalize_word(cat) == entity_word or entity_word in cat.lower():
                    candidate_cats.remove(cat)
                    candidate_cats.insert(0, cat)
                    break

        if (is_top or is_bottom) and candidate_cats:
            group_col = candidate_cats[0]
            target_metric = metric_col or (profile.numeric_columns[0] if profile.numeric_columns else profile.columns[0])
            sort_dir = "desc" if is_top else "asc"
            effective_limit = limit or 5
            agg_entry = Aggregation(column=target_metric, func=agg_func, alias=alias)
            sort_target = alias or target_metric
            return AnalysisPlan(
                operation="aggregate",
                columns=[group_col, target_metric],
                group_by=[group_col],
                aggregations=[agg_entry],
                sort_by=[SortOrder(column=sort_target, direction=sort_dir)],
                limit=effective_limit,
                chart=ChartSpec(
                    needed=True,
                    chart_type="bar",
                    x=group_col,
                    y=sort_target,
                    title=f"Top {effective_limit} {group_col} by {sort_target} ({agg_func})",
                ),
                explanation=f"Grouped by '{group_col}', aggregated '{target_metric}' using {agg_func}, and selected {sort_dir} top {effective_limit} records.",
            )

        # Handle simple group by aggregation: "sales by region", "orders by category"
        if mentioned_cat and metric_col:
            group_col = mentioned_cat[0]
            return AnalysisPlan(
                operation="aggregate",
                columns=[group_col, metric_col],
                group_by=[group_col],
                aggregations=[Aggregation(column=metric_col, func=agg_func)],
                sort_by=[SortOrder(column=metric_col, direction="desc")],
                chart=ChartSpec(
                    needed=True,
                    chart_type="bar",
                    x=group_col,
                    y=metric_col,
                    title=f"{metric_col} by {group_col}",
                ),
                explanation=f"Grouped by '{group_col}' and calculated {agg_func} of '{metric_col}'.",
            )

        # Handle value counts: "distribution of category", "how many per region"
        if mentioned_cat and any(t in q_lower for t in ["distribution", "breakdown", "count", "how many"]):
            group_col = mentioned_cat[0]
            return AnalysisPlan(
                operation="value_counts",
                columns=[group_col],
                sort_by=[SortOrder(column=group_col, direction="desc")],
                chart=ChartSpec(
                    needed=True,
                    chart_type="bar",
                    x=group_col,
                    y="count",
                    title=f"Distribution of {group_col}",
                ),
                explanation=f"Calculated frequency distribution for '{group_col}'.",
            )

        # If question asks for overall summary / count / mean of a numeric column
        if metric_col:
            return AnalysisPlan(
                operation="summary",
                columns=[metric_col],
                aggregations=[Aggregation(column=metric_col, func=agg_func)],
                explanation=f"Calculated overall {agg_func} for '{metric_col}'.",
            )

        # If question mentions unknown concept or unsupported request
        return AnalysisPlan(
            operation="unsupported",
            explanation="The question could not be mapped to available columns or supported operations.",
            unsupported_reason=(
                f"Could not identify relevant columns in the dataset for query: '{question}'. "
                f"Available columns are: {', '.join(profile.columns)}."
            ),
            follow_up_suggestion="Try asking about specific columns like: " + ", ".join(profile.columns[:4]),
        )


class GeminiProvider(LLMProvider):
    """Integrates Google Gemini models using direct HTTP API."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate_plan(self, question: str, profile: DatasetProfile) -> AnalysisPlan:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        schema_text = format_schema_for_llm(profile)
        user_prompt = (
            f"{schema_text}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"Respond with a single JSON object matching the AnalysisPlan schema."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": PLAN_SYSTEM_PROMPT},
                        {"text": user_prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = extract_json_from_text(text)
                return AnalysisPlan.model_validate_json(clean_json)
        except Exception as e:
            # Fallback to HeuristicMockProvider if API call fails
            mock_plan = HeuristicMockProvider().generate_plan(question, profile)
            mock_plan.explanation += f" (Note: LLM provider encountered error: {str(e)[:80]}. Generated plan via fallback heuristics.)"
            return mock_plan


class OpenAIProvider(LLMProvider):
    """Integrates OpenAI or OpenAI-compatible endpoints."""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self.model = model

    def generate_plan(self, question: str, profile: DatasetProfile) -> AnalysisPlan:
        url = f"{self.base_url}/chat/completions"
        schema_text = format_schema_for_llm(profile)
        user_prompt = f"{schema_text}\n\nUSER QUESTION: {question}\n\nReturn JSON matching AnalysisPlan schema."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                content = res.json()["choices"][0]["message"]["content"]
                clean_json = extract_json_from_text(content)
                return AnalysisPlan.model_validate_json(clean_json)
        except Exception as e:
            mock_plan = HeuristicMockProvider().generate_plan(question, profile)
            mock_plan.explanation += f" (Note: OpenAI provider error: {str(e)[:80]}. Fallback heuristics used.)"
            return mock_plan


class AnthropicProvider(LLMProvider):
    """Integrates Anthropic Claude models."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model

    def generate_plan(self, question: str, profile: DatasetProfile) -> AnalysisPlan:
        url = "https://api.anthropic.com/v1/messages"
        schema_text = format_schema_for_llm(profile)
        user_prompt = f"{schema_text}\n\nUSER QUESTION: {question}\n\nReturn ONLY a JSON object matching AnalysisPlan."

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "system": PLAN_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 1500,
            "temperature": 0.1,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                text = res.json()["content"][0]["text"]
                clean_json = extract_json_from_text(text)
                return AnalysisPlan.model_validate_json(clean_json)
        except Exception as e:
            mock_plan = HeuristicMockProvider().generate_plan(question, profile)
            mock_plan.explanation += f" (Note: Anthropic provider error: {str(e)[:80]}. Fallback heuristics used.)"
            return mock_plan


def extract_json_from_text(text: str) -> str:
    """Extracts JSON substring safely from raw model text."""
    text = text.strip()
    # Remove markdown code block fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text


def get_llm_provider() -> Tuple[LLMProvider, str]:
    """
    Factory to select the active LLM provider based on environment variables.
    Returns: (provider_instance, provider_name_display)
    """
    selected = os.environ.get("LLM_PROVIDER", "").lower().strip()

    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    if selected == "gemini" and gemini_key:
        return GeminiProvider(gemini_key), "Google Gemini"
    if selected == "openai" and openai_key:
        return OpenAIProvider(openai_key, base_url=os.environ.get("OPENAI_BASE_URL")), "OpenAI"
    if selected == "anthropic" and anthropic_key:
        return AnthropicProvider(anthropic_key), "Anthropic Claude"
    if selected == "mock":
        return HeuristicMockProvider(), "Offline Heuristic Engine"

    # Auto-detect if not explicitly selected
    if gemini_key:
        return GeminiProvider(gemini_key), "Google Gemini"
    if openai_key:
        return OpenAIProvider(openai_key, base_url=os.environ.get("OPENAI_BASE_URL")), "OpenAI"
    if anthropic_key:
        return AnthropicProvider(anthropic_key), "Anthropic Claude"

    return HeuristicMockProvider(), "Offline Heuristic Engine (No API key set)"
