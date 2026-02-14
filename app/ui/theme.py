from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

          :root {
            --bg-main: #f3f8f2;
            --bg-panel: #ffffff;
            --text-main: #122019;
            --text-soft: #4a6153;
            --accent: #1db954;
            --accent-2: #0f8f40;
            --ring: rgba(29, 185, 84, 0.25);
            --card-shadow: 0 8px 24px rgba(20, 42, 28, 0.09);
          }

          .stApp {
            font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
            color: var(--text-main);
            background:
              radial-gradient(1200px 500px at 100% -10%, rgba(29, 185, 84, 0.12), transparent 45%),
              radial-gradient(1000px 500px at -15% 10%, rgba(33, 150, 83, 0.08), transparent 50%),
              var(--bg-main);
          }

          h1, h2, h3 {
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
            letter-spacing: -0.01em;
          }

          [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f1f19 0%, #152921 100%);
          }

          [data-testid="stSidebar"] * {
            color: #eef7f1;
          }

          .brand-block {
            padding: 0.85rem 1rem;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(29, 185, 84, 0.28), rgba(16, 80, 42, 0.32));
            border: 1px solid rgba(188, 248, 206, 0.2);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
            margin-bottom: 0.7rem;
          }

          .brand-kicker {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            opacity: 0.82;
          }

          .brand-title {
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
            font-size: 1.14rem;
            font-weight: 700;
            margin-top: 0.1rem;
          }

          .brand-sub {
            opacity: 0.88;
            margin-top: 0.2rem;
            font-size: 0.88rem;
          }

          [data-testid="stMetric"] {
            background: var(--bg-panel);
            border: 1px solid #dbe9dc;
            border-radius: 14px;
            padding: 0.75rem 0.9rem;
            box-shadow: var(--card-shadow);
          }

          .stButton button {
            border-radius: 11px;
            border: 1px solid #c9decb;
            box-shadow: 0 1px 2px rgba(20, 42, 28, 0.1);
            transition: all 120ms ease-in-out;
          }

          .stButton button:hover {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--ring);
          }

          .stDownloadButton button,
          .stLinkButton a {
            border-radius: 11px !important;
          }

          .stTabs [role="tab"] {
            border-radius: 10px 10px 0 0;
          }

          [data-testid="stDataFrame"] {
            border: 1px solid #dbe9dc;
            border-radius: 12px;
            overflow: hidden;
          }

          @media (max-width: 900px) {
            .brand-title {
              font-size: 1.02rem;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
