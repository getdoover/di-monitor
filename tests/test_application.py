"""The application end to end, faked only at fetch_di / tags / notifications / clock."""

from di_monitor.app_config import ALARM_MESSAGE_DEFAULT

HIGH, LOW = True, False


# --- Basic hold behaviour (DI0 compressor style: alarm when LOW) ---------


def test_held_low_longer_than_hold_trips_once(rig):
    r = rig(hold_seconds=30.0)
    r.set(0, LOW)
    # The first LOW sample starts the timer, so 30 s of hold is the 31st sample.
    r.run_for(30)
    assert r.sent == []
    assert r.tag("alarm_active") is False
    r.run_for(1)
    assert r.events() == ["alarm"]
    assert r.sent[0]["message"] == "Compressor active for longer than 30 s"
    assert r.tag("alarm_active") is True
    assert r.tag("trip_count") == 1
    assert r.tag("last_trip_at") == int(r.clock.now * 1000)
    r.run_for(300)
    assert r.events() == ["alarm"]


def test_low_blip_shorter_than_hold_sends_nothing(rig):
    r = rig(hold_seconds=30.0)
    r.set(0, LOW)
    r.run_for(10)
    assert r.tag("active_seconds") == 9  # first low sample starts the timer
    r.set(0, HIGH)
    r.run_for(60)
    assert r.sent == []
    assert r.tag("trip_count") == 0
    assert r.tag("active_seconds") == 0


def test_clear_after_trip_sends_exactly_one_cleared(rig):
    r = rig(hold_seconds=5.0)
    r.set(0, LOW)
    r.run_for(10)
    r.set(0, HIGH)
    r.run_for(10)
    assert r.events() == ["alarm", "cleared"]
    assert r.sent[1]["message"] == "Compressor back to normal"
    assert r.tag("alarm_active") is False
    assert r.tag("warning_hidden") is True


def test_notify_on_clear_false(rig):
    r = rig(hold_seconds=5.0, notify_on_clear=False)
    r.set(0, LOW)
    r.run_for(10)
    r.set(0, HIGH)
    r.run_for(5)
    assert r.events() == ["alarm"]


def test_renotify_zero_sends_one_notification_over_ten_holds(rig):
    r = rig(hold_seconds=10.0, renotify_seconds=0.0)
    r.set(0, LOW)
    r.run_for(110)
    assert r.events() == ["alarm"]


def test_renotify_every_sixty_seconds(rig):
    r = rig(hold_seconds=10.0, renotify_seconds=60.0)
    r.set(0, LOW)
    r.run_for(10)  # trips on the 10th second after the first low sample
    r.run_for(1)
    assert r.events() == ["alarm"]
    r.run_for(180)
    assert r.events() == ["alarm"] * 4
    assert r.tag("trip_count") == 1  # renotifies are not new trips


def test_alarm_when_high(rig):
    r = rig(alarm_when="high", hold_seconds=5.0)
    r.set(0, HIGH)
    r.run_for(6)
    assert r.events() == ["alarm"]


def test_notification_severity_and_topic(rig):
    r = rig(hold_seconds=1.0)
    r.set(0, LOW)
    r.run_for(3)
    r.set(0, HIGH)
    r.run_for(1)
    alarm, cleared = r.sent
    assert alarm["severity"].name == "Warn"
    assert cleared["severity"].name == "Info"
    assert str(alarm["topic"]).endswith("/di_monitor_1/alarm")


# --- Unknown reads -------------------------------------------------------


def test_none_read_mid_hold_neither_resets_nor_trips(rig):
    r = rig(hold_seconds=10.0)
    r.set(0, LOW)
    r.run_for(5)
    r.set(0, None)
    r.run_for(20)
    assert r.sent == []
    assert r.tag("di_read_ok") is False
    assert r.tag("status") == "Input unreadable"
    assert r.tag("alarm_active") is False
    assert r.tag("di_state") is LOW  # last valid reading kept
    # Timer was not reset: the next valid LOW reading is well past the hold.
    r.set(0, LOW)
    r.run_for(1)
    assert r.events() == ["alarm"]
    assert r.tag("di_read_ok") is True


def test_read_exception_is_treated_as_unknown(rig):
    r = rig(hold_seconds=5.0)
    r.set(0, RuntimeError("grpc down"))
    r.run_for(10)
    assert r.sent == []
    assert r.tag("di_read_ok") is False


def test_none_read_while_tripped_does_not_clear(rig):
    r = rig(hold_seconds=2.0)
    r.set(0, LOW)
    r.run_for(5)
    r.set(0, None)
    r.run_for(5)
    assert r.events() == ["alarm"]
    assert r.tag("alarm_active") is True


# --- Arming --------------------------------------------------------------


def test_not_armed_never_trips(rig):
    r = rig(hold_seconds=5.0, arm_di_pin=3, arm_di_level="high", levels={3: LOW})
    r.set(0, LOW)
    r.run_for(120)
    assert r.sent == []
    assert r.tag("armed") is False
    assert r.tag("alarm_active") is False
    assert r.tag("status") == "Not armed (DI3 not HIGH)"
    assert 3 in r.reads


def test_armed_trips_normally(rig):
    r = rig(hold_seconds=5.0, arm_di_pin=3, arm_di_level="high", levels={3: HIGH})
    r.set(0, LOW)
    r.run_for(6)
    assert r.events() == ["alarm"]
    assert r.tag("armed") is True


def test_arm_drops_mid_hold_resets_timer(rig):
    r = rig(hold_seconds=10.0, arm_di_pin=3, levels={3: HIGH})
    r.set(0, LOW)
    r.run_for(8)
    r.set(3, LOW)  # isolator off
    r.run_for(1)
    assert r.tag("active_seconds") == 0
    r.set(3, HIGH)
    r.run_for(9)  # would have tripped long ago without the reset
    assert r.sent == []
    r.run_for(2)
    assert r.events() == ["alarm"]


def test_disarm_clears_active_alarm_without_notifying(rig):
    r = rig(hold_seconds=2.0, arm_di_pin=3, levels={3: HIGH})
    r.set(0, LOW)
    r.run_for(5)
    assert r.tag("alarm_active") is True
    r.set(3, LOW)
    r.run_for(1)
    assert r.events() == ["alarm"]  # no "cleared"
    assert r.tag("alarm_active") is False
    assert r.tag("warning_hidden") is True
    # Re-arming with the input back to normal: still nothing to clear.
    r.set(0, HIGH)
    r.set(3, HIGH)
    r.run_for(5)
    assert r.events() == ["alarm"]


def test_arm_level_low(rig):
    r = rig(hold_seconds=2.0, arm_di_pin=2, arm_di_level="low", levels={2: LOW})
    r.set(0, LOW)
    r.run_for(3)
    assert r.events() == ["alarm"]


def test_unreadable_arm_input_skips_sample(rig):
    r = rig(hold_seconds=5.0, arm_di_pin=3, levels={3: HIGH})
    r.set(0, LOW)
    r.run_for(3)
    r.set(3, None)
    r.run_for(10)
    assert r.sent == []
    assert r.tag("di_read_ok") is False
    assert r.tag("armed") is True  # last known arm state kept


def test_no_arm_pin_never_reads_other_inputs(rig):
    r = rig(hold_seconds=5.0)
    r.run_for(3)
    assert set(r.reads) == {0}
    assert r.tag("arm_hidden") is True


# --- Notifications disabled (isolator install) ---------------------------


def test_notifications_disabled_sends_nothing_but_ui_warns(rig):
    r = rig(
        di_name="Isolator",
        di_pin=3,
        hold_seconds=5.0,
        notifications_enabled=False,
        alarm_message="Isolator is switched off",
        levels={3: HIGH},
    )
    r.set(3, LOW)
    r.run_for(10)
    assert r.sent == []
    assert r.tag("alarm_active") is True
    assert r.tag("warning_hidden") is False
    assert r.tag("warning_text") == "Isolator is switched off"
    assert r.tag("trip_count") == 1
    r.set(3, HIGH)
    r.run_for(2)
    assert r.sent == []
    assert r.tag("warning_hidden") is True


# --- Persistence and presentation ----------------------------------------


def test_trip_count_continues_from_persisted_value(rig):
    r = rig(hold_seconds=1.0, trip_count=7)
    r.set(0, LOW)
    r.run_for(3)
    assert r.tag("trip_count") == 8


def test_status_shows_active_and_hold(rig):
    r = rig(hold_seconds=30.0)
    assert r.tag("status") in (None, "Starting")
    r.run_for(1)
    assert r.tag("status") == "Normal"
    r.set(0, LOW)
    r.run_for(13)
    assert r.tag("status") == "Active 12 s / hold 30 s"
    r.run_for(20)
    assert r.tag("status").startswith("ALARM: active")


def test_bad_message_template_does_not_raise(rig):
    r = rig(hold_seconds=1.0, alarm_message="{di_name} {unknown} {0} {")
    r.set(0, LOW)
    r.run_for(3)
    assert r.events() == ["alarm"]


def test_default_messages():
    assert "{di_name}" in ALARM_MESSAGE_DEFAULT
