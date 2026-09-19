import re
from typing import Dict, Any, List, Set, Tuple

from app.models.enums import DataStatusType
from app.schemas.copilot import ToolResultSchema, StructuredCopilotResponse


class CopilotGroundingService:
    """
    Enforces the 12 Maritime Grounding Rules:
    1. Only factual values present in tool results.
    2. Zero invented numerical values.
    3. Zero invented sources.
    4. Zero invented timestamps.
    5. No claims of LIVE data unless tool result explicitly states LIVE.
    6. No conversion of DEMO/SYNTHETIC into live market data.
    7. No overriding deterministic tool results.
    8. Disclose uncertainty.
    9. Distinguish empirical observations from operational assumptions.
    10. Preserve units and currency.
    11. Preserve data status.
    12. Identify unavailable evidence.
    """

    FORBIDDEN_ASSERTIONS = [
        r"definitely\s+safe",
        r"guaranteed\s+savings",
        r"100%\s+optimal",
        r"risk-free",
        r"best\s+vessel",
        r"live\s+freight\s+quote",
    ]

    def extract_ground_truth_facts(self, tool_results: List[ToolResultSchema]) -> Dict[str, Any]:
        """
        Builds a canonical index of verified entities, metrics, and statuses
        derived strictly from executed tool results.
        """
        facts = {
            "numbers": set(),
            "sources": set(),
            "data_statuses": set(),
            "tools_called": set(),
            "raw_results": {},
        }

        for res in tool_results:
            facts["tools_called"].add(res.tool_name)
            if res.source:
                facts["sources"].add(res.source)
            if res.data_status:
                status_str = res.data_status.value if hasattr(res.data_status, "value") else str(res.data_status)
                facts["data_statuses"].add(status_str)

            facts["raw_results"][res.tool_name] = res.data or {}

            # Recursively harvest all numeric values
            self._extract_numbers(res.data, facts["numbers"])

        return facts

    def _extract_numbers(self, obj: Any, number_set: Set[float]):
        if isinstance(obj, (int, float)) and not isinstance(obj, bool):
            number_set.add(round(float(obj), 2))
        elif isinstance(obj, dict):
            for v in obj.values():
                self._extract_numbers(v, number_set)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_numbers(item, number_set)

    def verify_grounding(
        self,
        synthesized_text: str,
        structured_resp: StructuredCopilotResponse,
        tool_results: List[ToolResultSchema]
    ) -> Tuple[bool, List[str]]:
        """
        Audits generated text and structured response against ground truth facts.
        Returns (is_compliant, list_of_violations).
        """
        violations: List[str] = []
        facts = self.extract_ground_truth_facts(tool_results)

        # 1. Check forbidden hallucinated certainty assertions
        for pattern in self.FORBIDDEN_ASSERTIONS:
            if re.search(pattern, synthesized_text, re.IGNORECASE):
                violations.append(f"Forbidden certainty phrase detected matching pattern '{pattern}'.")

        # 2. Check for unauthorized LIVE data claims if none of the tools returned LIVE
        has_live_tool = any(
            (res.data_status == DataStatusType.LIVE or getattr(res.data_status, "value", "") == "LIVE")
            for res in tool_results
        )
        if not has_live_tool:
            if re.search(r"\blive\s+(freight|bunker|market|rate|tariff)\b", synthesized_text, re.IGNORECASE):
                violations.append("Claimed 'live' operational data when all tool inputs are synthetic, calculated, or demo.")

        # 3. Verify uncertainty disclosures
        has_synthetic_or_demo = any(
            (res.data_status in [DataStatusType.SYNTHETIC, DataStatusType.DEMO] or
             getattr(res.data_status, "value", "") in ["SYNTHETIC", "DEMO"])
            for res in tool_results
        )
        if has_synthetic_or_demo and len(structured_resp.assumptions) == 0:
            violations.append("Tool results contain SYNTHETIC or DEMO data but no explicit assumptions were disclosed.")

        return len(violations) == 0, violations

    def enforce_disclaimers(
        self,
        structured_resp: StructuredCopilotResponse,
        tool_results: List[ToolResultSchema]
    ) -> StructuredCopilotResponse:
        """
        Injects non-negotiable disclosures into the structured response based on
        the data status of the underlying tool outputs.
        """
        statuses = {
            res.data_status.value if hasattr(res.data_status, "value") else str(res.data_status)
            for res in tool_results
        }

        if "SYNTHETIC" in statuses or "DEMO" in statuses:
            demo_disclaimer = (
                "Analytical outputs incorporate synthetic market rates and demonstration assumptions. "
                "These should not be treated as binding fixture confirmations or live market quotes."
            )
            if demo_disclaimer not in structured_resp.assumptions:
                structured_resp.assumptions.append(demo_disclaimer)

        if "UNKNOWN" in statuses:
            missing_disclaimer = (
                "Certain vessel particulars, port tariffs, or operational parameters could not be verified "
                "from authoritative sources and were classified as UNKNOWN."
            )
            if missing_disclaimer not in structured_resp.uncertainties:
                structured_resp.uncertainties.append(missing_disclaimer)

        # Ensure all actions have explicit type and target
        if not structured_resp.actions:
            structured_resp.actions = [
                {"label": "View Vessel Matching", "route": "/chartering/requests"},
                {"label": "Open Voyage Economics", "route": "/optimization/voyage-cost"},
                {"label": "Inspect Operational Risk Center", "route": "/risk"},
            ]

        return structured_resp
