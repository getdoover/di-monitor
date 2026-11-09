"""HoldAlarm on its own: pure numbers, no app."""

from di_monitor.hold_alarm import AlarmEvent, HoldAlarm

N, TRIP, RENOTIFY, CLEAR = (
    AlarmEvent.NONE,
    AlarmEvent.TRIP,
    AlarmEvent.RENOTIFY,
    AlarmEvent.CLEAR,
)


def feed(alarm, samples, start=0.0, dt=1.0):
    events = []
    t = start
    for s in samples:
        events.append(alarm.update(s, t))
        t += dt
    return events


def test_trips_once_after_hold():
    a = HoldAlarm(hold_seconds=5, renotify_seconds=0)
    events = feed(a, [True] * 20)
    assert events.count(TRIP) == 1
    assert events.index(TRIP) == 5  # t=5 is the first sample 5 s after t=0
    assert RENOTIFY not in events


def test_blip_shorter_than_hold_never_trips_or_clears():
    a = HoldAlarm(hold_seconds=5)
    events = feed(a, [True, True, True, False, False])
    assert events == [N] * 5


def test_clear_after_trip_is_one_event():
    a = HoldAlarm(hold_seconds=2)
    events = feed(a, [True, True, True, False, False, False])
    assert events.count(TRIP) == 1
    assert events.count(CLEAR) == 1


def test_renotify_zero_means_never():
    a = HoldAlarm(hold_seconds=3, renotify_seconds=0)
    events = feed(a, [True] * 31)  # 10x the hold
    assert [e for e in events if e is not N] == [TRIP]


def test_renotify_negative_or_none_means_never():
    for value in (-5, None):
        a = HoldAlarm(hold_seconds=1, renotify_seconds=value)
        assert [e for e in feed(a, [True] * 50) if e is not N] == [TRIP]


def test_renotify_interval():
    a = HoldAlarm(hold_seconds=10, renotify_seconds=60)
    events = feed(a, [True] * 200)
    assert events.count(TRIP) == 1
    trip_t = events.index(TRIP)
    renotify_ts = [i for i, e in enumerate(events) if e is RENOTIFY]
    assert renotify_ts == [trip_t + 60, trip_t + 120, trip_t + 180]


def test_none_neither_resets_nor_trips():
    a = HoldAlarm(hold_seconds=5)
    events = feed(a, [True, True, None, None, None, None, None, None])
    assert TRIP not in events
    assert a.active_since == 0.0  # not reset
    # The next valid active reading counts from the original start.
    assert a.update(True, 8.0) is TRIP


def test_none_while_tripped_does_not_clear():
    a = HoldAlarm(hold_seconds=1)
    feed(a, [True, True])
    assert a.tripped
    assert a.update(None, 5.0) is N
    assert a.tripped


def test_any_valid_inactive_reading_resets_timer():
    a = HoldAlarm(hold_seconds=5)
    events = feed(a, [True, True, True, True, False, True, True, True, True])
    assert TRIP not in events


def test_reset_is_silent():
    a = HoldAlarm(hold_seconds=1)
    feed(a, [True, True])
    assert a.reset() is True
    assert not a.tripped and a.active_since is None
    # nothing to clear afterwards
    assert a.update(False, 10.0) is N
    assert a.reset() is False


def test_zero_hold_trips_on_first_active_sample():
    a = HoldAlarm(hold_seconds=0)
    assert a.update(True, 0.0) is TRIP
