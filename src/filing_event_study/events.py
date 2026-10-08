from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo


EASTERN = ZoneInfo("America/New_York")


def map_to_session(accepted_utc: str, sessions: list[str]) -> tuple[str | None, str]:
    """Map a filing to the first clean daily session or return an exclusion reason."""
    timestamp = datetime.fromisoformat(accepted_utc.replace("Z", "+00:00")).astimezone(EASTERN)
    local_day = timestamp.date().isoformat()
    clock = timestamp.time().replace(tzinfo=None)
    if time(9, 30) <= clock < time(16, 0) and local_day in sessions:
        return None, "accepted during regular session; daily bars cannot isolate reaction"
    if clock >= time(16, 0):
        session = next((s for s in sessions if s > local_day), None)
        return (session, "after close mapped to next observed session") if session else (None, "no later price session")
    session = next((s for s in sessions if s >= local_day), None)
    return (session, "pre-open/non-session filing mapped to next observed session") if session else (None, "no later price session")


def cumulative_abnormal_return(prices: dict[str, float], benchmark: dict[str, float], sessions: list[str], event_session: str, window: int) -> float:
    if window < 0:
        raise ValueError("window must be nonnegative")
    center = sessions.index(event_session)
    first = center - window
    last = center + window
    if first < 1 or last >= len(sessions):
        raise ValueError("event does not have a complete requested return window")
    car = 0.0
    for idx in range(first, last + 1):
        today, yesterday = sessions[idx], sessions[idx - 1]
        if min(prices[today], prices[yesterday], benchmark[today], benchmark[yesterday]) <= 0:
            raise ValueError("close prices must be positive")
        import math
        car += math.log(prices[today] / prices[yesterday]) - math.log(benchmark[today] / benchmark[yesterday])
    return car
