# 📊 Natural-Language Data Analyst

A beginner-accessible, technically solid, and safe Natural-Language Data Analyst web application.

Users upload any CSV file, ask analytical questions in plain English, and receive:
1. **A direct, computed answer** derived strictly from data calculations.
2. **An interactive Plotly visualization** when visual presentation aids understanding.
3. **A transparent method explanation** highlighting the relevant columns and logic used.
4. **Clear error handling & guidance** when data cannot support an answer or when assumptions must be qualified.

---

## 🏛️ Architecture & Safety Guarantees

```
                   ┌───────────────────────────────┐
                   │          User CSV             │
                   └──────────────┬────────────────┘
                                  │ (Safe Inspection & Profiling)
                                  ▼
                   ┌───────────────────────────────┐
                   │ Compact Dataset Profile       │
                   │ (Columns, types, nulls,       │
                   │  2-3 bounded string samples)  │
                   └──────────────┬────────────────┘
                                  │
 User Question ───►  LLM / Heuristic Engine
                                  │
                                  ▼
                   ┌───────────────────────────────┐
                   │ Validated AnalysisPlan (JSON) │
                   │ (Operation, columns, filters, │
                   │  group_by, aggs, sort, chart) │
                   └──────────────┬────────────────┘
                                  │
                                  ▼ Strict Schema Validation
                   ┌───────────────────────────────┐
                   │   Allowlist Execution Engine  │
                   │  - Zero eval() / exec()       │
                   │  - Deterministic Pandas ops   │
                   │  - Causation ≠ Correlation    │
                   └──────────────┬────────────────┘
                                  │
                                  ▼
     ┌────────────────────────────────────────────────────────┐
     │ Streamlit Interface:                                   │
     │ 1. Direct answer card                                  │
     │ 2. Interactive Plotly chart                            │
     │ 3. Plain-English method & referenced columns           │
     │ 4. Data integrity & incomplete data notes              │
     └────────────────────────────────────────────────────────┘
```

### Safety & Correctness Principles:
- **Zero Arbitrary Execution:** Model output is strictly constrained to a Pydantic `AnalysisPlan`. The application **never executes arbitrary Python code, eval(), exec(), SQL, or shell commands**.
- **Data Privacy & Token Efficiency:** Raw dataset rows are **never** forwarded to external models. The LLM only sees a compact schema summary (column names, inferred types, null counts, and a bounded set of up to 3 sample string representations).
- **Allowlist Operations:** Only documented operations are permitted: `count`, `sum`, `mean`, `median`, `min`, `max`, `nunique`, `std`, `value_counts`, `sorting`, `filtering`, `grouping`, and `correlation`.
- **Statistical Integrity:** Correlation queries automatically include caveats stating that **correlation does not imply causation**.
- **Data Quality Transparency:** Calculations explicitly document any omitted missing values (`null` / `NaN`), empty results, or constant-variance columns.

---

## 📁 Project Structure

```
nl-data-analyst/
├── app.py                      # Streamlit UI & interactive dashboard
├── pyproject.toml              # Project metadata & pytest configuration
├── requirements.txt            # Core dependencies
├── .env.example                # Configuration template for API keys
├── sample_data/
│   └── ecommerce_orders.csv    # Sample e-commerce dataset for quick testing
├── nl_data_analyst/
│   ├── __init__.py             # Package init
│   ├── models.py               # Pydantic schemas (AnalysisPlan, DatasetProfile, ExecutionResult)
│   ├── data.py                 # Untrusted CSV ingestion, size check, safe profiling
│   ├── planner.py              # Plan validation, schema enforcement, plain-English translation
│   ├── executor.py             # Deterministic Pandas allowlist engine
│   ├── charts.py               # Responsive Plotly chart generator
│   └── llm.py                  # Pluggable LLM interface (Gemini, OpenAI, Anthropic, Mock)
└── tests/
    ├── test_data.py            # CSV security & profiling tests
    ├── test_planner.py         # Schema verification & validation tests
    ├── test_executor.py        # Safe execution & statistical caveat tests
    ├── test_charts.py          # Visualization tests
    └── test_e2e_examples.py    # End-to-end evaluation on standard questions
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or standard `venv` + `pip`

### 1. Clone & Set Up Virtual Environment

Using `uv`:
```bash
# In the project directory:
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

Or using standard `python3 -m venv`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)

The application includes an **Offline Heuristic Engine** out of the box so you can run and test queries immediately without any API keys or costs.

To connect to Google Gemini, OpenAI, or Anthropic, create a `.env` file from the template:
```bash
cp .env.example .env
```
Add your preferred key:
```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# OR OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# OR Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Run the Web Application

```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Running Unit & Integration Tests

The test suite validates schema enforcement, safe execution, missing-value handling, correlation caveats, and end-to-end questions.

```bash
# Run all tests
pytest -v
```

All 27 tests run in under 2 seconds.

---

## 💡 Example Questions

Using the built-in sample dataset (`sample_data/ecommerce_orders.csv`):

| Question | Interpretation | Output |
| :--- | :--- | :--- |
| **“Which product had the highest revenue?”** | Group by `product_name`, sum `sales`, sort desc, limit 1 | UltraSharp 4K Monitor ($3,999.92) + Bar chart |
| **“Show monthly sales for each region.”** | Group by `order_date` & `region`, sum `sales` | Time series breakdown + Line chart |
| **“Are higher discounts associated with lower profit?”** | Pearson correlation between `discount` and `profit` | Correlation coefficient, scatter plot + Causation warning |
| **“What are the top five categories by order count?”** | Group by `category`, count orders, sort desc, limit 5 | Category breakdown + Bar chart |

---

## ⚠️ Limitations & Boundary Conditions

1. **Format Scope:** Currently optimized for tabular CSV data. Multi-sheet Excel workbooks, nested JSON, and databases require flattening to CSV prior to upload.
2. **Tabular Modeling:** The planner performs single-table operations (grouping, filtering, ranking, aggregation, correlation). Multi-table SQL joins across multiple CSV files are not supported in this version.
3. **Linear Association:** Correlation queries evaluate Pearson linear correlation. Non-linear relationships or multi-factor regression models require dedicated statistical modeling.
4. **Token Limits:** Large datasets with more than 1,000 distinct columns will have column summaries truncated to preserve token efficiency.
