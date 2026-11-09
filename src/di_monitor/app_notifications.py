from pathlib import Path

from pydoover import notifications


class DiMonitorNotifications(notifications.Notifications):
    alarm = notifications.Notification(
        # Overridden on every send with the configured alarm message.
        "A monitored digital input has been active for longer than its hold time",
        display_name="Alarm",
        description=(
            "Sent when the input has stayed in its alarm state for the hold "
            "time, and again on each renotify interval if one is set."
        ),
        severity=notifications.NotificationSeverity.Warn,
    )
    cleared = notifications.Notification(
        "A monitored digital input is back to normal",
        display_name="Cleared",
        description="Sent when a tripped alarm returns to normal (if Notify On Clear is on).",
        severity=notifications.NotificationSeverity.Info,
    )


def export():
    DiMonitorNotifications.export(
        Path(__file__).parents[2] / "doover_config.json", "di_monitor"
    )
