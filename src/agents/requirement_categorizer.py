"""Requirement Categorizer Agent - classifies business and technical requirements into categories.

G3 Hardening (Spec-Kit 006): LLM generation now routes through LLMService.generate_with_gemini()
and LLMService._generate_with_gpt() instead of making raw HTTP calls with a hardcoded model name.
This ensures model discovery, candidate ranking, and error diagnostics remain consistent with the
shared LLM service contract used across all other agents.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from schemas.contracts import (
    AppState,
    ApplicationUnderstanding,
    Requirement,
    RequirementCategory,
    RequirementType
)
from src.agents.base_agent import BaseAgent
from src.services.llm_service import LLMService
from src.utils.logger import logger


class AIRequiredFailureException(Exception):
    def __init__(self, error_code: str, error_message: str, diagnostics: Dict[str, Any]):
        super().__init__(error_message)
        self.error_code = error_code
        self.error_message = error_message
        self.diagnostics = diagnostics


class RequirementCategorizer(BaseAgent):
    """Specialist agent to categorize app requirements before test generation."""

    __test__ = False

    def __init__(self, run_id: str = "RUN-20260813-001"):
        super().__init__(agent_name="RequirementCategorizer", description="Requirement Categorization Specialist")
        self.run_id = run_id
        self.artifact_dir = Path("uploads") / run_id / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.llm = LLMService()

    def run_ai_required(self, state: AppState) -> Tuple[AppState, Dict[str, Any]]:
        logger.info(f"Executing AI-Required Requirement Categorization for run {self.run_id}...")

        provider = self.llm._active_provider()
        api_key = self.llm._provider_key(provider)

        if not api_key or "placeholder" in api_key.lower():
            raise AIRequiredFailureException(
                error_code="provider_key_missing",
                error_message="Gemini API key missing or set to placeholder.",
                diagnostics={"provider": provider, "reason": "Missing API key"}
            )

        if not state.understanding:
            raise AIRequiredFailureException(
                error_code="schema_validation_failed",
                error_message="No Application Understanding artifact exists to categorize requirements from.",
                diagnostics={"run_id": self.run_id}
            )

        # Build prompt using existing understanding elements
        und = state.understanding
        prompt = (
            "You are a QA requirements analyst. Analyze the following application gaps, components, and notes, "
            "and output a structured requirement catalog in strict JSON format. "
            "Return JSON with key 'requirements', which is an array of objects. "
            "Each requirement object must have: requirement_id (string, e.g. REQ-F01), title (string), "
            "description (string), type (string, must be exactly one of: Functional, NonFunctional, Security, "
            "Performance, Accessibility, Reliability, Integration, Compliance, DataQuality, Usability), "
            "category_id (string, e.g. CAT-SEC), source_evidence (string).\\n"
            f"Summary: {und.summary}\\n"
            f"Architecture: {und.architecture_notes}\\n"
            f"Components: {[c.name for c in und.components]}\\n"
            f"Gaps: {[g.title for g in und.gaps]}\\n"
        )

        # G3: Route through LLMService instead of raw inline HTTP calls.
        # This ensures model discovery, candidate ranking, and timeout/error
        # diagnostics are handled consistently by the shared LLM service layer.
        llm_text: Optional[str] = None
        if provider == "gpt":
            llm_text = self.llm._generate_with_gpt(prompt, api_key)
            if llm_text is None:
                err = self.llm.last_error or {}
                err_code = err.get("error_code", "provider_disabled")
                status = err.get("status_code")
                if status in (401, 403):
                    err_code = "provider_key_missing"
                raise AIRequiredFailureException(
                    error_code=err_code,
                    error_message=err.get("error_message", "OpenAI GPT generation failed."),
                    diagnostics={**err, "provider": "gpt"}
                )
        else:
            # Gemini: use model-discovery + candidate-ranking path
            llm_text, attempts = self.llm.generate_with_gemini(prompt, api_key)
            if llm_text is None:
                last = attempts[-1] if attempts else {}
                err_code = last.get("error_code", "model_discovery_failed")
                status = last.get("status_code")
                if status in (401, 403):
                    err_code = "provider_key_missing"
                raise AIRequiredFailureException(
                    error_code=err_code,
                    error_message=last.get("error_message", "Gemini generation failed across all candidate models."),
                    diagnostics={"provider": "gemini", "attempts": attempts}
                )

        llm_data = self.llm.parse_json_payload(llm_text)
        if not llm_data or not isinstance(llm_data, dict) or "requirements" not in llm_data:
            raise AIRequiredFailureException(
                error_code="invalid_model_json",
                error_message="Model returned response that could not be parsed as valid JSON requirement catalog.",
                diagnostics={"provider": provider, "raw_preview": (llm_text[:300] if llm_text else "")}
            )

        requirements = []
        raw_reqs = llm_data.get("requirements") or []
        for i, item in enumerate(raw_reqs):
            req_id = item.get("requirement_id") or f"REQ-{i+1}"
            title = item.get("title") or f"Requirement {i+1}"
            desc = item.get("description") or "AI extracted requirement"
            r_type = item.get("type") or "Functional"
            cat_id = item.get("category_id") or "CAT-FUN"
            evidence = item.get("source_evidence") or "understanding_agent.py"
            
            # Map type string to enum
            try:
                type_enum = RequirementType(r_type)
            except Exception:
                type_enum = RequirementType.Functional

            requirements.append(Requirement(
                requirement_id=req_id,
                title=title,
                description=desc,
                type=type_enum,
                category_id=cat_id,
                source_evidence=evidence
            ))

        categories = self._group_requirements_into_categories(requirements)

        # Update state
        state.understanding.requirements = requirements
        state.understanding.requirement_categories = categories

        # Save artifacts
        self._save_artifacts(requirements, categories)

        provenance = {
            "provider": provider,
            "stage": "requirement_categorization",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "fallback_used": False,
            "validation_status": "VALIDATED"
        }
        return state, provenance

    def run(self, state: AppState) -> AppState:
        logger.info(f"Executing Deterministic/Heuristic Requirement Categorization for run {self.run_id}...")

        if not state.understanding:
            logger.warning("No Application Understanding exists to categorize. Initializing fallback understanding.")
            # Fallback initialization is handled upstream, but we bypass to prevent crash.
            return state

        # Collect components, flows, gaps
        und = state.understanding
        requirements: List[Requirement] = []

        # Heuristic 1: Functional from components & flows
        for idx, comp in enumerate(und.components):
            req_type = RequirementType.Functional
            category_id = "CAT-FUNC"
            evidence = comp.file_path
            
            # Classify using keywords
            name_lower = comp.name.lower() + " " + comp.description.lower()
            if any(k in name_lower for k in ["login", "auth", "password", "token", "jwt", "credential"]):
                req_type = RequirementType.Security
                category_id = "CAT-SEC"
            elif any(k in name_lower for k in ["wcag", "aria", "contrast", "accessibility", "reader"]):
                req_type = RequirementType.Accessibility
                category_id = "CAT-A11Y"
            elif any(k in name_lower for k in ["api", "rest", "endpoint", "http", "service"]):
                req_type = RequirementType.Integration
                category_id = "CAT-INT"
            elif any(k in name_lower for k in ["validate", "constraint", "size", "limit", "format"]):
                req_type = RequirementType.DataQuality
                category_id = "CAT-DQ"
            elif any(k in name_lower for k in ["drag", "drop", "theme", "light", "dark", "tooltip"]):
                req_type = RequirementType.Usability
                category_id = "CAT-USA"

            requirements.append(Requirement(
                requirement_id=f"REQ-{comp.component_id.upper()}",
                title=f"Core system support for {comp.name}",
                description=f"Verify UI elements, styles, and handlers of {comp.description}",
                type=req_type,
                category_id=category_id,
                source_evidence=evidence
            ))

        # Heuristic 2: Technical/Non-functional from gaps
        for idx, gap in enumerate(und.gaps):
            req_type = RequirementType.NonFunctional
            category_id = "CAT-NFR"
            evidence = gap.evidence_source
            
            name_lower = gap.title.lower() + " " + gap.description.lower()
            if any(k in name_lower for k in ["timeout", "latency", "load", "performance", "slow"]):
                req_type = RequirementType.Performance
                category_id = "CAT-PERF"
            elif any(k in name_lower for k in ["retry", "recovery", "failover", "fallback"]):
                req_type = RequirementType.Reliability
                category_id = "CAT-REL"
            elif any(k in name_lower for k in ["privacy", "pii", "consent", "regulation"]):
                req_type = RequirementType.Compliance
                category_id = "CAT-COMP"

            requirements.append(Requirement(
                requirement_id=f"REQ-GAP-{gap.gap_id.upper()}",
                title=gap.title,
                description=gap.description,
                type=req_type,
                category_id=category_id,
                source_evidence=evidence
            ))

        # Guarantee Functional for flow happy paths
        for idx, flow in enumerate(und.flows):
            requirements.append(Requirement(
                requirement_id=f"REQ-FLOW-{flow.flow_id.upper()}",
                title=f"Workflow transaction: {flow.name}",
                description=flow.description,
                type=RequirementType.Functional,
                category_id="CAT-FUNC",
                source_evidence="understanding_agent.py"
            ))

        categories = self._group_requirements_into_categories(requirements)

        # Update state
        state.understanding.requirements = requirements
        state.understanding.requirement_categories = categories

        # Save artifacts
        self._save_artifacts(requirements, categories)
        return state

    def _group_requirements_into_categories(self, requirements: List[Requirement]) -> List[RequirementCategory]:
        category_map: Dict[str, List[Requirement]] = {}
        for req in requirements:
            category_map[req.category_id] = category_map.get(req.category_id, [])
            category_map[req.category_id].append(req)

        categories = []
        for cat_id, req_list in category_map.items():
            first_req = req_list[0]
            cat_name = "Functional Verification" if cat_id == "CAT-FUNC" else \
                       "Security Controls" if cat_id == "CAT-SEC" else \
                       "Accessibility Requirements" if cat_id == "CAT-A11Y" else \
                       "Integration Interfaces" if cat_id == "CAT-INT" else \
                       "Performance Benchmarks" if cat_id == "CAT-PERF" else \
                       "Reliability and Recovery" if cat_id == "CAT-REL" else \
                       "Compliance & Privacy Rules" if cat_id == "CAT-COMP" else \
                       "Data Quality Guidelines" if cat_id == "CAT-DQ" else \
                       "Usability Standards" if cat_id == "CAT-USA" else \
                       "Non-Functional Requirements" if cat_id == "CAT-NFR" else "Uncategorized Requirements"
            
            categories.append(RequirementCategory(
                category_id=cat_id,
                name=cat_name,
                type=first_req.type,
                description=f"Requirement catalog group for type {first_req.type.value}",
                requirements=req_list
            ))
        return categories

    def _save_artifacts(self, requirements: List[Requirement], categories: List[RequirementCategory]) -> None:
        reqs_path = self.artifact_dir / "categorized_requirements.json"
        data = {
            "requirements": [r.model_dump() for r in requirements],
            "categories": [c.model_dump() for c in categories]
        }
        with open(reqs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved categorized requirements artifact: {reqs_path}")

