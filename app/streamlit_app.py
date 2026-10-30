"""
Optional Streamlit scaffold (kept for Docker experiments).

Sprint 5 primary UI is the Next.js app under web/ (Vercel).
See docs/sprint5_vercel.md.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Financial Market Data Lakehouse",
    page_icon="📈",
    layout="wide",
)

st.title("Financial Market Data Lakehouse")
st.info(
    "Primary dashboard is Next.js on Vercel (`web/`). "
    "This Streamlit file is an optional leftover scaffold."
)
st.markdown(
    """
    Run the real UI:

    ```text
    python scripts/build_gold_export.py
    cd web && npm run dev
    ```
    """
)
