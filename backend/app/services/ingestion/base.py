from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.models.enums import DataStatusType


class BaseDataAdapter(ABC):
    """
    Standard interface for all FREIGHT IQ ingestion adapters.
    Ensures verifiable data provenance, unit conversion, and status preservation.
    """

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def data_status(self) -> DataStatusType:
        pass

    @abstractmethod
    def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetches raw observations from the underlying data source."""
        pass

    @abstractmethod
    def validate(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates schemas, ranges, and nulls in raw payloads."""
        pass

    @abstractmethod
    def normalize(self, valid_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standardizes units, timestamps, and currency."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Returns adapter status, freshness, record count, and errors."""
        pass
