"""
Publishing Date, Time, and Queue Scheduler.
Implements Module 6 Part J (Nodes 24 & 25) of the Agentic AI Video Creation System.
Handles explicit timezones, persistent job state, and publication triggers.
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import zoneinfo

from .config import Config

logger = logging.getLogger(__name__)

class PublishScheduler:
    """Manages publishing schedule times and persistent job states."""

    @classmethod
    def get_tz(cls, tz_name: Optional[str] = None):
        """Resolves zoneinfo timezone safely."""
        name = tz_name or Config.DEFAULT_TIMEZONE
        try:
            return zoneinfo.ZoneInfo(name)
        except Exception:
            return zoneinfo.ZoneInfo("UTC")

    @classmethod
    def parse_schedule_time(
        cls,
        publish_date: Optional[str] = None,
        publish_time: Optional[str] = None,
        raw_text: Optional[str] = None,
        timezone_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses date and time strings or natural language prompt snippets into an ISO timestamp.
        """
        tz = cls.get_tz(timezone_str)
        now = datetime.now(tz)

        target_dt = None

        # 1. Structured date + time: e.g. 2026-09-05 + 19:00
        if publish_date and publish_time:
            clean_date = publish_date.strip()
            clean_time = publish_time.strip()
            # If 12-hour format with AM/PM
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(f"{clean_date} {clean_time}", fmt)
                    target_dt = dt.replace(tzinfo=tz)
                    break
                except ValueError:
                    pass

        # 2. Extract from natural language in prompt if not provided
        if not target_dt and raw_text:
            text = raw_text.lower()
            hour = 19
            minute = 0
            
            # Match time e.g. "at 7:00 pm", "7 pm", "19:00"
            t_match = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text)
            if t_match:
                h = int(t_match.group(1))
                m = int(t_match.group(2)) if t_match.group(2) else 0
                meridiem = t_match.group(3)
                if meridiem == "pm" and h < 12:
                    h += 12
                elif meridiem == "am" and h == 12:
                    h = 0
                hour, minute = h, m

            days_ahead = 0
            if "tomorrow" in text:
                days_ahead = 1
            elif "in 2 days" in text:
                days_ahead = 2

            scheduled_date = (now + timedelta(days=days_ahead)).date()
            target_dt = datetime(
                year=scheduled_date.year,
                month=scheduled_date.month,
                day=scheduled_date.day,
                hour=hour,
                minute=minute,
                second=0,
                tzinfo=tz
            )

        # Default fallback: 1 hour from now
        if not target_dt:
            target_dt = now + timedelta(hours=1)

        wait_seconds = max(0, int((target_dt - now).total_seconds()))

        return {
            "scheduled_iso": target_dt.isoformat(),
            "publish_date": target_dt.strftime("%Y-%m-%d"),
            "publish_time": target_dt.strftime("%H:%M:%S"),
            "timezone": str(tz),
            "wait_seconds": wait_seconds,
            "is_past": wait_seconds == 0
        }

    @classmethod
    def save_scheduled_job(cls, job_id: str, job_data: Dict[str, Any]) -> None:
        """Persists job metadata to disk."""
        store_path = Config.SCHEDULE_STORE_FILE
        store_path.parent.mkdir(parents=True, exist_ok=True)
        jobs = {}
        if store_path.exists():
            try:
                with open(store_path, "r", encoding="utf-8") as f:
                    jobs = json.load(f)
            except Exception:
                jobs = {}

        jobs[job_id] = job_data
        with open(store_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2)
        logger.info(f"Persisted scheduled job {job_id} to {store_path}")

    @classmethod
    def get_pending_jobs(cls) -> Dict[str, Any]:
        """Loads all stored jobs from disk."""
        store_path = Config.SCHEDULE_STORE_FILE
        if not store_path.exists():
            return {}
        try:
            with open(store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


if __name__ == "__main__":
    res = PublishScheduler.parse_schedule_time(raw_text="publish tomorrow at 7:00 PM")
    print("Schedule parsed:\n", json.dumps(res, indent=2))
