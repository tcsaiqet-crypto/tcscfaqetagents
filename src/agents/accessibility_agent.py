"""Accessibility Testing Specialist Agent -- static WCAG 2.1 A/AA rule engine.

No browser, no runtime execution, no external API/network calls. The uploaded
application's rendered/served URLs are dynamic per-run and can't be assumed to
be reachable, so this agent scans the extracted SOURCE CODE (HTML/JSX/TSX
templates and embedded/linked CSS) with regex-based pattern matching against a
fixed set of 13 WCAG 2.1 A/AA success criteria that can be reasonably verified
without rendering a page. Everything runs locally over files already on disk.

Honesty note: this is a proof-of-concept static approximation, not a full WCAG
audit. Roughly two-thirds of the WCAG A/AA criteria (focus order, keyboard
traps, reflow, timing, etc.) fundamentally require a rendered browser and are
therefore out of scope here by design -- they are simply not counted for or
against the rating below.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from schemas.contracts import AccessibilityFinding, AccessibilityReport, AccessibilityRuleResult, AppState
from src.agents.base_agent import BaseAgent
from src.utils.logger import logger

SCANNABLE_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".css"}
PASS_RATING_THRESHOLD = 10  # of 13 rules; see run_agent_suite guidance from the user

GENERIC_LINK_TEXT = {"click here", "here", "read more", "more", "link", "click"}


class AccessibilityAgent(BaseAgent):
    """Specialist agent scanning uploaded source for statically verifiable WCAG A/AA violations."""

    __test__ = False

    def __init__(self, run_id: str = "RUN-20260813-001"):
        super().__init__(agent_name="AccessibilityAgent", description="Static WCAG 2.1 A/AA Rule Engine")
        self.run_id = run_id
        self.artifact_dir = Path("uploads") / run_id / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def run(self, state: AppState) -> AppState:
        source_root = Path(state.intake_manifest.extracted_path) if state.intake_manifest else Path("sample_test_target_app")
        files = self._collect_files(source_root)

        findings: List[AccessibilityFinding] = []
        for file_path in files:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                logger.warning("Accessibility scan skipped unreadable file %s: %s", file_path, exc)
                continue
            rel_path = str(file_path.relative_to(source_root)) if source_root in file_path.parents else str(file_path)
            findings.extend(self._scan_file(rel_path, text))

        report = self._build_report(len(files), findings)
        state.accessibility_report = report
        self._save_artifacts(report)
        return state

    def _collect_files(self, source_root: Path) -> List[Path]:
        if not source_root.exists():
            return []
        return [p for p in source_root.rglob("*") if p.is_file() and p.suffix.lower() in SCANNABLE_EXTENSIONS]

    def _scan_file(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings: List[AccessibilityFinding] = []
        is_full_document = bool(re.search(r"<html\b", text, re.IGNORECASE))

        findings.extend(self._check_img_alt(rel_path, text))
        findings.extend(self._check_input_labels(rel_path, text))
        findings.extend(self._check_duplicate_ids(rel_path, text))
        findings.extend(self._check_link_purpose(rel_path, text))
        findings.extend(self._check_non_keyboard_clickable(rel_path, text))
        findings.extend(self._check_input_autocomplete(rel_path, text))
        findings.extend(self._check_contrast(rel_path, text))
        findings.extend(self._check_focus_visible(rel_path, text))
        if is_full_document:
            findings.extend(self._check_page_title(rel_path, text))
            findings.extend(self._check_lang_attribute(rel_path, text))
            findings.extend(self._check_skip_link(rel_path, text))

        return findings

    # -- Rule 1: SC 1.1.1 Non-text Content -------------------------------------------------
    def _check_img_alt(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        for match in re.finditer(r"<img\b[^>]*>", text, re.IGNORECASE):
            tag = match.group(0)
            if not re.search(r"\balt\s*=", tag, re.IGNORECASE):
                findings.append(self._finding(
                    "img-alt", "1.1.1", "Non-text Content", "critical",
                    "Image element has no 'alt' attribute.", rel_path, text, match.start(), tag,
                ))
        return findings

    # -- Rule 2/3: SC 1.3.1 Info and Relationships / 3.3.2 Labels or Instructions ---------
    def _check_input_labels(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        label_for_ids = set(re.findall(r"<label\b[^>]*\bfor\s*=\s*[\"']([^\"']+)[\"']", text, re.IGNORECASE))
        for match in re.finditer(r"<input\b[^>]*>", text, re.IGNORECASE):
            tag = match.group(0)
            if re.search(r"type\s*=\s*[\"']hidden[\"']", tag, re.IGNORECASE):
                continue
            if re.search(r"\baria-label(ledby)?\s*=", tag, re.IGNORECASE):
                continue
            id_match = re.search(r"\bid\s*=\s*[\"']([^\"']+)[\"']", tag, re.IGNORECASE)
            if id_match and id_match.group(1) in label_for_ids:
                continue
            findings.append(self._finding(
                "input-label", "1.3.1", "Info and Relationships", "critical",
                "Input has no associated <label>, aria-label, or aria-labelledby.", rel_path, text, match.start(), tag,
            ))
        return findings

    # -- Rule 4: SC 4.1.1 Parsing (duplicate IDs) -----------------------------------------
    def _check_duplicate_ids(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        seen: Dict[str, int] = {}
        for match in re.finditer(r"\bid\s*=\s*[\"']([^\"']+)[\"']", text, re.IGNORECASE):
            value = match.group(1)
            if value in seen:
                findings.append(self._finding(
                    "duplicate-id", "4.1.1", "Parsing", "moderate",
                    f"Duplicate id '{value}' found in the same file.", rel_path, text, match.start(), match.group(0),
                ))
            seen[value] = seen.get(value, 0) + 1
        return findings

    # -- Rule 5: SC 2.4.4 Link Purpose (In Context) ---------------------------------------
    def _check_link_purpose(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        for match in re.finditer(r"<a\b[^>]*>(.*?)</a>", text, re.IGNORECASE | re.DOTALL):
            inner_text = re.sub(r"<[^>]+>", "", match.group(1)).strip().lower()
            if inner_text in GENERIC_LINK_TEXT:
                findings.append(self._finding(
                    "generic-link-text", "2.4.4", "Link Purpose (In Context)", "moderate",
                    f"Link text '{inner_text}' does not describe its destination.", rel_path, text, match.start(), match.group(0)[:120],
                ))
        return findings

    # -- Rule 6: SC 2.1.1 Keyboard ---------------------------------------------------------
    def _check_non_keyboard_clickable(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        for match in re.finditer(r"<(div|span)\b[^>]*\bonclick\s*=[^>]*>", text, re.IGNORECASE):
            tag = match.group(0)
            if re.search(r"\brole\s*=", tag, re.IGNORECASE) and re.search(r"\btabindex\s*=", tag, re.IGNORECASE):
                continue
            findings.append(self._finding(
                "non-keyboard-clickable", "2.1.1", "Keyboard", "serious",
                f"<{match.group(1)}> with onclick has no role/tabindex, so it is not keyboard-operable.",
                rel_path, text, match.start(), tag,
            ))
        return findings

    # -- Rule 7: SC 1.3.5 Identify Input Purpose ------------------------------------------
    def _check_input_autocomplete(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        autocomplete_types = {"email", "password", "tel", "name", "username"}
        for match in re.finditer(r"<input\b[^>]*>", text, re.IGNORECASE):
            tag = match.group(0)
            type_match = re.search(r"type\s*=\s*[\"'](\w+)[\"']", tag, re.IGNORECASE)
            name_match = re.search(r"name\s*=\s*[\"'](\w+)[\"']", tag, re.IGNORECASE)
            hint = (type_match.group(1).lower() if type_match else "") + " " + (name_match.group(1).lower() if name_match else "")
            if not any(t in hint for t in autocomplete_types):
                continue
            if re.search(r"\bautocomplete\s*=", tag, re.IGNORECASE):
                continue
            findings.append(self._finding(
                "missing-autocomplete", "1.3.5", "Identify Input Purpose", "minor",
                "Input collecting common user data has no 'autocomplete' attribute.", rel_path, text, match.start(), tag,
            ))
        return findings

    # -- Rule 8/9: SC 1.4.3 Contrast (Minimum) / 1.4.11 Non-text Contrast -----------------
    def _check_contrast(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        for match in re.finditer(r"style\s*=\s*[\"']([^\"']*)[\"']", text, re.IGNORECASE):
            style = match.group(1)
            colors = dict(re.findall(r"(color|background(?:-color)?)\s*:\s*#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", style))
            fg = colors.get("color")
            bg = colors.get("background-color") or colors.get("background")
            if not fg or not bg:
                continue
            ratio = self._contrast_ratio(fg, bg)
            if ratio is None:
                continue
            if ratio < 4.5:
                findings.append(self._finding(
                    "low-contrast", "1.4.3", "Contrast (Minimum)", "serious",
                    f"Inline style contrast ratio {ratio:.2f}:1 is below the 4.5:1 minimum for text.",
                    rel_path, text, match.start(), match.group(0)[:120],
                ))
            elif ratio < 3.0:
                findings.append(self._finding(
                    "low-non-text-contrast", "1.4.11", "Non-text Contrast", "moderate",
                    f"Inline style contrast ratio {ratio:.2f}:1 is below the 3:1 minimum for UI components.",
                    rel_path, text, match.start(), match.group(0)[:120],
                ))
        return findings

    @staticmethod
    def _contrast_ratio(fg_hex: str, bg_hex: str):
        def luminance(hex_value: str) -> float:
            if len(hex_value) == 3:
                hex_value = "".join(c * 2 for c in hex_value)
            r, g, b = (int(hex_value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

            def channel(c: float) -> float:
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            r, g, b = channel(r), channel(g), channel(b)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        try:
            l1, l2 = luminance(fg_hex), luminance(bg_hex)
        except ValueError:
            return None
        lighter, darker = max(l1, l2), min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    # -- Rule 10: SC 2.4.7 Focus Visible ---------------------------------------------------
    def _check_focus_visible(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        findings = []
        for match in re.finditer(r"outline\s*:\s*(none|0)\b", text, re.IGNORECASE):
            findings.append(self._finding(
                "outline-removed", "2.4.7", "Focus Visible", "moderate",
                "'outline: none' removes the default focus indicator with no visible replacement.",
                rel_path, text, match.start(), match.group(0),
            ))
        return findings

    # -- Rule 11: SC 2.4.2 Page Titled (full documents only) ------------------------------
    def _check_page_title(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if title_match and title_match.group(1).strip():
            return []
        return [self._finding(
            "missing-page-title", "2.4.2", "Page Titled", "serious",
            "Document has no non-empty <title>.", rel_path, text, 0, "<title>",
        )]

    # -- Rule 12: SC 3.1.1 Language of Page (full documents only) ------------------------
    def _check_lang_attribute(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        html_match = re.search(r"<html\b[^>]*>", text, re.IGNORECASE)
        if html_match and re.search(r"\blang\s*=\s*[\"'][^\"']+[\"']", html_match.group(0), re.IGNORECASE):
            return []
        return [self._finding(
            "missing-lang", "3.1.1", "Language of Page", "serious",
            "<html> tag has no 'lang' attribute.", rel_path, text, html_match.start() if html_match else 0,
            html_match.group(0) if html_match else "<html>",
        )]

    # -- Rule 13: SC 2.4.1 Bypass Blocks (full documents only) ----------------------------
    def _check_skip_link(self, rel_path: str, text: str) -> List[AccessibilityFinding]:
        if re.search(r"href\s*=\s*[\"']#main", text, re.IGNORECASE) or re.search(r"skip[-_ ]?(link|nav|to-content)", text, re.IGNORECASE):
            return []
        return [self._finding(
            "missing-skip-link", "2.4.1", "Bypass Blocks", "moderate",
            "No skip-link mechanism found to bypass repeated navigation blocks.", rel_path, text, 0, "<body>",
        )]

    def _finding(
        self, rule_id: str, sc: str, name: str, impact: str, description: str,
        rel_path: str, text: str, offset: int, snippet: str,
    ) -> AccessibilityFinding:
        line_number = text.count("\n", 0, offset) + 1
        return AccessibilityFinding(
            rule_id=rule_id,
            wcag_sc=sc,
            wcag_name=name,
            impact=impact,
            description=description,
            file_path=rel_path,
            line_number=line_number,
            snippet=snippet.strip()[:160],
        )

    def _build_report(self, files_scanned: int, findings: List[AccessibilityFinding]) -> AccessibilityReport:
        rule_catalog: List[Tuple[str, str, str, str, str]] = [
            # (rule_id, wcag_sc, wcag_name, wcag_level, impact)
            ("img-alt", "1.1.1", "Non-text Content", "A", "critical"),
            ("input-label", "1.3.1", "Info and Relationships", "A", "critical"),
            ("non-keyboard-clickable", "2.1.1", "Keyboard", "A", "serious"),
            ("missing-skip-link", "2.4.1", "Bypass Blocks", "A", "moderate"),
            ("missing-page-title", "2.4.2", "Page Titled", "A", "serious"),
            ("generic-link-text", "2.4.4", "Link Purpose (In Context)", "A", "moderate"),
            ("missing-lang", "3.1.1", "Language of Page", "A", "serious"),
            ("duplicate-id", "4.1.1", "Parsing", "A", "moderate"),
            ("missing-autocomplete", "1.3.5", "Identify Input Purpose", "AA", "minor"),
            ("low-contrast", "1.4.3", "Contrast (Minimum)", "AA", "serious"),
            ("low-non-text-contrast", "1.4.11", "Non-text Contrast", "AA", "moderate"),
            ("outline-removed", "2.4.7", "Focus Visible", "AA", "moderate"),
            # input-label backs both 1.3.1 and 3.3.2 with the same evidence.
            ("input-label", "3.3.2", "Labels or Instructions", "A", "critical"),
        ]

        violations_by_rule: Dict[str, int] = {}
        for finding in findings:
            violations_by_rule[finding.rule_id] = violations_by_rule.get(finding.rule_id, 0) + 1

        rule_results = []
        for rule_id, sc, name, level, impact in rule_catalog:
            count = violations_by_rule.get(rule_id, 0)
            rule_results.append(AccessibilityRuleResult(
                rule_id=rule_id, wcag_sc=sc, wcag_name=name, wcag_level=level,
                impact=impact, passed=(count == 0), violation_count=count,
            ))

        rules_passed = sum(1 for r in rule_results if r.passed)
        rating = "A" if rules_passed >= PASS_RATING_THRESHOLD else "Below A"

        counts = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
        for finding in findings:
            counts[finding.impact] = counts.get(finding.impact, 0) + 1

        return AccessibilityReport(
            files_scanned=files_scanned,
            rules_total=len(rule_catalog),
            rules_passed=rules_passed,
            rating=rating,
            total_violations=len(findings),
            critical_count=counts["critical"],
            serious_count=counts["serious"],
            moderate_count=counts["moderate"],
            minor_count=counts["minor"],
            rule_results=rule_results,
            findings=findings,
            engine="static-rule-engine",
            generated_at=datetime.now(timezone.utc).isoformat(),
            provenance={
                "generator": "AccessibilityAgent",
                "method": "static-source-pattern-matching",
                "rating_threshold": f"{PASS_RATING_THRESHOLD}/{len(rule_catalog)} rules passed => 'A'",
            },
        )

    def _save_artifacts(self, report: AccessibilityReport) -> None:
        path = self.artifact_dir / "accessibility_report.json"
        path.write_text(json.dumps(report.model_dump(), indent=2), encoding="utf-8")
        logger.info("Saved accessibility report to %s", path)

