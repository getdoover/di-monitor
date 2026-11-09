from pathlib import Path

from pydoover import config
from pydoover.config import ApplicationPosition

LEVELS = ["low", "high"]

ALARM_MESSAGE_DEFAULT = "{di_name} active for longer than {hold_seconds} s"
CLEAR_MESSAGE_DEFAULT = "{di_name} back to normal"

PLACEHOLDER_HELP = (
    "Placeholders: {di_name}, {di_pin}, {hold_seconds}, {active_seconds}."
)


class DiMonitorConfig(config.Schema):
    di_name = config.String(
        "DI Name",
        description="What the input is, as shown in the UI and in notifications (e.g. Compressor).",
        name="di_name",
    )
    di_pin = config.Integer(
        "DI Pin",
        description="Doovit digital input to monitor (0-3).",
        minimum=0,
        maximum=3,
        name="di_pin",
    )
    alarm_when = config.Enum(
        "Alarm When",
        description="The input level that counts as active (alarming).",
        choices=LEVELS,
        default="low",
        name="alarm_when",
    )
    hold_seconds = config.Number(
        "Hold Seconds",
        description="How long the input must stay active, unbroken, before the alarm trips.",
        minimum=0,
        default=30.0,
        name="hold_seconds",
    )
    renotify_seconds = config.Number(
        "Renotify Seconds",
        description="While the alarm stays active, send it again this often. 0 = never re-notify.",
        minimum=0,
        default=0.0,
        name="renotify_seconds",
    )
    notify_on_clear = config.Boolean(
        "Notify On Clear",
        description="Send a 'cleared' notification when a tripped alarm returns to normal.",
        default=True,
        name="notify_on_clear",
    )
    notifications_enabled = config.Boolean(
        "Notifications Enabled",
        description=(
            "Send alarm / cleared notifications. When off, nothing is sent; "
            "the UI still shows the warning."
        ),
        default=True,
        name="notifications_enabled",
    )
    alarm_message = config.String(
        "Alarm Message",
        description="Message sent (and shown in the UI warning) when the alarm trips. "
        + PLACEHOLDER_HELP,
        default=ALARM_MESSAGE_DEFAULT,
        name="alarm_message",
    )
    clear_message = config.String(
        "Clear Message",
        description="Message sent when a tripped alarm clears. " + PLACEHOLDER_HELP,
        default=CLEAR_MESSAGE_DEFAULT,
        name="clear_message",
    )
    arm_di_pin = config.Integer(
        "Arm DI Pin",
        description=(
            "Optional. Only run the alarm while this digital input is at Arm DI "
            "Level (e.g. isolator power). Leave empty to always be armed. While "
            "not armed the hold timer resets and an active alarm clears without "
            "a notification."
        ),
        minimum=0,
        maximum=3,
        default=None,
        name="arm_di_pin",
    )
    arm_di_level = config.Enum(
        "Arm DI Level",
        description="The level of Arm DI Pin at which the alarm is armed.",
        choices=LEVELS,
        default="high",
        name="arm_di_level",
    )
    poll_period_seconds = config.Number(
        "Poll Period Seconds",
        description=(
            "How often the input (and the arm input, if set) is read. The hold "
            "timer runs on wall-clock time, so a longer period only delays "
            "detection by up to one period. Each read is a round trip to the "
            "Doovit MCU: raise this to cut I/O load."
        ),
        default=1.0,
        minimum=0.5,
        maximum=60,
        advanced=True,
        name="poll_period_seconds",
    )
    position = ApplicationPosition()


def export():
    DiMonitorConfig.export(
        Path(__file__).parents[2] / "doover_config.json", "di_monitor"
    )


if __name__ == "__main__":
    export()
