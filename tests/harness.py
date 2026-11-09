"""A real DiMonitorApplication wired to fakes at its edges.

Only what touches the outside world is replaced: ``fetch_di`` (a dict of pin
levels the test sets, ``None`` for a failed read), the tag store, the
notifications channel, and the clock. Everything else is production code.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import di_monitor.application as app_module
from di_monitor.app_config import DiMonitorConfig
from di_monitor.app_notifications import DiMonitorNotifications
from di_monitor.application import DiMonitorApplication

APP_KEY = "di_monitor_1"


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class FakeClock:
    def __init__(self, start: float = 1_700_000_000.0):
        self.now = float(start)
        self._original = None

    def install(self):
        self._original = app_module.time
        app_module.time = SimpleNamespace(
            time=lambda: self.now, monotonic=lambda: self.now
        )
        return self

    def restore(self):
        if self._original is not None:
            app_module.time = self._original
            self._original = None


class Tag:
    def __init__(self, value=None):
        self._value = value
        self.history = []

    def get(self):
        return self._value

    @property
    def value(self):
        return self._value

    async def set(self, value, log=False):
        self._value = value
        self.history.append(value)


class Tags:
    def __init__(self, **initial):
        object.__setattr__(self, "_tags", {})
        for name, value in initial.items():
            self._tags[name] = Tag(value)

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._tags.setdefault(name, Tag())


BASE_CONFIG = {"di_name": "Compressor", "di_pin": 0}


def build_config(**overrides) -> DiMonitorConfig:
    data = dict(BASE_CONFIG)
    data.update(overrides)
    config = DiMonitorConfig()
    config._inject_deployment_config(data)
    return config


class Rig:
    def __init__(self, levels: dict | None = None, trip_count=0, **config_overrides):
        self.clock = FakeClock().install()
        self.levels: dict[int, bool | None] = {0: True, 1: True, 2: False, 3: True}
        if levels:
            self.levels.update(levels)
        self.reads: list[int] = []
        self.sent: list[dict] = []
        self.tags = Tags(trip_count=trip_count)

        app = DiMonitorApplication.__new__(DiMonitorApplication)
        self.app = app
        app.config = build_config(**config_overrides)
        app.tags = self.tags
        app.app_key = APP_KEY
        app.fetch_di = self._fetch_di
        app.send_notification = self._send_notification
        app.notifications = DiMonitorNotifications(APP_KEY, app)
        run(app.setup())

    async def _fetch_di(self, pin):
        self.reads.append(pin)
        value = self.levels.get(pin)
        if isinstance(value, Exception):
            raise value
        return value

    async def _send_notification(self, message, **kwargs):
        self.sent.append({"message": message, **kwargs})

    # --- levers ---------------------------------------------------------

    def set(self, pin: int, value):
        self.levels[pin] = value

    def tick(self, seconds: float = 1.0, steps: int = 1):
        """Run ``steps`` loop iterations, ``seconds`` apart (clock advances first)."""
        for _ in range(steps):
            self.clock.now += seconds
            run(self.app.step())

    def run_for(self, seconds: float):
        self.tick(1.0, int(seconds))

    # --- observations ---------------------------------------------------

    def events(self) -> list[str]:
        return [str(s["topic"]).rsplit("/", 1)[-1] for s in self.sent]

    def tag(self, name):
        return getattr(self.tags, name).value

    def close(self):
        self.clock.restore()
