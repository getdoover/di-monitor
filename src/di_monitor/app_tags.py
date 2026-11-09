from pydoover.tags import AnyChange, Boolean, Number, String, Tags


class DiMonitorTags(Tags):
    #: Last valid reading of the monitored input (None until one arrives).
    di_state = Boolean(default=None, live=True, log_on=AnyChange())
    #: False while the monitored input (or the arm input) cannot be read.
    di_read_ok = Boolean(default=True, live=True, log_on=AnyChange())
    #: Whether the alarm logic is running (always True without an arm input).
    armed = Boolean(default=True, live=True, log_on=AnyChange())
    alarm_active = Boolean(default=False, live=True, log_on=AnyChange())
    #: Seconds the input has been continuously active (0 when not).
    active_seconds = Number(default=0, live=True)
    #: Persisted in tag_values, so it survives restarts.
    trip_count = Number(default=0)
    #: Epoch milliseconds of the last trip (None if never tripped).
    last_trip_at = Number(default=None)
    status = String(default="Starting", live=True)

    # UI helpers
    warning_text = String(default="", live=True)
    warning_hidden = Boolean(default=True, live=True)
    arm_hidden = Boolean(default=True)
