# 📊 Natural-Language Data Analyst

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/frontend-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/charts-Plotly-3F4F75.svg)](https://plotly.com/)
[![Pydantic v2](https://img.shields.io/badge/validation-Pydantic%20v2-e92063.svg)](https://docs.pydantic.dev/)
[![Tests Passing](https://img.shields.io/badge/tests-30%20passed-success.svg)](https://github.com/ashishh9090)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Ask analytical questions about your CSV in plain English.**  
> Get mathematically verified answers, interactive Plotly visualizations, transparent audit trails, and zero code-execution risk.

---

## 🎬 Live Demo & Video Walkthrough

Watch the Natural-Language Data Analyst in action below:

<p align="center">
  <video src="NLDA.DEMO.mp4" controls="controls" muted="muted" style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    Your browser does not support the video tag.
  </video>
</p>

> 📹 **High-Definition Demo Video:**  
> **[▶️ Click here to watch / download the demo video (`NLDA.DEMO.mp4`)](https://github.com/ashishh9090/natural-language-data-analyst/raw/main/NLDA.DEMO.mp4)**

### What you see in the demo:
1. **Welcoming Exploration Workspace:** Starting with a clean empty state, quick-start sample datasets, and clear privacy disclosures.
2. **Instant Dataset Profiling:** Uploading/selecting a dataset inspects row counts, column types, missing value percentages, and preview records in local memory.
3. **Plain-English Questions:** Asking *"Which product had the highest revenue?"*, *"Show monthly sales for each region"*, and *"Are higher discounts associated with lower profit?"*.
4. **Verified Answers & Interactive Charts:** Direct computed answers, responsive Plotly charts with on-the-fly chart type switching (Bar, Line, Scatter, Pie), and transparent *"How this was calculated"* cards with statistical honesty notes.

---

## 💡 Why We Built This (The Real Problem with AI Data Analysts)

Most existing "chat with your data" tools suffer from two dangerous flaws:

1. **The Code-Execution Trap (`eval()` / `exec()`):**  
   Many tools ask an LLM to generate Python or SQL code and blindly execute it on your computer or database. This is a massive security hazard. Malformed questions or adversarial CSV contents can result in arbitrary code execution, disk corruption, or database leaks.
2. **The Hallucination Trap & Arithmetic Blindness:**  
   Language models are language engines, not calculators. When an LLM tries to compute totals, medians, or correlations in its head, it frequently hallucinates numbers, drops outliers, or invents convincing trends that don't exist.
3. **Data Privacy Violations:**  
   Sending entire rows of sensitive financial records or customer PII to external APIs is unacceptable for most teams and privacy regulations.

### 🛡️ How Natural-Language Data Analyst Solves This

This project uses a **strict separation of Planning and Execution**:

- **The LLM is only an Intent Translator:** It reads your question and a compact summary of the table schema (column names and data types)—**never raw table rows**. It produces a strictly validated Pydantic `AnalysisPlan`.
- **The Execution Engine is 100% Deterministic:** Plans execute through an **explicit allowlist of Pandas operations**. There is zero arbitrary code execution, zero `eval()`, zero `exec()`, and zero raw SQL.
- **Answers are Calculated, Not Guessed:** Answers and charts are derived directly from the computed output of the data engine.
- **Statistical Integrity:** If you ask about correlations, the app automatically flags that **correlation does not imply causation** and highlights missing-data omissions.

---

## ✨ Key Features

| Feature | What It Does | Why It Matters |
| :--- | :--- | :--- |
| 💬 **Natural-Language Querying** | Translates questions like *"Top 5 categories by sales"* into structured analysis. | Accessible to non-technical stakeholders, product managers, and executives. |
| 🔒 **Air-Gapped Privacy** | Raw table rows never leave your computer. Only schema column profiles are sent. | Safe for confidential corporate data and customer records. |
| 🛡️ **100% Safe Execution** | Only documented operations allowed: `sum`, `mean`, `median`, `min`, `max`, `count`, `value_counts`, `filter`, `group_by`, `correlation`. | Zero arbitrary script execution or code injection vulnerabilities. |
| 📊 **Interactive Visualizations** | Plotly charts generated automatically with an instant **Chart-Type Switcher** (Bar, Line, Scatter, Pie, Box, Histogram). | Switch visual representations on the fly without losing answers. |
| 🔍 **Plain-English Audit Trail** | Every answer includes an expandable *"How your question was understood"* panel. | Eliminates black-box confusion; verify the math behind every number. |
| ⚖️ **Honest Statistics** | Automatically warns about correlation vs. causation, empty subsets, and missing values. | Prevents misleading business decisions based on flawed interpretations. |
| ⚡ **Built-In Offline Engine** | Comes with a rule-based heuristic planner that runs with **zero API keys**. | Works out of the box offline or connects to Gemini, OpenAI, or Claude. |
| 📁 **Included Sample Datasets** | Pre-loaded with **E-Commerce Orders** and **SaaS Customer Metrics**. | Instant testing without having to hunt for sample CSV files. |

---

## 🏛️ Architecture & Data Flow

```
                           ┌─────────────────────────────────────────┐
                           │            User Uploads CSV             │
                           └────────────────────┬────────────────────┘
                                                │ Local Inspection & Profiling
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │      Compact Schema Profile             │
                           │  - Column names & inferred types        │
                           │  - Missing value counts & memory        │
                           │  - 2-3 bounded string formats           │
                           │  (ZERO raw data rows sent to LLM!)      │
                           └────────────────────┬────────────────────┘
                                                │
   User Plain-English Question ─────────────────┼────────────────────────┐
                                                ▼                        │
                           ┌─────────────────────────────────────────┐   │
                           │       Replaceable Planner Engine        │   │
                           │   (Built-in Heuristic / Gemini /        │   │
                           │    OpenAI / Claude)                     │   │
                           └────────────────────┬────────────────────┘   │
                                                │                        │
                                                ▼                        │
                           ┌─────────────────────────────────────────┐   │
                           │       Pydantic AnalysisPlan (JSON)      │   │
                           │   Operation, columns, filters, grouping,│   │
                           │   aggregations, sorting, chart spec     │   │
                           └────────────────────┬────────────────────┘   │
                                                │                        │
                                                ▼ Strict Schema Check    │
                           ┌─────────────────────────────────────────┐   │
                           │       Pandas Allowlist Executor         │   │
                           │   - Runs only verified Pandas routines  │   │
                           │   - Computes exact numbers & records    │   │
                           │   - Handles NaNs & zero-variance safely │   │
                           └────────────────────┬────────────────────┘   │
                                                │                        │
                                                ▼                        │
 ┌───────────────────────────────────────────────────────────────────────┴──────────┐
 │                          Polished Streamlit Workspace                            │
 │  1. ⚡ Direct Computed Answer Card                                               │
 │  2. 📊 Interactive Plotly Visualization (with Bar / Line / Pie / Scatter switch)  │
 │  3. 🔍 Interpreted Plan Panel (Allowlist Verified ✅)                             │
 │  4. 📖 Method & Data Health Notes (Correlation caveats & missing data flags)     │
 │  5. 📋 Downloadable Result Records (CSV Export)                                  │
 └──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
nl-data-analyst/
├── app.py                          # Streamlit application workspace
├── run.sh                          # 1-click launch script
├── pyproject.toml                  # Project packaging and test configuration
├── requirements.txt                # Production dependencies
├── .env.example                    # API key template (optional)
├── NLDA.DEMO.mp4                   # High-definition video walkthrough
├── record_demo_linkedin.py         # Automated recording script
├── sample_data/
│   ├── ecommerce_orders.csv        # Realistic e-commerce sales dataset
│   └── saas_metrics.csv            # SaaS customer subscriptions & churn dataset
├── nl_data_analyst/
│   ├── __init__.py                 # Core package init
│   ├── models.py                   # Pydantic schemas (AnalysisPlan, DatasetProfile, ExecutionResult)
│   ├── data.py                     # Safe CSV loader, size guard (100MB), schema profiler
│   ├── planner.py                  # Schema validation, question suggester, plan explainer
│   ├── executor.py                 # Deterministic Pandas allowlist execution engine
│   ├── charts.py                   # Plotly chart generator & dynamic chart switcher
│   ├── llm.py                      # Multi-provider LLM interface (Offline, Gemini, OpenAI, Claude)
│   └── ui/                         # Modular, accessible UI components
│       ├── __init__.py             # UI module export
│       ├── styles.py               # Modern analytics CSS tokens & responsive styles
│       ├── header.py               # Header with active dataset status indicator
│       ├── empty_state.py          # Welcoming empty state & sample data pickers
│       ├── dataset_view.py         # Dimensions, health metrics, and 5-row preview
│       ├── ask_bar.py              # Prominent input with dynamic suggestion chips
│       ├── results_view.py         # Answers, charts, plan expander, and CSV download
│       └── sidebar.py              # Model provider settings & safety audit panel
└── tests/
    ├── test_data.py                # File size limits, empty files, profiling tests
    ├── test_planner.py             # Schema verification & heuristic planner tests
    ├── test_executor.py            # Safe Pandas execution & statistical caveat tests
    ├── test_charts.py              # Chart generator & chart switcher tests
    ├── test_ui_components.py       # UI component function tests
    └── test_e2e_examples.py        # End-to-end evaluation on standard analytical queries
```

---

## 🚀 Quick Start Guide (Ready in 2 Minutes)

### 1. Clone the Repository
```bash
git clone https://github.com/ashishh9090/natural-language-data-analyst.git
cd natural-language-data-analyst
```

### 2. Set Up Virtual Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. *(Optional)* Add LLM API Keys
The application works **completely offline out of the box** using its built-in rule-based planning engine!

If you want to power it with a frontier LLM:
```bash
cp .env.example .env
```
Open `.env` and add your preferred provider key:
```env
# Choose any of the following:
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 4. Launch the App
You can use the convenient 1-click startup script:
```bash
./run.sh
```
Or run directly with Streamlit:
```bash
source .venv/bin/activate
streamlit run app.py
```
Your browser will open automatically at **`http://localhost:8501`**!

---

## 💬 Example Questions to Try

### On E-Commerce Data (`ecommerce_orders.csv`):
- *"Which product had the highest revenue?"*  
  ➡️ **Result:** UltraSharp 4K Monitor ($4,499.91 across 4 orders)
- *"Show monthly sales for each region"*  
  ➡️ **Result:** Interactive grouped bar / line chart by month and region
- *"Are higher discounts associated with lower profit?"*  
  ➡️ **Result:** Pearson r calculation with an explicit disclaimer that *correlation does not imply causation*
- *"What are the top five categories by order count?"*  
  ➡️ **Result:** Value counts breakdown for categories

### On SaaS Metrics Data (`saas_metrics.csv`):
- *"What is the average satisfaction score by plan tier?"*  
  ➡️ **Result:** Enterprise: 8.97, Professional: 7.85, Starter: 5.75
- *"Is usage hours correlated with customer satisfaction?"*  
  ➡️ **Result:** Strong positive correlation (r ≈ 0.88) with scatter trendline
- *"How many customers churned per plan?"*  
  ➡️ **Result:** Churn counts segmented by plan tier

---

## 🧪 Automated Testing & Verification

The project includes an extensive automated test suite with **30 unit and end-to-end tests**:

```bash
source .venv/bin/activate
pytest -v
```

### Test Coverage Highlights:
- **Security & Upload Protection:** Rejection of non-CSV files, malformed headers, and files exceeding the 100MB limit.
- **Strict Schema Enforcement:** Verification that queries referencing non-existent columns are gracefully caught before execution.
- **Allowlist Execution:** Unit tests validating that aggregations (`sum`, `mean`, `median`, `min`, `max`), grouping, filtering, and value counts run cleanly.
- **Statistical Honesty:** Verification that correlation routines attach the non-causation caveat and handle zero-variance columns without crashing.
- **Dynamic Visualizations:** Testing chart creation and fallback logic across Bar, Line, Scatter, and Pie modes.
- **End-to-End Consistency:** Validating that direct computed answers match ground truth mathematical results.

---

## 🤝 Contributing

Contributions, feature suggestions, and feedback are always welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ for transparent, safe, and accessible data exploration.
</p>
