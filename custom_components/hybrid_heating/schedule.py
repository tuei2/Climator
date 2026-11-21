"""Week schedule with two profiles (workday / weekend) of comfort blocks."""

from __future__ import annotations

from datetime import datetime, time, timedelta

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

DEFAULT_SCHEDULE = {
    "profiles": {
        "workday": [
            {"start": "06:45", "end": "08:30", "temp": 20.0, "enabled": True},
            {"start": "16:30", "end": "22:30", "temp": 20.5, "enabled": True},
        ],
        "weekend": [
            {"start": "08:00", "end": "23:00", "temp": 20.5, "enabled": True},
        ],
    },
    "days": {"mon": "workday", "tue": "workday", "wed": "workday", "thu": "workday",
             "fri": "workday", "sat": "weekend", "sun": "weekend"},
    "weekend_enabled": True,
}


def _t(v: str) -> time:
    h, m = str(v).split(":")[:2]
    return time(int(h) % 24, int(m))


def validate(schedule: dict) -> dict:
    """Normalise a schedule coming from the UI; raises ValueError when invalid."""
    out = {"profiles": {}, "days": {}, "weekend_enabled": bool(schedule.get("weekend_enabled", True))}
    for name in ("workday", "weekend"):
        blocks = []
        for b in schedule.get("profiles", {}).get(name, [])[:6]:
            start, end = _t(b["start"]), _t(b["end"])
            temp = float(b["temp"])
            if not 5 <= temp <= 28:
                raise ValueError("temperature out of range")
            blocks.append({"start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
                           "temp": round(temp * 2) / 2, "enabled": bool(b.get("enabled", True))})
        out["profiles"][name] = sorted(blocks, key=lambda b: b["start"])
    for d in DAYS:
        p = schedule.get("days", {}).get(d, DEFAULT_SCHEDULE["days"][d])
        out["days"][d] = p if p in ("workday", "weekend") else "workday"
    return out


def _blocks_for(schedule: dict, day: datetime) -> list:
    name = schedule["days"][DAYS[day.weekday()]]
    if name == "weekend" and not schedule.get("weekend_enabled", True):
        name = "workday"
    return [b for b in schedule["profiles"].get(name, []) if b.get("enabled", True)]


def comfort_at(schedule: dict, now: datetime) -> float | None:
    """Comfort temperature at this moment, or None outside comfort blocks."""
    for offset in (0, -1):  # blocks from yesterday may run past midnight
        day = now + timedelta(days=offset)
        for b in _blocks_for(schedule, day):
            s, e = _t(b["start"]), _t(b["end"])
            start = day.replace(hour=s.hour, minute=s.minute, second=0, microsecond=0)
            end = day.replace(hour=e.hour, minute=e.minute, second=0, microsecond=0)
            if end <= start:
                end += timedelta(days=1)
            if start <= now < end:
                return float(b["temp"])
    return None


def next_block(schedule: dict, now: datetime, within_days: int = 2):
    """(start datetime, temp) of the next comfort block that starts after now."""
    best = None
    for offset in range(within_days + 1):
        day = now + timedelta(days=offset)
        for b in _blocks_for(schedule, day):
            s = _t(b["start"])
            start = day.replace(hour=s.hour, minute=s.minute, second=0, microsecond=0)
            if start > now and (best is None or start < best[0]):
                best = (start, float(b["temp"]))
    return best
