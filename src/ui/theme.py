"""Professional Light Enterprise Theme System for QET Agent Accelerator."""

import streamlit as st

# Color Palette Constants
PAGE_BG = "#F5F7FB"
CARD_BG = "#FFFFFF"
PRIMARY_NAVY = "#163B65"
PRIMARY_BLUE = "#2563EB"
SUCCESS_GREEN = "#16803C"
WARNING_AMBER = "#B7791F"
ERROR_RED = "#C53030"
NEUTRAL_SLATE = "#64748B"
BORDER_COLOR = "#E2E8F0"

CUSTOM_CSS = f"""
<style>
    /* Global App Container */
    .stApp {{
        background: {PAGE_BG} !important;
        font-family: 'Segoe UI', Tahoma, sans-serif !important;
        color: {PRIMARY_NAVY} !important;
    }}

    section[data-testid="stSidebar"] > div {{
        background: #163B65;
        color: #F8FAFC;
        padding-top: 12px;
    }}

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: #E2E8F0 !important;
    }}

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.35) !important;
        border-radius: 2px !important;
    }}
    
    /* Headings */
    h1, h2, h3, h4 {{
        color: {PRIMARY_NAVY} !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }}

    /* Card Containers */
    .qet-card {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 2px;
        padding: 20px;
        box-shadow: none;
        margin-bottom: 16px;
    }}

    .qet-card-disabled {{
        background-color: #F8FAFC;
        border: 1px dashed {BORDER_COLOR};
        border-radius: 2px;
        padding: 18px;
        opacity: 0.75;
        margin-bottom: 14px;
    }}

    /* Header Bar */
    .qet-header {{
        background-color: {CARD_BG};
        border-bottom: 1px solid {BORDER_COLOR};
        padding: 16px 24px;
        border-radius: 2px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    /* Stepper Container */
    .qet-stepper-container {{
        background-color: {CARD_BG};
        border: 1px solid {BORDER_COLOR};
        border-radius: 2px;
        padding: 14px 20px;
        margin-bottom: 24px;
    }}

    /* Status Badges */
    .badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 2px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    .badge-completed {{ background-color: #DCFCE7; color: {SUCCESS_GREEN}; border: 1px solid #86EFAC; }}
    .badge-running {{ background-color: #DBEAFE; color: {PRIMARY_BLUE}; border: 1px solid #93C5FD; }}
    .badge-requires-review {{ background-color: #FEF3C7; color: {WARNING_AMBER}; border: 1px solid #FCD34D; }}
    .badge-failed {{ background-color: #FEE2E2; color: {ERROR_RED}; border: 1px solid #FCA5A5; }}
    .badge-not-run {{ background-color: #F1F5F9; color: {NEUTRAL_SLATE}; border: 1px solid #CBD5E1; }}
    .badge-not-configured {{ background-color: #F1F5F9; color: {NEUTRAL_SLATE}; border: 1px solid #CBD5E1; }}
    .badge-disabled {{ background-color: #F1F5F9; color: #94A3B8; border: 1px solid #E2E8F0; }}
    .badge-approved {{ background-color: #DCFCE7; color: {SUCCESS_GREEN}; border: 1px solid #86EFAC; }}
    .badge-not-started {{ background-color: #F8FAFC; color: {NEUTRAL_SLATE}; border: 1px solid #E2E8F0; }}
    .badge-ready {{ background-color: #EFF6FF; color: {PRIMARY_BLUE}; border: 1px solid #BFDBFE; }}

    /* Evidence Badges */
    .badge-evidence {{
        background-color: #F1F5F9;
        color: {PRIMARY_NAVY};
        border: 1px solid #CBD5E1;
        padding: 2px 8px;
        border-radius: 2px;
        font-size: 0.75rem;
        font-weight: 500;
    }}

    /* Confidence Badges */
    .badge-conf-high {{ background-color: #DCFCE7; color: {SUCCESS_GREEN}; font-weight: 600; padding: 2px 8px; border-radius: 2px; font-size: 0.75rem; }}
    .badge-conf-medium {{ background-color: #FEF3C7; color: {WARNING_AMBER}; font-weight: 600; padding: 2px 8px; border-radius: 2px; font-size: 0.75rem; }}
    .badge-conf-low {{ background-color: #FEE2E2; color: {ERROR_RED}; font-weight: 600; padding: 2px 8px; border-radius: 2px; font-size: 0.75rem; }}

    /* AI Provenance Panel */
    .provenance-panel {{
        background-color: #F8FAFC;
        border: 1px solid {BORDER_COLOR};
        border-left: 4px solid {PRIMARY_BLUE};
        border-radius: 2px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: {NEUTRAL_SLATE};
        margin-top: 10px;
    }}

    .qet-hero {{
        background: #EFF6FF;
        color: #163B65;
        border: 1px solid #BFDBFE;
        border-radius: 2px;
        padding: 14px 18px;
        margin: 8px 0 18px 0;
        box-shadow: none;
        font-size: 0.95rem;
        letter-spacing: 0.01em;
    }}

    div.stButton > button {{
        border-radius: 2px !important;
        border: 1px solid #94B6E5 !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em;
    }}

    div.stButton > button[kind="primary"] {{
        background: #1D4E89 !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: none;
    }}

    .qet-side-shell {{
        margin-top: 8px;
    }}

    .qet-side-app {{
        color: #BFD2EA;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 4px;
        text-transform: lowercase;
        letter-spacing: 0.01em;
    }}

    .qet-side-project {{
        color: #F8FAFC;
        font-size: 1.55rem;
        font-weight: 800;
        margin-bottom: 14px;
        letter-spacing: -0.02em;
    }}

    .qet-run-card {{
        background: #1E3657;
        border: 1px solid #2F4C73;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 18px;
    }}

    .qet-run-card-title {{
        color: #A7C0DD;
        font-size: 0.74rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 2px;
    }}

    .qet-run-card-id {{
        color: #F5FAFF;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 4px;
        word-break: break-word;
    }}

    .qet-run-card-meta {{
        color: #BFD2EA;
        font-size: 0.78rem;
    }}

    .qet-nav-group-label {{
        color: #1FD4FF;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 14px 0 8px 0;
    }}

    .qet-nav-vertical {{
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-bottom: 2px;
    }}

    .qet-nav-item-vertical {{
        display: inline-flex;
        align-items: center;
        justify-content: flex-start;
        border: 1px solid #27456B;
        border-radius: 10px;
        background: #132744;
        color: #C8D5E7 !important;
        text-decoration: none !important;
        padding: 10px 12px;
        min-height: 38px;
        font-size: 1rem;
        font-weight: 600;
        white-space: nowrap;
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }}

    .qet-nav-item-vertical:hover {{
        border-color: #3A6397;
        background: #173053;
        color: #EAF7FF !important;
    }}

    .qet-nav-item-vertical:focus-visible {{
        outline: 2px solid #00D1FF;
        outline-offset: 2px;
    }}

    .qet-nav-item-vertical.active {{
        background: #0F324B;
        color: #EAF7FF !important;
        border-color: #00D1FF;
        box-shadow: inset 4px 0 0 #00D1FF;
    }}

    .qet-ai-footer {{
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        background: #0E1A2B;
        border-top: 1px solid #1E3657;
        color: #D9E7F5;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 10px;
        z-index: 999;
        font-size: 0.82rem;
    }}

    .qet-ai-footer .badge {{
        margin: 0;
    }}

    .qet-ai-footer-path {{
        opacity: 0.8;
        font-size: 0.78rem;
        margin-left: auto;
    }}

    div[data-testid="stHorizontalBlock"] > div:has(> div.stSelectbox),
    div[data-testid="stHorizontalBlock"] > div:has(> div.stButton) {{
        padding-top: 4px;
    }}
</style>
"""


def apply_theme() -> None:
    """Inject CSS tokens into Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
