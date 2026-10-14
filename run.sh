#!/usr/bin/env bash
set -e

# Move to the script's directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

# Activate the project virtual environment
source .venv/bin/activate

# Launch Streamlit and open the browser automatically
echo "Starting Natural-Language Data Analyst..."
streamlit run app.py
