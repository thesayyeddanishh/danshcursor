"""Prev/Next page navigation for the Streamlit multi-page app."""
from __future__ import annotations

import streamlit as st

# Circular order: Home → Batters → Pacers → Spinners → Leaderboard → Home
_NAV = [
    ("home", "Home.py"),
    ("batters", "pages/01_Batters.py"),
    ("pacers", "pages/02_Pacers.py"),
    ("spinners", "pages/03_Spinners.py"),
    ("leaderboard", "pages/04_Leaderboard.py"),
]


def render_page_nav(page_id: str) -> None:
    page_id = (page_id or "home").lower().strip()
    idx = next((i for i, (pid, _) in enumerate(_NAV) if pid == page_id), 0)
    prev_path = _NAV[(idx - 1) % len(_NAV)][1]
    next_path = _NAV[(idx + 1) % len(_NAV)][1]
    c1, _mid, c3 = st.columns([0.4, 10, 0.4])
    with c1:
        if st.button("◀", key=f"nav_prev_{page_id}", help="Previous page"):
            st.switch_page(prev_path)
    with c3:
        if st.button("▶", key=f"nav_next_{page_id}", help="Next page"):
            st.switch_page(next_path)
