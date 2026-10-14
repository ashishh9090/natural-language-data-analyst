"""
CSS design system and scoped styles for the Natural-Language Data Analyst workspace.
Adheres to modern analytics-dashboard guidelines with light background, dark readable text,
restrained color palette, and accessible contrast.
"""

import streamlit as st


def inject_custom_styles():
    """Injects scoped, modern CSS styles into the Streamlit application."""
    st.markdown(
        """
        <style>
        /* Import clean modern sans-serif font */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #0f172a;
        }

        code, pre {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Top Header Component */
        .workspace-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.25rem 0 1rem 0;
            margin-bottom: 1.25rem;
            border-bottom: 1px solid #e2e8f0;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header-title-group h1 {
            font-size: 1.75rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.025em;
            margin: 0;
            line-height: 1.2;
        }

        .header-title-group p {
            font-size: 0.95rem;
            color: #475569;
            margin: 0.25rem 0 0 0;
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.825rem;
            font-weight: 600;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .status-badge.active {
            background-color: #ecfdf5;
            color: #065f46;
            border-color: #a7f3d0;
        }

        .status-badge.inactive {
            background-color: #f1f5f9;
            color: #64748b;
            border-color: #cbd5e1;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-badge.active .status-dot {
            background-color: #10b981;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.25);
        }

        .status-badge.inactive .status-dot {
            background-color: #94a3b8;
        }

        /* Empty State Hero Card */
        .empty-hero-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 2.25rem;
            box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.04), 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            margin-bottom: 2rem;
        }

        .hero-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }

        .hero-desc {
            font-size: 1rem;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }

        .feature-item {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1rem;
        }

        .feature-item h4 {
            font-size: 0.95rem;
            font-weight: 700;
            color: #1e293b;
            margin: 0 0 0.35rem 0;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .feature-item p {
            font-size: 0.85rem;
            color: #64748b;
            margin: 0;
            line-height: 1.45;
        }

        .privacy-banner {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            font-size: 0.875rem;
            color: #1e40af;
            margin-top: 1.25rem;
        }

        /* Dataset Overview Cards */
        .metric-summary-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            text-align: left;
        }

        .metric-summary-card .label {
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #64748b;
            margin-bottom: 0.25rem;
        }

        .metric-summary-card .value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0f172a;
        }

        /* Results Display Cards */
        .answer-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #cbd5e1;
            border-left: 5px solid #4f46e5;
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            margin: 1.5rem 0 1.25rem 0;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }

        .answer-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
            color: #4f46e5;
            margin-bottom: 0.5rem;
        }

        .answer-text {
            font-size: 1.35rem;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.45;
        }

        .unsupported-card {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 5px solid #f59e0b;
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            margin: 1.5rem 0 1.25rem 0;
            color: #92400e;
        }

        .unsupported-card h4 {
            margin: 0 0 0.5rem 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: #92400e;
        }

        .unsupported-card p {
            margin: 0;
            font-size: 0.95rem;
            line-height: 1.5;
            color: #78350f;
        }

        .badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            font-size: 0.775rem;
            font-weight: 600;
            background-color: #e0e7ff;
            color: #3730a3;
            margin: 0.15rem 0.25rem 0.15rem 0;
            border: 1px solid #c7d2fe;
        }

        /* Question suggestion chips */
        .chip-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.75rem 0 1.25rem 0;
        }

        /* Chart control bar */
        .chart-control-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.5rem 0.85rem;
            margin-bottom: 0.75rem;
        }

        /* Accessible button states & reduced motion */
        button {
            transition: all 0.15s ease-in-out;
        }

        button:focus-visible {
            outline: 2px solid #4f46e5 !important;
            outline-offset: 2px !important;
        }

        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
