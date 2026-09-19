"""
Unified Operational Risk Engine
Coordinates multi-dimensional risk evaluation across Ports, Vessels, and Charter Voyages.

STRICT PRINCIPLES:
- Evaluates real physical and contractual variables:
  - Origin & Destination Congestion (Queue, Berth Occupancy, Demurrage)
  - Origin & Destination Weather (Precipitation bulk stoppage, Wind/Wave pilotage/crane cutoffs)
  - Origin & Destination Tidal Windows & UKC clearances
  - Vessel Laycan Timing & Cancelling Date margins
  - Port Operational & Maintenance Disruptions
  - Data Quality, Freshness, and Missing Field Penalties
- Never returns unverified fake live data; maintains provenance markers.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.enums import RiskType, RiskSeverity
from app.services.risk.weather_service import WeatherRiskService
from app.services.risk.tidal_service import TidalGateScheduler
from app.services.risk.congestion_service import CongestionRiskService
from app.services.risk.operational_risk_service import (
    PortOperationalRiskService,
    TimingRiskService,
    IdleRiskService,
    DataQualityRiskService
)
from app.services.risk.aggregation import RiskAggregationService


class RiskEngine:
    def __init__(
        self,
        weather_service: Optional[WeatherRiskService] = None,
        congestion_service: Optional[CongestionRiskService] = None
    ):
        self.weather_service = weather_service or WeatherRiskService()
        self.congestion_service = congestion_service or CongestionRiskService()

    def evaluate_port_risk(
        self,
        port_id: str,
        port_name: Optional[str] = None,
        vessel_draft_m: Optional[float] = None,
        berth_draft_m: Optional[float] = None,
        cargo_type: Optional[str] = "COKING_COAL",
        vessel_class: Optional[str] = "PANAMAX"
    ) -> Dict[str, Any]:
        """
        Comprehensive operational risk evaluation for a single port.
        """
        # 1. Congestion
        congestion_eval = self.congestion_service.evaluate_congestion_risk(
            port_id=port_id,
            port_name=port_name,
            vessel_class=vessel_class
        )
        congestion_eval["risk_type"] = RiskType.PORT_CONGESTION.value

        # 2. Weather
        weather_eval = self.weather_service.evaluate_weather_risk(
            port_id=port_id,
            port_name=port_name,
            cargo_type=cargo_type
        )
        weather_eval["risk_type"] = RiskType.WEATHER.value

        # 3. Tidal
        tidal_eval = TidalGateScheduler.evaluate_ukc_feasibility(
            vessel_draft_m=vessel_draft_m,
            berth_draft_m=berth_draft_m,
            port_id=port_id,
            port_name=port_name
        )
        # Map tidal status to RiskSeverity
        t_status = tidal_eval.get("status")
        if t_status == "FAIL":
            tidal_sev = RiskSeverity.CRITICAL.value
        elif t_status == "CONDITIONAL":
            tidal_sev = RiskSeverity.MEDIUM.value
        elif t_status == "PASS":
            tidal_sev = RiskSeverity.LOW.value
        else:
            tidal_sev = RiskSeverity.UNKNOWN.value

        tidal_comp = {
            "risk_type": RiskType.TIDAL.value,
            "severity": tidal_sev,
            "status": t_status,
            "tidal_evaluation": tidal_eval,
            "explanations": [tidal_eval["explanation"]] if tidal_eval.get("explanation") else [],
            "mitigations": [tidal_eval["mitigation"]] if tidal_eval.get("mitigation") else []
        }

        # 4. Port Operations Notices
        ops_eval = PortOperationalRiskService.evaluate_port_operations(
            port_id=port_id,
            port_name=port_name
        )
        ops_eval["risk_type"] = RiskType.PORT_OPERATION.value

        # 5. Aggregate components
        components = [congestion_eval, weather_eval, tidal_comp, ops_eval]
        aggregate = RiskAggregationService.aggregate_operational_risks(components)

        return {
            "port_id": port_id,
            "port_name": port_name,
            "overall_severity": aggregate["overall_severity"],
            "primary_drivers": aggregate["primary_drivers"],
            "financial_exposure": aggregate["financial_exposure"],
            "total_delay_hours": aggregate["total_delay_hours"],
            "components": {
                "congestion": congestion_eval,
                "weather": weather_eval,
                "tidal": tidal_comp,
                "operations": ops_eval,
            },
            "explanations": aggregate["explanations"],
            "mitigations": aggregate["mitigations"]
        }

    def evaluate_voyage_risk(
        self,
        origin_port_id: str,
        origin_port_name: Optional[str],
        destination_port_id: str,
        destination_port_name: Optional[str],
        vessel_name: Optional[str] = None,
        vessel_class: Optional[str] = "PANAMAX",
        vessel_draft_m: Optional[float] = None,
        origin_berth_draft_m: Optional[float] = None,
        destination_berth_draft_m: Optional[float] = None,
        cargo_type: Optional[str] = "COKING_COAL",
        eta_origin: Optional[datetime] = None,
        laycan_from: Optional[datetime] = None,
        laycan_to: Optional[datetime] = None,
        charter_hire_usd_per_day: float = 20000.0
    ) -> Dict[str, Any]:
        """
        Full end-to-end voyage operational risk evaluation.
        """
        # 1. Origin Port Risk
        origin_risk = self.evaluate_port_risk(
            port_id=origin_port_id,
            port_name=origin_port_name,
            vessel_draft_m=vessel_draft_m,
            berth_draft_m=origin_berth_draft_m,
            cargo_type=cargo_type,
            vessel_class=vessel_class
        )

        # 2. Destination Port Risk
        dest_risk = self.evaluate_port_risk(
            port_id=destination_port_id,
            port_name=destination_port_name,
            vessel_draft_m=vessel_draft_m,
            berth_draft_m=destination_berth_draft_m,
            cargo_type=cargo_type,
            vessel_class=vessel_class
        )

        # 3. Timing / Laycan Risk at Origin
        timing_eval = TimingRiskService.evaluate_laycan_risk(
            eta=eta_origin,
            laycan_from=laycan_from,
            laycan_to=laycan_to,
            vessel_name=vessel_name
        )
        timing_eval["risk_type"] = RiskType.TIMING.value
        timing_eval["explanations"] = [timing_eval["explanation"]]
        timing_eval["mitigations"] = [timing_eval["mitigation"]]

        # 4. Data Quality Check
        dq_eval = DataQualityRiskService.evaluate_data_quality(
            entity_type="VOYAGE",
            entity_id=f"{origin_port_id}->{destination_port_id}",
            provided_fields={
                "vessel_draft_m": vessel_draft_m,
                "origin_berth_draft_m": origin_berth_draft_m,
                "dest_berth_draft_m": destination_berth_draft_m,
                "eta_origin": eta_origin,
                "laycan_to": laycan_to,
            },
            required_fields=["vessel_draft_m", "origin_berth_draft_m", "dest_berth_draft_m", "eta_origin", "laycan_to"]
        )
        dq_eval["risk_type"] = RiskType.DATA_QUALITY.value
        dq_eval["explanations"] = [dq_eval["explanation"]]
        dq_eval["mitigations"] = [dq_eval["mitigation"]]

        # Collect components
        all_components = [
            origin_risk["components"]["congestion"],
            origin_risk["components"]["weather"],
            origin_risk["components"]["tidal"],
            origin_risk["components"]["operations"],
            dest_risk["components"]["congestion"],
            dest_risk["components"]["weather"],
            dest_risk["components"]["tidal"],
            dest_risk["components"]["operations"],
            timing_eval,
            dq_eval
        ]

        aggregate = RiskAggregationService.aggregate_operational_risks(
            all_components,
            charter_hire_rate_usd_per_day=charter_hire_usd_per_day
        )

        return {
            "origin_port": {
                "id": origin_port_id,
                "name": origin_port_name,
                "risk": origin_risk
            },
            "destination_port": {
                "id": destination_port_id,
                "name": destination_port_name,
                "risk": dest_risk
            },
            "timing_risk": timing_eval,
            "data_quality": dq_eval,
            "overall_severity": aggregate["overall_severity"],
            "primary_drivers": aggregate["primary_drivers"],
            "financial_exposure": aggregate["financial_exposure"],
            "total_delay_hours": aggregate["total_delay_hours"],
            "explanations": aggregate["explanations"],
            "mitigations": aggregate["mitigations"]
        }
