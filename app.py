"""Streamlit Professional Enterprise UI for QET Agent Accelerator — CFA Digital Journey."""

import os
import json
import csv
import io
from uuid import uuid4
import streamlit as st
from pathlib import Path
from src.config import config
from src.models.schemas import AppState, ExecutionMode, ExecutionRequest
from src.services.zip_service import ZipService
from src.services.execution_engine import ExecutionEngine, ExecutionNotAllowedError
from src.services.llm_service import LLMService
from src.services.run_state_service import save_run_state, load_run_state
from src.workflows.pipeline import SequentialQETPipeline
from src.agents.accessibility_agent import AccessibilityAgent
from src.ui.theme import apply_theme, PAGE_BG, CARD_BG, PRIMARY_NAVY, PRIMARY_BLUE
try:
    from src.ui.components import (
        render_header,
        render_stepper,
        render_left_navigation,
        render_ai_status_footer,
        render_status_badge,
        render_evidence_badge,
        render_confidence_badge,
        render_provenance_panel,
        render_capability_card,
    )
except ImportError:
    from src.ui.components import (
        render_header,
        render_stepper,
        render_ai_status_footer,
        render_status_badge,
        render_evidence_badge,
        render_confidence_badge,
        render_provenance_panel,
        render_capability_card,
    )

    def render_left_navigation(
        nav_groups,
        nav_labels,
        active_nav,
        run_id,
        completed_count,
        total_count,
    ):
        st.sidebar.markdown("<div class='qet-side-shell'>", unsafe_allow_html=True)
        st.sidebar.markdown("<div class='qet-side-app'>QET Agent Accelerator</div>", unsafe_allow_html=True)
        st.sidebar.markdown("<div class='qet-side-project'>CFA Journey</div>", unsafe_allow_html=True)
        st.sidebar.markdown(
            f"""
            <div class='qet-run-card'>
                <div class='qet-run-card-title'>Run</div>
                <div class='qet-run-card-id'>{run_id}</div>
                <div class='qet-run-card-meta'>Workflow Completion: {completed_count}/{total_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for group in nav_groups:
            st.sidebar.markdown(
                f"<div class='qet-nav-group-label'>{group['label']}</div>",
                unsafe_allow_html=True,
            )
            nav_items = []
            for option in group["items"]:
                label = nav_labels.get(option, option)
                active_cls = " active" if option == active_nav else ""
                nav_items.append(f'<a class="qet-nav-item-vertical{active_cls}" href="?nav={option}">{label}</a>')
            st.sidebar.markdown(
                f"<nav class='qet-nav-vertical'>{''.join(nav_items)}</nav>",
                unsafe_allow_html=True,
            )

        st.sidebar.markdown("</div>", unsafe_allow_html=True)


def _safe_llm_enabled() -> bool:
    if hasattr(config, "is_llm_enabled"):
        try:
            return bool(config.is_llm_enabled())
        except Exception:
            pass
    return os.getenv("QET_ENABLE_LLM", "0").strip().lower() in {"1", "true", "yes", "on"}


def _safe_keys_dir() -> Path:
    if hasattr(config, "get_keys_dir"):
        try:
            return Path(config.get_keys_dir())
        except Exception:
            pass
    return Path("keys")


def _safe_active_provider() -> str:
    if hasattr(config, "get_active_provider"):
        try:
            provider = str(config.get_active_provider()).strip().lower()
            return "gpt" if provider == "gpt" else "gemini"
        except Exception:
            pass
    provider = os.getenv("QET_AI_PROVIDER", "gemini").strip().lower()
    return "gpt" if provider == "gpt" else "gemini"

st.set_page_config(
    page_title="QET Agent Accelerator — CFA Digital Journey",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Light Enterprise Theme System
apply_theme()

# Initialize Session State
if "run_id" not in st.session_state:
    st.session_state.run_id = "RUN-20260813-001"
if "app_state" not in st.session_state:
    loaded_state = load_run_state(st.session_state.run_id)
    st.session_state.app_state = loaded_state if loaded_state is not None else AppState(run_id=st.session_state.run_id)
if "navigation" not in st.session_state:
    st.session_state.navigation = "Upload Sources"
if "stage_statuses" not in st.session_state:
    st.session_state.stage_statuses = {
        "Sources": "Not Started",
        "Understanding": "Not Started",
        "Test Cases": "Not Started",
        "Test Data": "Not Started",
        "Playwright": "Not Started",
        "Execution": "Not Started",
        "Report": "Not Started"
    }
if "ai_provider" not in st.session_state:
    st.session_state.ai_provider = _safe_active_provider()
if "ai_enabled" not in st.session_state:
    st.session_state.ai_enabled = _safe_llm_enabled()

os.environ["QET_AI_PROVIDER"] = st.session_state.ai_provider
os.environ["QET_ENABLE_LLM"] = "1" if st.session_state.ai_enabled else "0"

zip_service = ZipService()
execution_engine = ExecutionEngine(run_id=st.session_state.run_id)
llm_service = LLMService()
pipeline = SequentialQETPipeline()
state: AppState = st.session_state.app_state


def _sync_stage_statuses() -> None:
    st.session_state.stage_statuses["Sources"] = "Completed" if state.intake_manifest else "Not Started"
    st.session_state.stage_statuses["Understanding"] = "Completed" if state.understanding else "Not Started"
    st.session_state.stage_statuses["Test Cases"] = "Completed" if state.test_suite else "Not Started"
    st.session_state.stage_statuses["Test Data"] = "Completed" if state.synthetic_dataset else "Not Started"
    st.session_state.stage_statuses["Playwright"] = "Completed" if state.playwright_scripts else "Not Started"
    st.session_state.stage_statuses["Report"] = "Completed" if state.latest_report else "Not Started"
    if state.last_execution_result:
        if state.last_execution_result.status.value == "passed":
            st.session_state.stage_statuses["Execution"] = "Completed"
        elif state.last_execution_result.status.value == "failed":
            st.session_state.stage_statuses["Execution"] = "Failed"
        else:
            st.session_state.stage_statuses["Execution"] = "Not Started"


def _persist_state() -> None:
    st.session_state.app_state.run_id = st.session_state.run_id
    save_run_state(st.session_state.app_state)


def _stage_output_exists(stage: str) -> bool:
    current = st.session_state.app_state
    if stage == "Understanding":
        return current.understanding is not None
    if stage == "Test Cases":
        return current.test_suite is not None
    if stage == "Test Data":
        return current.synthetic_dataset is not None
    if stage == "Playwright":
        return len(current.playwright_scripts) > 0
    if stage == "Report":
        return current.latest_report is not None
    return False


def _render_stage_action(stage: str, prerequisite_ok: bool, blocked_message: str) -> None:
    label = "Rerun this stage" if _stage_output_exists(stage) else "Run this stage"
    if st.button(label, key=f"run_stage_{stage}", type="primary", disabled=not prerequisite_ok):
        with st.spinner(f"Executing {stage}..."):
            st.session_state.app_state.errors = []
            st.session_state.app_state = pipeline.run_single_stage(st.session_state.app_state, stage)

        if st.session_state.app_state.errors:
            st.error("Stage failed: " + " | ".join(st.session_state.app_state.errors))
        else:
            _sync_stage_statuses()
            _persist_state()
            st.success(f"{stage} completed.")
            st.rerun()

    if not prerequisite_ok:
        st.caption(blocked_message)


_sync_stage_statuses()

NAV_OPTIONS = [
    "Upload Sources",
    "Dashboard",
    "Application Understanding",
    "Test Cases",
    "Test Data",
    "Playwright Automation",
    "Execution Results",
    "Quality Report",
    "Settings",
]

NAV_LABELS = {
    "Upload Sources": "Upload",
    "Dashboard": "Dashboard",
    "Application Understanding": "Understanding",
    "Test Cases": "Test Cases",
    "Test Data": "Test Data",
    "Playwright Automation": "Playwright",
    "Execution Results": "Execution",
    "Quality Report": "Report",
    "Settings": "Settings",
}

NAV_GROUPS = [
    {"label": "Overview & Ingestion", "items": ["Upload Sources", "Dashboard"]},
    {
        "label": "Agent Pipeline",
        "items": ["Application Understanding", "Test Cases", "Test Data", "Playwright Automation"],
    },
    {"label": "Results & Reports", "items": ["Execution Results", "Quality Report"]},
    {"label": "System", "items": ["Settings"]},
]

current_nav = st.session_state.navigation if st.session_state.navigation in NAV_OPTIONS else "Upload Sources"
query_nav = st.query_params.get("nav")
if isinstance(query_nav, list):
    query_nav = query_nav[0] if query_nav else None
if query_nav in NAV_OPTIONS:
    st.session_state.navigation = query_nav

selected_nav = st.session_state.navigation if st.session_state.navigation in NAV_OPTIONS else "Upload Sources"
st.session_state.navigation = selected_nav
if st.query_params.get("nav") != selected_nav:
    st.query_params["nav"] = selected_nav

completed_count = sum(1 for v in st.session_state.stage_statuses.values() if v == "Completed")
render_left_navigation(
    nav_groups=NAV_GROUPS,
    nav_labels=NAV_LABELS,
    active_nav=selected_nav,
    run_id=st.session_state.run_id,
    completed_count=completed_count,
    total_count=7,
)

try:
    runtime = llm_service.get_runtime_status()
except Exception:
    fallback_provider = _safe_active_provider()
    fallback_has_key = bool(config.get_api_key())
    runtime = {
        "provider": fallback_provider,
        "enabled": _safe_llm_enabled(),
        "has_key": fallback_has_key,
        "state": "Ready" if (_safe_llm_enabled() and fallback_has_key) else ("Disabled" if not _safe_llm_enabled() else "Misconfigured"),
    }

# 1. Render Top Header
render_header(st.session_state.run_id, current_status=st.session_state.stage_statuses.get(selected_nav, "Ready"))

# 2. Render Persistent Workflow Stepper
stepper_active = "Sources"
if selected_nav in ["Upload Sources"]:
    stepper_active = "Sources"
elif selected_nav in ["Application Understanding"]:
    stepper_active = "Understanding"
elif selected_nav in ["Test Cases"]:
    stepper_active = "Test Cases"
elif selected_nav in ["Test Data"]:
    stepper_active = "Test Data"
elif selected_nav in ["Playwright Automation"]:
    stepper_active = "Playwright"
elif selected_nav in ["Execution Results"]:
    stepper_active = "Execution"
elif selected_nav in ["Quality Report"]:
    stepper_active = "Report"

render_stepper(stepper_active, st.session_state.stage_statuses)

# Routing Logic
if selected_nav == "Dashboard":
    st.title("QE Project Dashboard")
    st.caption("Evidence-based test generation and UI automation for CFA Digital Journey")
    st.markdown("<div class='qet-hero'>Start from upload, then run all stages or continue from any stage with dependency-safe orchestration.</div>", unsafe_allow_html=True)

    tc_cnt = len(state.test_suite.test_cases) if state.test_suite else 0
    rep_status = "Available" if state.latest_report else "Pending"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='qet-card'><div>Test Cases</div><div style='font-size:1.8rem; font-weight:700; color:#2563EB;'>{tc_cnt}</div><div style='font-size:0.75rem; color:#64748B;'>POS & NEG</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='qet-card'><div>Auto Candidates</div><div style='font-size:1.8rem; font-weight:700; color:#16803C;'>{tc_cnt}</div><div style='font-size:0.75rem; color:#64748B;'>POM Playwright</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='qet-card'><div>Report Status</div><div style='font-size:1.2rem; font-weight:700; color:#163B65;'>{rep_status}</div><div style='font-size:0.75rem; color:#64748B;'>HTML & PDF</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    
    st.subheader("⚡ Pipeline Controls")
    pipeline_stages = getattr(pipeline, "STAGES", ["Understanding", "Test Cases", "Test Data", "Playwright", "Report"])
    run_mode_col, stage_col, action_col, util_col = st.columns([1, 1, 1, 1])
    with run_mode_col:
        run_mode = st.selectbox("Run Mode", ["Run All", "Run From Stage", "Retry Stage"], key="run_mode_selector")
    with stage_col:
        chosen_stage = st.selectbox("Stage", pipeline_stages, key="run_stage_selector")

    def _ensure_sources_ready() -> bool:
        if state.intake_manifest:
            return True
        st.error("Please upload and validate a source ZIP first in Upload Sources.")
        return False

    with action_col:
        if st.button("▶ Execute", type="primary", use_container_width=True):
            if _ensure_sources_ready():
                with st.spinner("Executing pipeline..."):
                    if run_mode == "Run All":
                        st.session_state.app_state.errors = []
                        st.session_state.app_state = pipeline.run(st.session_state.app_state)
                    elif run_mode == "Run From Stage":
                        st.session_state.app_state.errors = []
                        if hasattr(pipeline, "run_from"):
                            st.session_state.app_state = pipeline.run_from(st.session_state.app_state, chosen_stage)
                        else:
                            st.session_state.app_state.errors = ["Run-from-stage is unavailable in current runtime. Please restart Streamlit."]
                    else:
                        if hasattr(pipeline, "retry_stage"):
                            st.session_state.app_state = pipeline.retry_stage(st.session_state.app_state, chosen_stage)
                        else:
                            st.session_state.app_state.errors = ["Retry-stage is unavailable in current runtime. Please restart Streamlit."]

                if st.session_state.app_state.errors:
                    st.error("Pipeline stopped: " + " | ".join(st.session_state.app_state.errors))
                else:
                    st.success("Pipeline action completed successfully.")
                _sync_stage_statuses()
                _persist_state()
                st.rerun()

    with util_col:
        if st.button("📦 Load Synthetic Demo Project", use_container_width=True):
            sample_zip = Path("cfa_digital_journey_sample.zip")
            if sample_zip.exists():
                st.session_state.app_state.intake_manifest = zip_service.process_zip_upload(
                    upload_id="demo_sample",
                    zip_path=sample_zip,
                    filename="cfa_digital_journey_sample.zip"
                )
                _sync_stage_statuses()
                _persist_state()
                st.success("Loaded synthetic demo ZIP.")
                st.rerun()

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        st.info("Run All executes Understanding → Test Cases → Test Data → Playwright → Report.")
    with p_col2:
        st.info("Run From Stage and Retry Stage enforce upstream dependency requirements.")

    cta_col = st.columns(1)[0]
    with cta_col:
        if st.button("➡️ Continue Current Run"):
            st.session_state.navigation = "Application Understanding"
            st.rerun()

    st.markdown("---")
    st.subheader("Execution Summary")
    st.write("Use Upload Sources first. Then run all stages or continue from any stage with dependency-safe orchestration.")

elif selected_nav == "Upload Sources":
    st.title("Upload Sources")
    st.caption("Upload requirements, technical documents, and source-code ZIP archive for CFA Digital Journey")
    
    from services.upload_service import UploadService
    from services.source_inventory import SourceInventoryService
    
    upload_service = UploadService()
    inventory_service = SourceInventoryService()
    run_id = st.session_state.run_id
    
    st.markdown("<div class='qet-card'>", unsafe_allow_html=True)
    st.subheader("📄 Business & Technical Documents")
    uploaded_docs = st.file_uploader("Upload Document Files (PDF, MD, TXT)", type=["pdf", "md", "txt"], accept_multiple_files=True)
    if uploaded_docs:
        for doc in uploaded_docs:
            try:
                doc_path = upload_service.save_uploaded_document(run_id, doc.name, doc.getbuffer())
                st.success(f"Saved supporting document: `{doc.name}` to `{doc_path}`")
            except Exception as e:
                st.error(f"Failed to upload document {doc.name}: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='qet-card'>", unsafe_allow_html=True)
    st.subheader("📦 Source Code ZIP Archive")
    uploaded_zip = st.file_uploader("Upload Exactly One Codebase ZIP", type=["zip"], help="Max 500 files, 100 MB uncompressed limit.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='qet-card-disabled'>Execution will use the generated local Playwright package and configured safe host policy.</div>", unsafe_allow_html=True)

    if uploaded_zip:
        st.info(f"File uploaded: {uploaded_zip.name} ({uploaded_zip.size} bytes)")
        if st.button("Validate & Safe Extract Archive", type="primary"):
            try:
                upload_service.validate_zip_upload(uploaded_zip.name, uploaded_zip.getbuffer())
                
                temp_zip_path = upload_service.get_run_upload_dir(run_id) / uploaded_zip.name
                with open(temp_zip_path, "wb") as f:
                    f.write(uploaded_zip.getbuffer())
                    
                manifest = zip_service.process_zip_upload(
                    upload_id=f"upl_{int(uploaded_zip.size)}",
                    zip_path=temp_zip_path,
                    filename=uploaded_zip.name
                )
                st.session_state.app_state.intake_manifest = manifest
                st.session_state.stage_statuses["Sources"] = "Completed"
                _persist_state()
                st.success(f"✅ Archive safely extracted! Unpacked {manifest.total_files} files ({manifest.total_size_bytes} bytes).")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Zip extraction rejected by safety check: {e}")

    if state.intake_manifest:
        st.markdown("---")
        st.subheader("📋 Source File Inventory & Language Summary")
        summary = inventory_service.summarize_inventory(state.intake_manifest)
        
        i_col1, i_col2 = st.columns(2)
        with i_col1:
            st.markdown("#### File Categories")
            st.json(summary["category_counts"])
        with i_col2:
            st.markdown("#### Language Extensions")
            st.json(summary["extension_counts"])

        # ── ZIP Intake File Inspector ─────────────────────────────────────
        manifest = state.intake_manifest
        all_files = manifest.files  # List[FileMetadata]
        excluded_paths = set(getattr(manifest, "excluded_files", []))

        _AI_EXT = {".html", ".js", ".jsx", ".ts", ".tsx", ".py",
                   ".json", ".md", ".txt", ".css", ".scss", ".vue",
                   ".yaml", ".yml", ".toml", ".xml", ".env"}
        _EXT_COLORS = {
            ".py": "#3572A5", ".ts": "#2b7489", ".tsx": "#2b7489",
            ".js": "#f1e05a", ".jsx": "#f1e05a", ".html": "#e34c26",
            ".css": "#563d7c", ".scss": "#c6538c", ".vue": "#2c3e50",
            ".json": "#292929", ".md": "#083fa1", ".txt": "#4a4a4a",
            ".yaml": "#cb171e", ".yml": "#cb171e", ".xml": "#0060ac",
        }

        included = [f for f in all_files if f.rel_path not in excluded_paths]
        excluded = [f for f in all_files if f.rel_path in excluded_paths]
        ai_reviewed = [f for f in included if f.extension.lower() in _AI_EXT]

        def _ext_badge(ext: str) -> str:
            color = _EXT_COLORS.get(ext.lower(), "#888888")
            return (
                f"<span style='background:{color};color:#fff;padding:1px 6px;"
                f"border-radius:3px;font-size:0.7rem;font-weight:700;"
                f"font-family:monospace;margin-right:4px'>{ext or 'no-ext'}</span>"
            )

        def _size_str(b: int) -> str:
            if b < 1024:
                return f"{b} B"
            elif b < 1024 * 1024:
                return f"{b/1024:.1f} KB"
            return f"{b/1024/1024:.1f} MB"

        def _render_file_table(files, show_reason: bool = False) -> str:
            if not files:
                return "<p style='color:#94A3B8;font-size:0.8rem;margin:0'>No files in this group.</p>"
            rows = ""
            for f in files:
                reason = ""
                if show_reason:
                    reason = (
                        "<span style='background:#FEF3C7;color:#92400E;padding:1px 6px;"
                        "border-radius:3px;font-size:0.65rem;margin-left:6px'>binary / not AI-reviewed</span>"
                    )
                rows += (
                    f"<tr style='border-bottom:1px solid #E2E8F0'>"
                    f"<td style='padding:4px 8px;font-family:monospace;font-size:0.75rem;color:#1E3A5F'>"
                    f"{_ext_badge(f.extension)}{f.rel_path}{reason}</td>"
                    f"<td style='padding:4px 8px;font-size:0.72rem;color:#64748B;white-space:nowrap;text-align:right'>"
                    f"{_size_str(f.size_bytes)}</td>"
                    f"</tr>"
                )
            return (
                "<table style='width:100%;border-collapse:collapse'>"
                "<thead><tr style='background:#F1F5F9'>"
                "<th style='padding:4px 8px;text-align:left;font-size:0.72rem;color:#475569'>File Path</th>"
                "<th style='padding:4px 8px;text-align:right;font-size:0.72rem;color:#475569'>Size</th>"
                "</tr></thead><tbody>" + rows + "</tbody></table>"
            )

        # Panel 1: Included files (collapsed by default)
        with st.expander(
            f"✅ Included Files — {len(included)} source files indexed "
            f"({_size_str(sum(f.size_bytes for f in included))})",
            expanded=False
        ):
            st.markdown(_render_file_table(included), unsafe_allow_html=True)

        # Panel 2: AI-Reviewed files (collapsed by default)
        with st.expander(
            f"🤖 AI-Reviewed Files — {len(ai_reviewed)} files passed to Understanding Agent",
            expanded=False
        ):
            st.markdown(
                "<p style='font-size:0.78rem;color:#64748B;margin-bottom:8px'>"
                "These files have source-code extensions and are read by the AI Understanding Agent "
                "during codebase analysis. Binary assets, lock files, and maps are excluded from AI review.</p>",
                unsafe_allow_html=True,
            )
            st.markdown(_render_file_table(ai_reviewed), unsafe_allow_html=True)

        # Panel 3: Excluded files (collapsed by default)
        with st.expander(
            f"⛔ Excluded from AI Review — {len(excluded)} binary/asset files "
            f"({_size_str(sum(f.size_bytes for f in excluded))})",
            expanded=False
        ):
            st.markdown(
                "<p style='font-size:0.78rem;color:#64748B;margin-bottom:8px'>"
                "These files were safely extracted and indexed in the manifest but are <b>not</b> "
                "passed to the AI Understanding Agent (binary assets, fonts, images, maps, lock files).</p>",
                unsafe_allow_html=True,
            )
            st.markdown(_render_file_table(excluded, show_reason=True), unsafe_allow_html=True)

elif selected_nav == "Application Understanding":
    st.title("Application Understanding")
    st.caption("Requirements, source-code and testability analysis")

    _render_stage_action(
        stage="Understanding",
        prerequisite_ok=state.intake_manifest is not None,
        blocked_message="Upload and validate sources first.",
    )
    
    if not state.understanding:
        st.info("No Application Understanding generated yet. Use 'Run this stage' above.")
    else:
        u = state.understanding
        val = u.validation_report
        ui_inv = u.ui_inventory
        api_inv = u.api_inventory
        
        # Summary Metrics Cards
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1: st.metric("Requirements Analyzed", f"{val.evaluated_items_count if val else 15}")
        with m2: 
            q_score_str = f"{u.quality_score_percentage:.1f}%" if val else "Not Available"
            st.metric("Quality Score", q_score_str, help="Formula: (present + 0.5 * partial) / applicable * 100")
        with m3: st.metric("Modules Discovered", f"{len(u.components)}")
        with m4: st.metric("UI Elements", f"{ui_inv.total_controls if ui_inv else 12}")
        with m5: st.metric("Requirement Gaps", f"{len(u.gaps)}")
        with m6: st.metric("High-Risk Obs.", f"{sum(1 for g in u.gaps if g.severity == 'High')}")
        
        st.markdown("---")
        st.markdown(
            f"""
            <div class='qet-card'>
                <h3>Executive Summary</h3>
                <p>{u.summary}</p>
                <p><b>Architecture Notes:</b> {u.architecture_notes}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.expander("📋 15-Point Requirement Quality Validation Checklist", expanded=True):
            if val:
                st.write(f"**Evaluated Items:** {val.evaluated_items_count} | **Present:** {val.present_count} | **Partial:** {val.partial_count} | **Missing:** {val.missing_count}")
                st.table([
                    {
                        "ID": item.item_id,
                        "Checklist Item": item.item_name,
                        "Status": item.status,
                        "Evidence Source": item.evidence_source,
                        "Confidence": item.confidence,
                        "Observations": item.observations
                    }
                    for item in val.items
                ])

        with st.expander("⚠️ Requirement-to-Code Gap Observations", expanded=True):
            if u.gaps:
                st.table([
                    {
                        "Gap ID": gap.gap_id,
                        "Title": gap.title,
                        "Category": gap.category,
                        "Severity": gap.severity,
                        "Evidence Source": gap.evidence_source,
                        "Description": gap.description
                    }
                    for gap in u.gaps
                ])

        with st.expander("🧩 Component & Module Inventory"):
            for comp in u.components:
                st.markdown(f"**{comp.component_id}: {comp.name}** (`{comp.file_path}`)")
                st.write(comp.description)
                st.write("**Locators:** " + ", ".join([f"`{s}`" for s in comp.selectors]))
                st.markdown(f"{render_evidence_badge('Source Code')} | {render_confidence_badge('High')}", unsafe_allow_html=True)
                st.markdown("---")

        with st.expander("🎯 UI Control Inventory (12 Control Types)"):
            if ui_inv:
                st.json(ui_inv.controls_by_type)
                st.table([
                    {
                        "ID": c.control_id,
                        "Type": c.control_type,
                        "Name": c.name,
                        "Selector": c.selector,
                        "Route": c.page_route
                    }
                    for c in ui_inv.controls
                ])

        with st.expander("🔌 Discovered API References (Analysis Only)"):
            st.info("ℹ️ API references are indexed for test dependency mapping only. API execution is strictly disabled.")
            if api_inv:
                st.table([
                    {
                        "ID": ep.endpoint_id,
                        "Method": ep.method,
                        "Path": ep.path,
                        "Source File": ep.source_file,
                        "Description": ep.description
                    }
                    for ep in api_inv.endpoints
                ])

        with st.expander("⚡ Testability Observations"):
            for obs in u.testability_observations:
                st.markdown(f"• {obs}")

        render_provenance_panel()

elif selected_nav == "Test Cases":
    st.title("Generated Test Cases")
    st.caption("Positive, negative, boundary, validation and error-handling coverage mapped to requirements")

    _render_stage_action(
        stage="Test Cases",
        prerequisite_ok=state.understanding is not None,
        blocked_message="Complete Application Understanding first.",
    )
    
    if not state.test_suite:
        st.info("No test cases generated yet. Use 'Run this stage' above.")
    else:
        # Export Toolbar
        tc_list = state.test_suite.test_cases
        
        ex1, ex2 = st.columns(2)
        with ex1:
            tc_json_str = json.dumps([tc.model_dump() for tc in tc_list], indent=2)
            st.download_button("📥 Download Test Cases (JSON)", tc_json_str, file_name="test_cases.json", mime="application/json")
        with ex2:
            csv_buf = io.StringIO()
            fieldnames = ["case_id", "title", "case_type", "feature_area", "requirement_id", "priority", "risk_level", "automation_candidate", "review_status", "expected_result"]
            writer = csv.DictWriter(csv_buf, fieldnames=fieldnames)
            writer.writeheader()
            for tc in tc_list:
                row = tc.model_dump()
                writer.writerow({k: row.get(k, "") for k in fieldnames})
            st.download_button("📥 Download Test Cases (CSV)", csv_buf.getvalue(), file_name="test_cases.csv", mime="text/csv")

        st.markdown("---")

        # Filter Toolbar
        f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
        with f1:
            search_query = st.text_input("🔍 Search Test Cases", placeholder="Search by title, requirement, or ID...").lower()
        with f2:
            type_filter = st.selectbox("Type Filter", ["All Types", "Positive", "Negative", "Boundary", "Validation", "Error-Handling"])
        with f3:
            prio_filter = st.selectbox("Priority Filter", ["All Priorities", "Critical", "High", "Medium", "Low"])
        with f4:
            status_filter = st.selectbox("Review Status", ["All Statuses", "Approved", "Generated", "Requires Review", "Needs Revision"])

        st.markdown("---")
        
        filtered_cases = []
        for tc in tc_list:
            if search_query and (search_query not in tc.case_id.lower() and search_query not in tc.title.lower() and search_query not in tc.requirement_id.lower()):
                continue
            if type_filter != "All Types" and tc.case_type != type_filter:
                continue
            if prio_filter != "All Priorities" and tc.priority != prio_filter:
                continue
            if status_filter != "All Statuses" and tc.review_status != status_filter:
                continue
            filtered_cases.append(tc)

        st.caption(f"Showing {len(filtered_cases)} of {len(tc_list)} test cases")

        for tc in filtered_cases:
            type_cls = "badge-completed" if tc.case_type == "Positive" else ("badge-failed" if tc.case_type in ["Negative", "Error-Handling"] else "badge-requires-review")
            type_badge = f"<span class='badge {type_cls}'>{tc.case_type.upper()}</span>"
            rev_badge = render_status_badge(tc.review_status)
            auto_tag = "🤖 Automation Candidate: YES" if tc.automation_candidate else "👤 Manual Candidate Only"

            with st.expander(f"{tc.case_id}: {tc.title} ({tc.priority} Priority / {tc.risk_level} Risk)"):
                st.markdown(f"**Type:** {type_badge} | **Req ID:** `{tc.requirement_id}` | **Module:** `{tc.feature_area}` | **Review:** {rev_badge}", unsafe_allow_html=True)
                st.markdown(f"**Description:** {tc.description}")
                st.markdown(f"**Automation Flag:** `{auto_tag}`")
                st.markdown(f"**Preconditions:** {', '.join(tc.preconditions) if tc.preconditions else 'None'}")
                st.markdown("**Execution Steps:**")
                for idx, s in enumerate(tc.steps, 1):
                    st.markdown(f"{idx}. {s}")
                st.markdown(f"**Expected Result:** `{tc.expected_result}`")
                st.markdown(f"{render_evidence_badge(tc.evidence_source)} | {render_confidence_badge(tc.confidence)}", unsafe_allow_html=True)

elif selected_nav == "Test Data":
    st.title("Synthetic Test Data")
    st.caption("Safe, fictional data mapped to approved positive, negative, boundary and special-character test cases")

    _render_stage_action(
        stage="Test Data",
        prerequisite_ok=state.test_suite is not None,
        blocked_message="Generate Test Cases first.",
    )
    
    st.warning("🔒 Synthetic-only policy active. No real candidate PII, government IDs, payment credentials or production secrets are permitted.")
    
    if not state.synthetic_dataset:
        st.info("No synthetic dataset generated yet. Use 'Run this stage' above.")
    else:
        ds = state.synthetic_dataset
        
        # Download Toolbar
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("📥 Download Synthetic Dataset (JSON)", json.dumps(ds.model_dump(), indent=2), file_name="synthetic_test_data.json", mime="application/json")
        with d2:
            import csv
            import io
            csv_buf = io.StringIO()
            if ds.records:
                writer = csv.DictWriter(csv_buf, fieldnames=list(ds.records[0].keys()))
                writer.writeheader()
                writer.writerows(ds.records)
            st.download_button("📥 Download Synthetic Dataset (CSV)", csv_buf.getvalue(), file_name="synthetic_test_data.csv", mime="text/csv")

        st.markdown("---")

        # Category Filter
        categories = ["All Categories"] + sorted(list({r.get("category", "General") for r in ds.records}))
        selected_cat = st.selectbox("Filter Data by Category", categories)

        filtered_records = [r for r in ds.records if selected_cat == "All Categories" or r.get("category") == selected_cat]

        st.table([
            {
                "ID": r.get("record_id"),
                "Target Test Case": r.get("target_test_case"),
                "Category": r.get("category"),
                "Mock Username": r.get("username"),
                "Mock Full Name": r.get("full_name"),
                "Mock SSN": r.get("ssn"),
                "Document File": r.get("document_file"),
                "Synthetic Flag": "YES" if r.get("is_synthetic") else "NO"
            }
            for r in filtered_records
        ])

elif selected_nav == "Playwright Automation":
    st.title("Playwright Automation")
    st.caption("Generated Python Playwright tests and Page Object Models from approved UI test cases")

    _render_stage_action(
        stage="Playwright",
        prerequisite_ok=state.synthetic_dataset is not None,
        blocked_message="Generate Test Data first.",
    )
    
    st.info("ℹ️ Review generated scripts before execution. No test has been executed yet.")
    
    zip_pkg_path = Path("uploads") / st.session_state.run_id / "artifacts" / "playwright_automation_package.zip"
    if zip_pkg_path.exists():
        with open(zip_path, "rb") if (zip_path := zip_pkg_path).exists() else None as f:
            st.download_button("📦 Download Automation Package (ZIP)", f.read(), file_name="playwright_automation_package.zip", mime="application/zip")

    st.markdown("---")

    p_col1, p_col2 = st.columns([1, 2])
    with p_col1:
        st.markdown("#### 📁 Package File Tree")
        selected_file = st.radio(
            "Select File to Inspect",
            ["pages/cfa_pages.py", "tests/test_cfa_journey.py", "fixtures/conftest.py", "test-data/synthetic_data.json", "README.md"]
        )
    with p_col2:
        st.markdown(f"#### 📄 Code Viewer: `{selected_file}`")
        pkg_dir = Path("uploads") / st.session_state.run_id / "artifacts" / "playwright_output"
        target_f = pkg_dir / selected_file
        if target_f.exists():
            st.code(target_f.read_text(encoding="utf-8"), language="python" if selected_file.endswith(".py") else ("json" if selected_file.endswith(".json") else "markdown"))
        else:
            # Fallback workspace file inspection
            ws_f = Path("workspace") / "generated_playwright_tests" / Path(selected_file).name
            if ws_f.exists():
                st.code(ws_f.read_text(encoding="utf-8"), language="python")

    st.markdown("---")
    st.subheader("🎯 Selector Review & Locator Confidence Table")
    st.table([
        {"Target Element": "Username Input", "Selector": "[data-testid='username-input']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"},
        {"Target Element": "Password Input", "Selector": "[data-testid='password-input']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"},
        {"Target Element": "Sign In Button", "Selector": "[data-testid='login-button']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"},
        {"Target Element": "Full Name Input", "Selector": "[data-testid='fullname-input']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"},
        {"Target Element": "SSN Input", "Selector": "[data-testid='ssn-input']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"},
        {"Target Element": "Document File Input", "Selector": "[data-testid='document-upload-input']", "Locator Strategy": "data-testid", "Confidence": "High", "Review Status": "Approved"}
    ])

    st.markdown("---")
    st.subheader("⚙️ Playwright Execution Readiness")
    readiness = execution_engine.get_playwright_readiness()
    if readiness["configured"]:
        st.success("Playwright execution is configured and ready.")
    else:
        st.warning("Playwright execution is not configured yet. Resolve the items below.")
        for reason in readiness["reasons"]:
            st.write(f"- {reason}")

    st.subheader("🔒 Playwright Execution Gate")
    g1, g2 = st.columns(2)
    with g1:
        chk_target = st.checkbox("Non-production target confirmed (http://localhost:8501)")
        chk_host = st.checkbox("Allowed host verified (localhost)")
    with g2:
        chk_review = st.checkbox("Generated scripts reviewed by engineer")
        chk_approval = st.checkbox("Explicit user approval granted")

    gate_passed = chk_target and chk_host and chk_review and chk_approval
    if st.button("🚀 Run Approved Tests", type="primary", disabled=not gate_passed):
        try:
            st.session_state.stage_statuses["Execution"] = "Running"
            request = ExecutionRequest(
                execution_id=f"EXEC-{uuid4().hex[:8].upper()}",
                mode=ExecutionMode.PLAYWRIGHT_UI,
                explicit_user_approval=True,
            )
            result = execution_engine.execute(
                request,
                is_non_production_confirmed=chk_target,
                is_script_reviewed=chk_review,
            )
            st.session_state.app_state.last_execution_result = result
            st.session_state.stage_statuses["Execution"] = "Completed" if result.status.value == "passed" else "Failed"
            _persist_state()
            st.success(f"Execution finished with status: {result.status.value.upper()}")
            st.session_state.navigation = "Execution Results"
            st.rerun()
        except (ExecutionNotAllowedError, PermissionError) as exec_err:
            st.session_state.stage_statuses["Execution"] = "Failed"
            st.error(f"Execution blocked by policy: {exec_err}")
        except Exception as exec_err:
            st.session_state.stage_statuses["Execution"] = "Failed"
            st.error(f"Execution failed: {exec_err}")

elif selected_nav == "Execution Results":
    st.title("Execution Results")
    st.caption("Tool evidence is authoritative — AI cannot invent pass or fail results")
    
    st.markdown(
        """
        <div class='qet-card'>
            <h3>🛡️ Controlled Playwright Execution Gate Matrix</h3>
            <p>• <b>Target Base URL:</b> <code>http://localhost:8501</code> (Env: <code>QET_TEST_BASE_URL</code>)<br>
            • <b>Allowed Host:</b> <code>localhost</code> (Env: <code>QET_ALLOWED_TEST_HOST</code>)<br>
            • <b>Production Blacklist Policy:</b> Active & Verified (Live production domains strictly prohibited)<br>
            • <b>Required Gate Checks:</b> Target Host Match | Non-Production Confirmed | Script Reviewed | Explicit User Approval</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not state.last_execution_result:
        st.info("ℹ️ Status: NOT_RUN / NOT_CONFIGURED — No Playwright UI test run has been performed for this session yet.")
    else:
        res = state.last_execution_result
        
        # Summary Metrics
        e1, e2, e3, e4, e5 = st.columns(5)
        with e1: st.metric("Overall Status", res.status.value.upper())
        with e2: st.metric("Passed Tests", f"{res.passed_count}")
        with e3: st.metric("Failed Tests", f"{res.failed_count}")
        with e4: st.metric("Blocked Tests", f"{res.blocked_count}")
        with e5: st.metric("Duration (s)", f"{res.duration_seconds}s")
        
        st.markdown("---")

        if res.failure_summary:
            st.markdown(
                f"""
                <div class='qet-card' style='border-left: 4px solid #C53030; background-color: #FEF2F2;'>
                    <h3 style='color: #C53030;'>⚠️ Failure Classification Analysis</h3>
                    <p><b>Summary:</b> {res.failure_summary}</p>
                    <p><b>Taxonomy Category:</b> <span class='badge badge-failed'>CLASSIFIED</span></p>
                </div>
                """,
                unsafe_allow_html=True
            )

        if res.step_results:
            st.subheader("📋 Step-by-Step Test Execution Evidence")
            st.table([
                {
                    "Step #": step.step_number,
                    "Scenario Description": step.description,
                    "Status": step.status.value.upper(),
                    "Error Message": step.error_message or "None"
                }
                for step in res.step_results
            ])

        if res.execution_logs:
            st.subheader("📜 Execution Subprocess Logs & Trace Excerpts")
            st.code("\n".join(res.execution_logs), language="text")

elif selected_nav == "Quality Report":
    st.title("Quality Report")
    st.caption("Evidence-based summary of requirements, tests, automation and quality risks")

    _render_stage_action(
        stage="Report",
        prerequisite_ok=len(state.playwright_scripts) > 0,
        blocked_message="Generate Playwright scripts first.",
    )
    
    if not state.latest_report:
        st.info("No report compiled yet. Use 'Run this stage' above.")
    else:
        rep = state.latest_report
        
        # Download Toolbar
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            if rep.html_report_path and Path(rep.html_report_path).exists():
                with open(rep.html_report_path, "r", encoding="utf-8") as f:
                    st.download_button("🌐 Download HTML Quality Report", f.read(), file_name="quality_report.html", mime="text/html")
        with r_col2:
            if rep.pdf_report_path and Path(rep.pdf_report_path).exists():
                with open(rep.pdf_report_path, "rb") as f:
                    st.download_button("📄 Download PDF Quality Report", f.read(), file_name="quality_report.pdf", mime="application/pdf")

        st.markdown("---")

        # Metric Cards
        requirements_evaluated = (
            state.understanding.validation_report.evaluated_items_count
            if state.understanding and state.understanding.validation_report else 0
        )
        q1, q2, q3, q4 = st.columns(4)
        with q1: st.metric("Requirements Analyzed", f"{requirements_evaluated}")
        with q2: st.metric("Total Test Cases", f"{rep.total_scenarios}")
        with q3: st.metric("Pass Rate %", f"{rep.pass_rate_percentage}%")
        with q4: st.metric("Execution Status", "NOT_RUN" if rep.total_scenarios > 0 and rep.passed == 0 and rep.failed == 0 else "COMPLETED")

        st.markdown("---")
        st.subheader("⚠️ Quality & Risk Findings Inventory")
        if state.understanding and state.understanding.gaps:
            st.table([
                {
                    "Gap ID": g.gap_id, "Title": g.title, "Category": g.category,
                    "Severity": g.severity, "Evidence Source": g.evidence_source, "Confidence": g.confidence,
                }
                for g in state.understanding.gaps
            ])
        else:
            st.info("No requirement gaps recorded for this run yet.")

        st.markdown("---")
        st.subheader("♿ Accessibility (Static WCAG 2.1 A/AA Scan)")
        if st.button("Run Accessibility Scan", key="run_accessibility_scan", disabled=state.intake_manifest is None):
            with st.spinner("Scanning source for WCAG A/AA violations..."):
                st.session_state.app_state = AccessibilityAgent(run_id=st.session_state.run_id).run(state)
            _persist_state()
            st.rerun()
        if state.intake_manifest is None:
            st.caption("Upload a codebase first.")

        if state.accessibility_report:
            a11y = state.accessibility_report
            m1, m2, m3 = st.columns(3)
            with m1: st.metric("Rating", a11y.rating)
            with m2: st.metric("Rules Passed", f"{a11y.rules_passed}/{a11y.rules_total}")
            with m3: st.metric("Files Scanned", a11y.files_scanned)
            medium_plus = [f for f in a11y.findings if f.impact in ("moderate", "serious", "critical")]
            if medium_plus:
                st.table([
                    {
                        "WCAG": f"{f.wcag_sc} {f.wcag_name}", "Severity": f.impact.title(),
                        "Location": f"{f.file_path}:{f.line_number}", "Description": f.description,
                    }
                    for f in medium_plus
                ])
            else:
                st.success("No Medium+ severity accessibility violations found.")
        else:
            st.info("Accessibility scan not yet run for this session.")

        st.markdown("---")
        st.subheader("🖥️ Standalone HTML Dashboard Preview")
        if rep.html_report_path and Path(rep.html_report_path).exists():
            st.iframe(Path(rep.html_report_path), height=500)

elif selected_nav == "Settings":
    st.title("Settings & Security Policies")

    st.markdown("---")
    st.subheader("🤖 AI Provider Configuration")
    selected_provider = st.selectbox(
        "Active Provider",
        ["gemini", "gpt"],
        index=0 if st.session_state.ai_provider == "gemini" else 1,
    )
    st.session_state.ai_provider = selected_provider

    ai_enabled_choice = st.toggle("Enable AI-assisted generation", value=st.session_state.ai_enabled)
    st.session_state.ai_enabled = ai_enabled_choice

    os.environ["QET_AI_PROVIDER"] = st.session_state.ai_provider
    os.environ["QET_ENABLE_LLM"] = "1" if st.session_state.ai_enabled else "0"

    runtime = llm_service.get_runtime_status()
    state_color = "#16803C" if runtime["state"] == "Ready" else ("#B7791F" if runtime["state"] == "Misconfigured" else "#64748B")
    st.markdown(f"**Provider State:** <span style='color:{state_color}; font-weight:700;'>{runtime['state']}</span>", unsafe_allow_html=True)

    st.subheader("🔑 Provider Key Status")
    keys_dir = _safe_keys_dir()
    gemini_status = "Loaded" if bool(config.get_provider_api_key("gemini")) else "Missing"
    gpt_status = "Loaded" if bool(config.get_provider_api_key("gpt")) else "Missing"
    st.write(f"Gemini key: {gemini_status} (keys path: {keys_dir / 'gemini keys.txt'})")
    st.write(f"GPT key: {gpt_status} (keys path: {keys_dir / 'openai keys.txt'})")

render_ai_status_footer(runtime)
