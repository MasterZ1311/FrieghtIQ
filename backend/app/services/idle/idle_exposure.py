"""
Idle Exposure Service
Calculates potential or observed idle duration based on confirmed availability
and subsequent employment milestones.

STRICT DATA INTEGRITY:
Potential Idle Days = Next Employment Time - Available Time
Only calculate if both values are supported.
Otherwise: idle_days = None (UNKNOWN).
Never substitute zero.
"""
from typing import Optional, Tuple
from datetime import datetime, timezone


class IdleExposureService:
    @staticmethod
    def calculate_idle_days(
        available_time: Optional[datetime],
        next_employment_time: Optional[datetime]
    ) -> Tuple[Optional[float], str]:
        """
        Calculates potential idle duration in days.
        Returns:
            (idle_days, explanation)
            If either timestamp is missing, returns (None, 'UNKNOWN').
        """
        if available_time is None and next_employment_time is None:
            return (
                None,
                "Both availability date and next employment date are unrecorded."
            )
        if available_time is None:
            return (
                None,
                "Vessel open/availability date is unrecorded."
            )
        if next_employment_time is None:
            return (
                None,
                "Subsequent fixture or employment date is unknown."
            )

        # Normalize timezones
        avail_dt = available_time if available_time.tzinfo else available_time.replace(tzinfo=timezone.utc)
        next_dt = next_employment_time if next_employment_time.tzinfo else next_employment_time.replace(tzinfo=timezone.utc)

        delta_seconds = (next_dt - avail_dt).total_seconds()
        days = round(delta_seconds / 86400.0, 2)

        if days < 0:
            return (
                0.0,
                f"Negative idle exposure ({days} days): Next employment commences before vessel availability."
            )

        return (
            days,
            f"Calculated idle exposure window: {days} days between {avail_dt.strftime('%Y-%m-%d')} and {next_dt.strftime('%Y-%m-%d')}."
        )
