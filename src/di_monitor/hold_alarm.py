"""A hold-time alarm: trips once a condition has held continuously for a while.

Based on ``4-20ma-sensor``'s ``alarm.Alarm`` but fixing its two traps:

* **renotify <= 0 means never.** The original treats 0 as "re-notify on every
  poll" because ``now - last < 0`` is never true.
* **Clearing is an event of its own.** The original returns ``False`` both for
  "nothing changed" and for "the alarm just cleared", so a caller cannot send
  a cleared notification. :meth:`HoldAlarm.update` returns an
  :class:`AlarmEvent`, and ``CLEAR`` only follows a real ``TRIP``: a blip
  shorter than the hold never produces one.

The class is pure: the caller passes the clock in, so tests drive it with
plain numbers.
"""

from __future__ import annotations

from enum import Enum


class AlarmEvent(Enum):
    NONE = "none"
    TRIP = "trip"
    RENOTIFY = "renotify"
    CLEAR = "clear"


class HoldAlarm:
    """Trip after ``hold_seconds`` of continuous activity.

    Parameters
    ----------
    hold_seconds
        How long the condition must hold, unbroken, before the alarm trips.
        0 trips on the first active sample.
    renotify_seconds
        While tripped, emit ``RENOTIFY`` this often. ``<= 0`` (or ``None``)
        means never: one ``TRIP`` and then silence until it clears.
    """

    def __init__(self, hold_seconds: float, renotify_seconds: float | None = 0.0):
        self.hold_seconds = max(0.0, float(hold_seconds or 0.0))
        self.renotify_seconds = float(renotify_seconds or 0.0)
        self.active_since: float | None = None
        self.tripped = False
        self._last_notified: float | None = None

    def active_seconds(self, now: float) -> float:
        """How long the condition has held so far (0 when it is not active)."""
        if self.active_since is None:
            return 0.0
        return max(0.0, now - self.active_since)

    def update(self, active: bool | None, now: float) -> AlarmEvent:
        """Feed one sample.

        ``active=None`` means the input could not be read: the sample is
        skipped. The hold timer is neither reset nor advanced by the sample
        itself and nothing trips on it (wall time still passes, so a valid
        active reading afterwards counts from the original start).
        """
        if active is None:
            return AlarmEvent.NONE

        if not active:
            self.active_since = None
            if self.tripped:
                self.tripped = False
                self._last_notified = None
                return AlarmEvent.CLEAR
            return AlarmEvent.NONE

        if self.active_since is None:
            self.active_since = now

        if not self.tripped:
            if now - self.active_since >= self.hold_seconds:
                self.tripped = True
                self._last_notified = now
                return AlarmEvent.TRIP
            return AlarmEvent.NONE

        if (
            self.renotify_seconds > 0
            and self._last_notified is not None
            and now - self._last_notified >= self.renotify_seconds
        ):
            self._last_notified = now
            return AlarmEvent.RENOTIFY
        return AlarmEvent.NONE

    def reset(self) -> bool:
        """Forget everything without emitting an event.

        Used when the alarm is disarmed. Returns whether the alarm had been
        tripped, so the caller can log it.
        """
        was_tripped = self.tripped
        self.active_since = None
        self.tripped = False
        self._last_notified = None
        return was_tripped
