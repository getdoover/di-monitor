import logging

log = logging.getLogger(__name__)

def seconds_to_hms(dt_sec: float) -> str:
    neg = dt_sec < 0
    s = abs(dt_sec)

    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(round(s % 60))  # round to nearest second

    # fix rounding carry (e.g., 59.9 → 60)
    if sec == 60:
        sec = 0
        m += 1
    if m == 60:
        m = 0
        h += 1

    return f"{'-' if neg else ''}{h:02d}:{m:02d}:{sec:02d}"