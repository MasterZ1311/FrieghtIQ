from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.enums import CostComponentType, DataStatusType


class PortCostProvider(ABC):
    """
    Abstract interface for port disbursement and tariff calculations.
    """
    @abstractmethod
    def calculate_port_disbursement(
        self,
        port_unlocode: str,
        port_name: str,
        operation_type: str, # "LOAD" or "DISCHARGE"
        cargo_tonnage_mt: float,
        vessel_grt: Optional[float] = None,
        vessel_dwt: Optional[float] = None,
        berth_hours: float = 48.0,
        tug_count: int = 2
    ) -> Dict[str, Any]:
        pass


class PublicPortTariffAdapter(PortCostProvider):
    """
    Calculates port charges from official Port Trust Scale of Rates (SOR)
    for major Indian East Coast ports and Australian export terminals.
    Preserves document references, effective dates, and published currency rates.
    """

    TARIFF_SCHEDULES: Dict[str, Dict[str, Any]] = {
        # Paradip Port Trust (PPT) - Major Coal Discharge Terminal
        "INPRT": {
            "authority": "Paradip Port Authority (PPA) Scale of Rates (SOR)",
            "effective_date": "2025-04-01",
            "currency": "USD",
            "port_dues_per_grt": 0.44, # Coastal/Foreign blended rate
            "berth_hire_per_grt_per_hour": 0.0034,
            "pilotage_per_grt": 0.92, # Includes pilotage & 2 tug assistance
            "tug_hire_per_tug_hour": 450.0,
            "cargo_handling_per_mt": 3.10, # Mechanized coal handling / stackyard
            "port_environment_cess_usd": 1200.0,
            "agency_sundries_usd": 4500.0,
            "data_status": DataStatusType.PUBLIC,
        },
        # Visakhapatnam Port Trust (VPA)
        "INVTZ": {
            "authority": "Visakhapatnam Port Authority (VPA) SOR",
            "effective_date": "2025-04-01",
            "currency": "USD",
            "port_dues_per_grt": 0.41,
            "berth_hire_per_grt_per_hour": 0.0031,
            "pilotage_per_grt": 0.86,
            "tug_hire_per_tug_hour": 420.0,
            "cargo_handling_per_mt": 2.85,
            "port_environment_cess_usd": 1000.0,
            "agency_sundries_usd": 4000.0,
            "data_status": DataStatusType.PUBLIC,
        },
        # Haldia Dock Complex (SMP Kolkata) - Riverine navigation
        "INHAL": {
            "authority": "Syama Prasad Mookerjee Port Kolkata - HDC SOR",
            "effective_date": "2025-04-01",
            "currency": "USD",
            "port_dues_per_grt": 0.52, # Higher due to dredging surcharge
            "berth_hire_per_grt_per_hour": 0.0038,
            "pilotage_per_grt": 1.15, # River pilotage from Sandheads
            "tug_hire_per_tug_hour": 520.0,
            "cargo_handling_per_mt": 3.40,
            "port_environment_cess_usd": 1400.0,
            "agency_sundries_usd": 4800.0,
            "data_status": DataStatusType.PUBLIC,
        },
        # Dhamra Port (DPCL - Adani) - Private deep draft
        "INDHM": {
            "authority": "Dhamra Port Company Ltd Published Commercial Tariff",
            "effective_date": "2025-06-01",
            "currency": "USD",
            "port_dues_per_grt": 0.38,
            "berth_hire_per_grt_per_hour": 0.0029,
            "pilotage_per_grt": 0.82,
            "tug_hire_per_tug_hour": 400.0,
            "cargo_handling_per_mt": 2.70,
            "port_environment_cess_usd": 850.0,
            "agency_sundries_usd": 3800.0,
            "data_status": DataStatusType.PUBLIC,
        },
        # Port of Newcastle (PWCS / NCIG) - Primary Australian Coal Load Terminal
        "AUNCY": {
            "authority": "Port of Newcastle Schedule of Port Charges",
            "effective_date": "2025-07-01",
            "currency": "USD",
            "port_dues_per_grt": 0.42, # Converted AUD to USD
            "berth_hire_per_grt_per_hour": 0.0025,
            "pilotage_per_grt": 0.55, # Port Authority of NSW
            "tug_hire_per_tug_hour": 650.0,
            "cargo_handling_per_mt": 0.95, # Terminal wharfage / loader fee
            "port_environment_cess_usd": 1500.0,
            "agency_sundries_usd": 6500.0,
            "data_status": DataStatusType.PUBLIC,
        },
        # Dalrymple Bay Coal Terminal (DBCT) / Hay Point
        "AUDBY": {
            "authority": "North Queensland Bulk Ports Schedule of Dues",
            "effective_date": "2025-07-01",
            "currency": "USD",
            "port_dues_per_grt": 0.39,
            "berth_hire_per_grt_per_hour": 0.0022,
            "pilotage_per_grt": 0.52,
            "tug_hire_per_tug_hour": 620.0,
            "cargo_handling_per_mt": 0.88,
            "port_environment_cess_usd": 1200.0,
            "agency_sundries_usd": 6000.0,
            "data_status": DataStatusType.PUBLIC,
        },
    }

    def calculate_port_disbursement(
        self,
        port_unlocode: str,
        port_name: str,
        operation_type: str,
        cargo_tonnage_mt: float,
        vessel_grt: Optional[float] = None,
        vessel_dwt: Optional[float] = None,
        berth_hours: float = 48.0,
        tug_count: int = 2
    ) -> Dict[str, Any]:
        key = port_unlocode.upper().strip()
        schedule = self.TARIFF_SCHEDULES.get(key)
        if not schedule:
            # Fallback to name search
            for code, sched in self.TARIFF_SCHEDULES.items():
                if port_name.upper() in sched["authority"].upper() or code in port_name.upper():
                    schedule = sched
                    key = code
                    break

        if not schedule:
            return {
                "port_unlocode": port_unlocode,
                "port_name": port_name,
                "is_supported": False,
                "total_port_cost_usd": 0.0,
                "data_status": DataStatusType.UNKNOWN,
                "explanation": f"Official tariff schedule not available for {port_name} ({port_unlocode})."
            }

        # Estimate GRT from DWT if GRT missing (standard bulk carrier ratio ~0.55 - 0.60 GRT/DWT)
        effective_grt = vessel_grt
        grt_assumption = "Actual Vessel Registered Gross Tonnage"
        if not effective_grt or effective_grt <= 0:
            if vessel_dwt and vessel_dwt > 0:
                effective_grt = round(vessel_dwt * 0.58, 0)
                grt_assumption = f"Approximated GRT ({effective_grt:,.0f}) from vessel Summer DWT ({vessel_dwt:,.0f} MT) @ 0.58 ratio"
            else:
                effective_grt = 45000.0 # Benchmark Panamax GRT
                grt_assumption = "Benchmark Panamax GRT (45,000) applied in absence of vessel particulars"

        # Itemized fee calculations
        port_dues = round(effective_grt * schedule["port_dues_per_grt"], 2)
        berth_hire = round(effective_grt * schedule["berth_hire_per_grt_per_hour"] * max(12.0, berth_hours), 2)
        pilotage_towage = round(effective_grt * schedule["pilotage_per_grt"] + (schedule["tug_hire_per_tug_hour"] * tug_count * 4.0), 2)
        cargo_handling = round(cargo_tonnage_mt * schedule["cargo_handling_per_mt"], 2)
        agency_sundries = round(schedule["agency_sundries_usd"] + schedule["port_environment_cess_usd"], 2)

        total_cost = round(port_dues + berth_hire + pilotage_towage + cargo_handling + agency_sundries, 2)

        components = [
            {
                "component_type": CostComponentType.PORT_DUES,
                "amount": port_dues,
                "unit": "USD/GRT",
                "quantity": effective_grt,
                "rate": schedule["port_dues_per_grt"],
                "source": schedule["authority"],
                "data_status": schedule["data_status"]
            },
            {
                "component_type": CostComponentType.BERTH_CHARGES,
                "amount": berth_hire,
                "unit": "USD/GRT/HR",
                "quantity": effective_grt * max(12.0, berth_hours),
                "rate": schedule["berth_hire_per_grt_per_hour"],
                "source": schedule["authority"],
                "data_status": schedule["data_status"]
            },
            {
                "component_type": CostComponentType.PILOTAGE_TOWAGE,
                "amount": pilotage_towage,
                "unit": "USD",
                "quantity": 1.0,
                "rate": pilotage_towage,
                "source": schedule["authority"],
                "data_status": schedule["data_status"]
            },
            {
                "component_type": CostComponentType.CARGO_HANDLING,
                "amount": cargo_handling,
                "unit": "USD/MT",
                "quantity": cargo_tonnage_mt,
                "rate": schedule["cargo_handling_per_mt"],
                "source": schedule["authority"],
                "data_status": schedule["data_status"]
            },
            {
                "component_type": CostComponentType.AGENCY_SUNDRIES,
                "amount": agency_sundries,
                "unit": "USD",
                "quantity": 1.0,
                "rate": agency_sundries,
                "source": schedule["authority"],
                "data_status": schedule["data_status"]
            },
        ]

        return {
            "port_unlocode": key,
            "port_name": port_name,
            "operation_type": operation_type,
            "authority": schedule["authority"],
            "effective_date": schedule["effective_date"],
            "currency": schedule["currency"],
            "total_port_cost_usd": total_cost,
            "cost_per_mt": round(total_cost / max(1.0, cargo_tonnage_mt), 2),
            "effective_grt": effective_grt,
            "grt_assumption": grt_assumption,
            "components": components,
            "data_status": schedule["data_status"],
            "is_supported": True,
            "explanation": f"Disbursement account for {operation_type} at {port_name} calculated per {schedule['authority']} ({schedule['effective_date']})."
        }


class LicensedPortCostAdapter(PortCostProvider):
    """
    Adapter for third-party commercial port disbursement account (PDA) integrations.
    """
    def calculate_port_disbursement(
        self,
        port_unlocode: str,
        port_name: str,
        operation_type: str,
        cargo_tonnage_mt: float,
        vessel_grt: Optional[float] = None,
        vessel_dwt: Optional[float] = None,
        berth_hours: float = 48.0,
        tug_count: int = 2
    ) -> Dict[str, Any]:
        return {
            "port_unlocode": port_unlocode,
            "port_name": port_name,
            "is_supported": False,
            "total_port_cost_usd": 0.0,
            "data_status": DataStatusType.LICENSED,
            "explanation": "Commercial licensed PDA API is not configured. Falling back to public scale of rates."
        }


class SyntheticPortCostAdapter(PortCostProvider):
    """
    Synthetic parametric disbursement model for unrecorded minor or foreign terminals.
    Explicitly labeled as SYNTHETIC.
    """
    def calculate_port_disbursement(
        self,
        port_unlocode: str,
        port_name: str,
        operation_type: str,
        cargo_tonnage_mt: float,
        vessel_grt: Optional[float] = None,
        vessel_dwt: Optional[float] = None,
        berth_hours: float = 48.0,
        tug_count: int = 2
    ) -> Dict[str, Any]:
        grt = vessel_grt or (vessel_dwt * 0.58 if vessel_dwt else 45000.0)
        dues = grt * 0.40
        berth = grt * 0.0030 * max(12.0, berth_hours)
        pilot = grt * 0.75 + (500.0 * tug_count * 4.0)
        handling = cargo_tonnage_mt * (2.50 if operation_type == "DISCHARGE" else 1.20)
        agency = 4000.0
        total = round(dues + berth + pilot + handling + agency, 2)

        return {
            "port_unlocode": port_unlocode,
            "port_name": port_name,
            "operation_type": operation_type,
            "authority": "FREIGHT IQ Synthetic Parametric Port Cost Model",
            "effective_date": "2026-01-01",
            "currency": "USD",
            "total_port_cost_usd": total,
            "cost_per_mt": round(total / max(1.0, cargo_tonnage_mt), 2),
            "effective_grt": grt,
            "grt_assumption": "Parametric baseline",
            "components": [
                {"component_type": CostComponentType.PORT_DUES, "amount": dues, "unit": "USD", "quantity": 1.0, "rate": dues, "source": "Synthetic Parametric", "data_status": DataStatusType.SYNTHETIC},
                {"component_type": CostComponentType.BERTH_CHARGES, "amount": berth, "unit": "USD", "quantity": 1.0, "rate": berth, "source": "Synthetic Parametric", "data_status": DataStatusType.SYNTHETIC},
                {"component_type": CostComponentType.PILOTAGE_TOWAGE, "amount": pilot, "unit": "USD", "quantity": 1.0, "rate": pilot, "source": "Synthetic Parametric", "data_status": DataStatusType.SYNTHETIC},
                {"component_type": CostComponentType.CARGO_HANDLING, "amount": handling, "unit": "USD", "quantity": 1.0, "rate": handling, "source": "Synthetic Parametric", "data_status": DataStatusType.SYNTHETIC},
                {"component_type": CostComponentType.AGENCY_SUNDRIES, "amount": agency, "unit": "USD", "quantity": 1.0, "rate": agency, "source": "Synthetic Parametric", "data_status": DataStatusType.SYNTHETIC},
            ],
            "data_status": DataStatusType.SYNTHETIC,
            "is_supported": True,
            "explanation": f"Synthetic parametric port disbursement calculated for unrecorded port {port_name}."
        }


class PortCostService:
    """
    High-level port cost orchestrator evaluating combined origin (load)
    and destination (discharge) port expenses.
    """
    def __init__(self, provider: Optional[PortCostProvider] = None):
        self.public_provider = PublicPortTariffAdapter()
        self.synthetic_provider = SyntheticPortCostAdapter()
        self.provider = provider or self.public_provider

    def calculate_voyage_port_costs(
        self,
        origin_unlocode: str,
        origin_name: str,
        destination_unlocode: str,
        destination_name: str,
        cargo_quantity_mt: float,
        vessel_grt: Optional[float] = None,
        vessel_dwt: Optional[float] = None,
        load_berth_hours: float = 48.0,
        discharge_berth_hours: float = 60.0,
    ) -> Dict[str, Any]:
        # Evaluate Load Port
        load_res = self.provider.calculate_port_disbursement(
            port_unlocode=origin_unlocode,
            port_name=origin_name,
            operation_type="LOAD",
            cargo_tonnage_mt=cargo_quantity_mt,
            vessel_grt=vessel_grt,
            vessel_dwt=vessel_dwt,
            berth_hours=load_berth_hours
        )
        if not load_res.get("is_supported"):
            load_res = self.synthetic_provider.calculate_port_disbursement(
                port_unlocode=origin_unlocode,
                port_name=origin_name,
                operation_type="LOAD",
                cargo_tonnage_mt=cargo_quantity_mt,
                vessel_grt=vessel_grt,
                vessel_dwt=vessel_dwt,
                berth_hours=load_berth_hours
            )

        # Evaluate Discharge Port
        disch_res = self.provider.calculate_port_disbursement(
            port_unlocode=destination_unlocode,
            port_name=destination_name,
            operation_type="DISCHARGE",
            cargo_tonnage_mt=cargo_quantity_mt,
            vessel_grt=vessel_grt,
            vessel_dwt=vessel_dwt,
            berth_hours=discharge_berth_hours
        )
        if not disch_res.get("is_supported"):
            disch_res = self.synthetic_provider.calculate_port_disbursement(
                port_unlocode=destination_unlocode,
                port_name=destination_name,
                operation_type="DISCHARGE",
                cargo_tonnage_mt=cargo_quantity_mt,
                vessel_grt=vessel_grt,
                vessel_dwt=vessel_dwt,
                berth_hours=discharge_berth_hours
            )

        total_port_cost = round(load_res["total_port_cost_usd"] + disch_res["total_port_cost_usd"], 2)
        cost_per_mt = round(total_port_cost / max(1.0, cargo_quantity_mt), 2)

        combined_components = list(load_res.get("components", [])) + list(disch_res.get("components", []))

        # Overall provenance determination
        statuses = [load_res["data_status"], disch_res["data_status"]]
        overall_status = DataStatusType.PUBLIC if all(s == DataStatusType.PUBLIC for s in statuses) else DataStatusType.SYNTHETIC

        return {
            "origin_port": load_res,
            "destination_port": disch_res,
            "total_port_cost_usd": total_port_cost,
            "cost_per_mt": cost_per_mt,
            "components": combined_components,
            "data_status": overall_status,
            "explanation": f"Total port disbursements: {origin_name} (${load_res['total_port_cost_usd']:,.2f}) + {destination_name} (${disch_res['total_port_cost_usd']:,.2f})."
        }
