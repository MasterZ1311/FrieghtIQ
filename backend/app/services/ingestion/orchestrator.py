from typing import Dict, Any, List
from app.services.ingestion.adapters import (
    FreightAdapter,
    AISAdapter,
    WeatherAdapter,
    TideAdapter,
    CongestionAdapter,
    PortConstraintAdapter,
    BunkerAdapter,
)


class DataIngestionOrchestrator:
    """
    Centralized data ingestion manager and pipeline health monitor for FREIGHT IQ.
    Coordinates all 7 adapters and reports real-time data status and provenance.
    """

    def __init__(self):
        self.adapters = [
            FreightAdapter(),
            AISAdapter(),
            WeatherAdapter(),
            TideAdapter(),
            CongestionAdapter(),
            PortConstraintAdapter(),
            BunkerAdapter(),
        ]

    def get_all_adapter_health(self) -> Dict[str, Any]:
        metas = [a.get_metadata() for a in self.adapters]
        total_errors = sum(m.get("error_count", 0) for m in metas)
        active = sum(1 for m in metas if m.get("status") != "OFFLINE")

        return {
            "overall_status": "HEALTHY" if total_errors == 0 else "DEGRADED",
            "total_adapters": len(self.adapters),
            "active_adapters": active,
            "adapters": metas,
        }
