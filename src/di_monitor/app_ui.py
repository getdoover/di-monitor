from pathlib import Path

from pydoover import ui

from .app_tags import DiMonitorTags as T


class DiMonitorUI(ui.UI):
    # Shown whenever the alarm is active, whether or not notifications are
    # enabled: on an install with notifications off (e.g. the isolator
    # monitor) this is the only place the alarm appears.
    alarm_warning = ui.WarningIndicator(
        T.warning_text,
        name="alarm_warning",
        hidden=T.warning_hidden,
        can_cancel=False,
        position=1,
    )
    status = ui.TextVariable("Status", value=T.status, name="status", position=2)
    input_state = ui.BooleanVariable(
        "Input High", value=T.di_state, name="input_state", position=3
    )
    armed = ui.BooleanVariable(
        "Armed", value=T.armed, name="armed", hidden=T.arm_hidden, position=4
    )
    alarm_active = ui.BooleanVariable(
        "Alarm Active", value=T.alarm_active, name="alarm_active", position=5
    )
    active_seconds = ui.NumericVariable(
        "Active For",
        value=T.active_seconds,
        name="active_seconds",
        units="s",
        precision=0,
        position=6,
    )
    trip_count = ui.NumericVariable(
        "Trip Count", value=T.trip_count, name="trip_count", precision=0, position=7
    )
    last_trip_at = ui.Timestamp(
        "Last Trip", value=T.last_trip_at, name="last_trip_at", position=8
    )
    read_ok = ui.BooleanVariable(
        "Input Readable", value=T.di_read_ok, name="read_ok", position=9
    )

    async def setup(self):
        name = self.config.di_name.value
        pin = int(self.config.di_pin.value)
        self.input_state.display_name = f"{name} Input (DI{pin}) High"
        arm_pin = self.config.arm_di_pin.value
        if arm_pin is not None:
            level = str(self.config.arm_di_level.value).upper()
            self.armed.display_name = f"Armed (DI{int(arm_pin)} {level})"
        hold = float(self.config.hold_seconds.value)
        self.active_seconds.display_name = f"Active For (hold {hold:g} s)"


def export():
    DiMonitorUI(None, None, None).export(
        Path(__file__).parents[2] / "doover_config.json", "di_monitor"
    )


if __name__ == "__main__":
    export()
