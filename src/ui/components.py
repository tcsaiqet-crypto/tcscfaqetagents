"""Reusable Enterprise UI Components for QET Agent Accelerator."""

import html
import streamlit as st
from typing import Optional, List, Dict, Any
from urllib.parse import quote


def render_header(run_id: str, current_status: str = "Idle") -> None:
    """Header bar with fixed project context, Run ID, and status badge."""
    status_cls = current_status.lower().replace(" ", "-")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 16px;">
                <span style="font-size: 1.5rem; font-weight: 800; color: #163B65;">⚡ QET Agent Accelerator</span>
                <span style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #2563EB; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                    Project: CFA Digital Journey ▼
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div style="text-align: right; font-size: 0.85rem; color: #64748B;">
                <div><b>Run ID:</b> <code>{run_id}</code></div>
                <div><b>Status:</b> <span class="badge badge-{status_cls}">{current_status}</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("---")


def render_stepper(active_stage: str, stage_statuses: Dict[str, str]) -> None:
    """
    Persistent Workflow Stepper:
    Sources ➔ Understanding ➔ Test Cases ➔ Test Data ➔ Playwright ➔ Execution ➔ Report
    """
    stages = [
        ("Sources", "Intake & Inventory"),
        ("Understanding", "App Analysis"),
        ("Test Cases", "Scenario Generation"),
        ("Test Data", "Synthetic Datasets"),
        ("Playwright", "POM Automation"),
        ("Execution", "Controlled UI Test"),
        ("Report", "Quality Summary")
    ]

    cols = st.columns(len(stages))
    for idx, (stage_key, label) in enumerate(stages):
        status = stage_statuses.get(stage_key, "Not Started")
        is_active = (stage_key == active_stage)

        # Style resolution
        if is_active:
            border_style = "2px solid #2563EB"
            bg_color = "#EFF6FF"
            text_color = "#163B65"
        elif status == "Completed":
            border_style = "1px solid #86EFAC"
            bg_color = "#F0FDF4"
            text_color = "#16803C"
        elif status == "Failed":
            border_style = "1px solid #FCA5A5"
            bg_color = "#FEF2F2"
            text_color = "#C53030"
        elif status in ["Not Configured", "Disabled"]:
            border_style = "1px dashed #CBD5E1"
            bg_color = "#F8FAFC"
            text_color = "#94A3B8"
        else:
            border_style = "1px solid #E2E8F0"
            bg_color = "#FFFFFF"
            text_color = "#64748B"

        badge_cls = f"badge-{status.lower().replace(' ', '-')}"

        with cols[idx]:
            st.markdown(
                f"""
                <div style="background: {bg_color}; border: {border_style}; border-radius: 8px; padding: 8px; text-align: center; font-size: 0.75rem;">
                    <div style="font-weight: 700; color: {text_color}; font-size: 0.8rem;">{stage_key}</div>
                    <div style="color: #64748B; font-size: 0.7rem; margin-bottom: 4px;">{label}</div>
                    <span class="badge {badge_cls}">{status}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown("<br>", unsafe_allow_html=True)


def render_top_navigation(nav_options: List[str], nav_labels: Dict[str, str], active_nav: str) -> None:
    """Render premium horizontal top navigation using stable CSS classes and query-param links."""
    nav_items: List[str] = []
    for option in nav_options:
        label = html.escape(nav_labels.get(option, option))
        value = quote(option)
        active_cls = " active" if option == active_nav else ""
        nav_items.append(
            f'<a class="qet-nav-item{active_cls}" href="?nav={value}">{label}</a>'
        )

    st.markdown(
        f"""
        <nav class="qet-nav-rail" aria-label="Primary Navigation">
            {''.join(nav_items)}
        </nav>
        """,
        unsafe_allow_html=True,
    )


def render_left_navigation(
    nav_groups: List[Dict[str, Any]],
    nav_labels: Dict[str, str],
    active_nav: str,
    run_id: str,
    completed_count: int,
    total_count: int,
) -> None:
    """Render grouped left navigation rail in the sidebar using query-param links."""
    st.sidebar.markdown("<div class='qet-side-shell'>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='qet-side-app'>QET Agent Accelerator</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='qet-side-project'>CFA Journey</div>", unsafe_allow_html=True)
    st.sidebar.markdown(
        f"""
        <div class='qet-run-card'>
            <div class='qet-run-card-title'>Run</div>
            <div class='qet-run-card-id'>{html.escape(run_id)}</div>
            <div class='qet-run-card-meta'>Workflow Completion: {completed_count}/{total_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for group in nav_groups:
        group_label = html.escape(group["label"])
        st.sidebar.markdown(
            f"<div class='qet-nav-group-label'>{group_label}</div>",
            unsafe_allow_html=True,
        )

        nav_items: List[str] = []
        for option in group["items"]:
            label = html.escape(nav_labels.get(option, option))
            value = quote(option)
            active_cls = " active" if option == active_nav else ""
            nav_items.append(
                f'<a class="qet-nav-item-vertical{active_cls}" href="?nav={value}">{label}</a>'
            )

        st.sidebar.markdown(
            f"<nav class='qet-nav-vertical'>{''.join(nav_items)}</nav>",
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("</div>", unsafe_allow_html=True)


def render_ai_status_footer(runtime: Dict[str, Any]) -> None:
    """Render compact AI provider and state footer."""
    state = html.escape(str(runtime.get("state", "Unknown")).upper())
    provider = html.escape(str(runtime.get("provider", "unknown")).upper())
    badge_cls = "badge-completed" if state == "READY" else ("badge-disabled" if state == "DISABLED" else "badge-requires-review")
    st.markdown(
        f"""
        <div class='qet-ai-footer'>
            <span><b>AI</b> {provider}</span>
            <span class='badge {badge_cls}'>{state}</span>
            <span class='qet-ai-footer-path'>keys/gemini keys.txt | keys/openai keys.txt</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status: str) -> str:
    """Format status string into HTML badge."""
    cls = status.lower().replace(" ", "-")
    return f'<span class="badge badge-{cls}">{status}</span>'


def render_evidence_badge(evidence_type: str) -> str:
    """Format evidence source into HTML badge."""
    return f'<span class="badge-evidence">Evidence: {evidence_type}</span>'


def render_confidence_badge(confidence: str) -> str:
    """Format confidence level into HTML badge."""
    c_lower = confidence.lower()
    return f'<span class="badge-conf-{c_lower}">Confidence: {confidence.capitalize()}</span>'


def render_provenance_panel(
    model_name: str = "gemini-3.6-flash",
    source: str = "Extracted CFA Source Inventory & Requirement Docs",
    timestamp: str = "2026-08-13T14:30:00Z",
    confidence: str = "High"
) -> None:
    """AI Provenance & Disclaimer Footer Panel."""
    st.markdown(
        f"""
        <div class="provenance-panel">
            🤖 <b>AI Generation Provenance & Advisory Notice</b><br>
            • <b>Model:</b> <code>{model_name}</code> | • <b>Source:</b> {source} | • <b>Timestamp:</b> {timestamp} | • {render_confidence_badge(confidence)}<br>
            <i>Note: AI findings are recommendations backed by empirical source code evidence. Review critical findings prior to deployment.</i>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_capability_card(
    title: str,
    is_enabled: bool,
    description: str,
    version_tag: str = "Version 1"
) -> None:
    """Render capability status card for Settings and Dashboard."""
    if is_enabled:
        st.markdown(
            f"""
            <div class="qet-card" style="border-left: 4px solid #16803C;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1rem; color: #163B65;">✅ {title}</span>
                    <span class="badge badge-completed">ENABLED</span>
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-top: 6px;">{description}</div>
                <div style="font-size: 0.75rem; color: #16803C; margin-top: 4px; font-weight: 600;">{version_tag} Active</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div class="qet-card-disabled">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1rem; color: #94A3B8;">🚫 {title}</span>
                    <span class="badge badge-disabled">DISABLED</span>
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 6px;">{description}</div>
                <div style="font-size: 0.75rem; color: #C53030; margin-top: 4px; font-weight: 600;">Disabled in {version_tag} policy</div>
            </div>
            """,
            unsafe_allow_html=True
        )
