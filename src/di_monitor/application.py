"""DI Monitor: a hold-time alarm on one Doovit digital input.

Every Poll Period Seconds (default 1 s): read the input (and the arm input, if
one is configured), feed :class:`HoldAlarm`, act on its event, publish tags.
All judgement about timing lives in :mod:`hold_alarm`; this file is the I/O
around it.

Unknown readings: ``fetch_di`` returns ``None`` when the platform interface
request fails. That sample is skipped (the hold timer is neither reset nor
tripped by it) and ``di_read_ok`` goes False.

Disarming: when the arm input leaves its arming level the hold timer resets
and an active alarm clears **without** a ``cleared`` notification. Losing the
arm condition (e.g. the isolator being switched off) is not the fault going
away, so telling people "back to normal" would be misleading; the UI warning
simply disappears and the status reads "Not armed".
"""

from __future__ import annotations

import logging
import time

from pydoover.docker import Application

from .app_config import DiMonitorConfig
from .app_notifications import DiMonitorNotifications
from .app_tags import DiMonitorTags
from .app_ui import DiMonitorUI
from .hold_alarm import AlarmEvent, HoldAlarm

log = logging.getLogger(__name__)


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def format_message(template: str, **values) -> str:
    """``str.format_map`` that leaves unknown placeholders alone and never raises."""
    try:
        return template.format_map(_SafeDict(values))
    except (ValueError, IndexError, AttributeError):
        return template


class DiMonitorApplication(Application):
    config: DiMonitorConfig
    tags: DiMonitorTags
    notifications: DiMonitorNotifications

    config_cls = DiMonitorConfig
    tags_cls = DiMonitorTags
    ui_cls = DiMonitorUI
    notifications_cls = DiMonitorNotifications

    async def setup(self):
        # pydoover's run_app stamps the app key onto every component it knows
        # about after construction — but not onto the notifications set, which
        # was built with ``app_key=None`` and so refused every send with
        # "Application key has not been set" (pydoover <= 1.18.4; station-8,
        # 2026-11-09: the first alarm crash-looped di_monitor_compressor).
        # Fixed upstream in pydoover; harmless once that lands.
        if self.notifications is not None and not self.notifications.app_key:
            self.notifications.app_key = self.app_key

        c = self.config
        self.loop_target_period = float(c.poll_period_seconds.value)
        self.di_name: str = str(c.di_name.value)
        self.di_pin: int = int(c.di_pin.value)
        self.alarm_high: bool = c.alarm_when.value == "high"
        self.hold_seconds: float = float(c.hold_seconds.value)
        self.arm_pin: int | None = (
            int(c.arm_di_pin.value) if c.arm_di_pin.value is not None else None
        )
        self.arm_high: bool = c.arm_di_level.value == "high"
        self.alarm = HoldAlarm(self.hold_seconds, c.renotify_seconds.value)

        await self.tags.arm_hidden.set(self.arm_pin is None)
        log.info(
            "Monitoring %s on DI%d: alarm when %s for %gs%s",
            self.di_name,
            self.di_pin,
            "HIGH" if self.alarm_high else "LOW",
            self.hold_seconds,
            ""
            if self.arm_pin is None
            else f", armed while DI{self.arm_pin} {'HIGH' if self.arm_high else 'LOW'}",
        )

    async def main_loop(self):
        await self.step()

    # ------------------------------------------------------------------
    # One sample
    # ------------------------------------------------------------------

    async def _read_di(self, pin: int) -> bool | None:
        try:
            value = await self.fetch_di(pin)
        except Exception as e:  # noqa: BLE001 - a failed read is just "unknown"
            log.warning("DI%d read failed: %s", pin, e)
            return None
        if isinstance(value, (list, tuple)):
            value = value[0] if len(value) == 1 else None
        return None if value is None else bool(value)

    async def step(self):
        now = time.monotonic()
        di = await self._read_di(self.di_pin)

        armed: bool | None = True
        if self.arm_pin is not None:
            arm_value = (
                di if self.arm_pin == self.di_pin else await self._read_di(self.arm_pin)
            )
            armed = None if arm_value is None else arm_value == self.arm_high

        read_ok = di is not None and armed is not None
        await self.tags.di_read_ok.set(read_ok)
        if di is not None:
            await self.tags.di_state.set(di)
        if armed is not None:
            await self.tags.armed.set(armed)

        if armed is False:
            if self.alarm.reset():
                log.info("%s alarm cleared by disarm (no notification)", self.di_name)
            event = AlarmEvent.NONE
        elif not read_ok:
            event = self.alarm.update(None, now)
        else:
            event = self.alarm.update(di == self.alarm_high, now)

        await self._handle_event(event)
        await self._publish_state(now, di, armed, read_ok)

    async def _handle_event(self, event: AlarmEvent):
        if event is AlarmEvent.NONE:
            return
        if event is AlarmEvent.TRIP:
            count = (self.tags.trip_count.get() or 0) + 1
            await self.tags.trip_count.set(count, log=True)
            await self.tags.last_trip_at.set(int(time.time() * 1000))
            log.warning("%s alarm tripped (trip %d)", self.di_name, count)
        elif event is AlarmEvent.CLEAR:
            log.info("%s alarm cleared", self.di_name)

        if not self.config.notifications_enabled.value:
            return
        if event in (AlarmEvent.TRIP, AlarmEvent.RENOTIFY):
            await self.notifications.alarm.send(self.alarm_text())
        elif event is AlarmEvent.CLEAR and self.config.notify_on_clear.value:
            await self.notifications.cleared.send(self.clear_text())

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    def _message_values(self) -> dict:
        return {
            "di_name": self.di_name,
            "di_pin": self.di_pin,
            "hold_seconds": f"{self.hold_seconds:g}",
            "active_seconds": f"{self.alarm.active_seconds(time.monotonic()):.0f}",
        }

    def alarm_text(self) -> str:
        return format_message(
            str(self.config.alarm_message.value), **self._message_values()
        )

    def clear_text(self) -> str:
        return format_message(
            str(self.config.clear_message.value), **self._message_values()
        )

    def status_text(self, now: float, armed: bool | None, read_ok: bool) -> str:
        if armed is False:
            level = "HIGH" if self.arm_high else "LOW"
            return f"Not armed (DI{self.arm_pin} not {level})"
        if not read_ok:
            return "Input unreadable"
        active = self.alarm.active_seconds(now)
        if self.alarm.tripped:
            return f"ALARM: active {active:.0f} s / hold {self.hold_seconds:g} s"
        if self.alarm.active_since is not None:
            return f"Active {active:.0f} s / hold {self.hold_seconds:g} s"
        return "Normal"

    async def _publish_state(
        self, now: float, di: bool | None, armed: bool | None, read_ok: bool
    ):
        active = self.alarm.tripped
        await self.tags.alarm_active.set(active)
        await self.tags.active_seconds.set(round(self.alarm.active_seconds(now)))
        await self.tags.status.set(self.status_text(now, armed, read_ok))
        await self.tags.warning_hidden.set(not active)
        await self.tags.warning_text.set(self.alarm_text() if active else "")
