from pathlib import Path

from pydoover import config

from enum import Enum

class DiState(Enum):
    HIGH = "rising"
    LOW = "falling"
    AI_RISING = "VI+"
    AI_FALLING = "VI-"
    
class VoltageState(Enum):
    V12 = "12V"
    V24 = "24V"


class DiMonitorConfig(config.Schema):
    def __init__(self):
        self.di_name = config.String(
            "DI Name",
            description="The name of the Digital Input to monitor"
        )
        self.di_channel = config.Integer(
            "DI Channel",
            minimum=0,
            description="The channel of the Digital Input to monitor"
        )
        self.di_state_enum = config.Enum(
            "DI Triggered State",
            choices=DiState,
            default=DiState.HIGH,
            description=(
                "The state of the Digital Input to monitor, rising or falling "
                "for a digital input, or VI+ or VI- for an analog input"
            )
        )
        self.send_triggered_alert = config.Boolean(
            "Send Triggered Alert",
            default=True,
            description=(
                "Whether or not to send an alert when the Digital Input is "
                "triggered"
            )
        )
        self.send_untriggered_alert = config.Boolean(
            "Send Untriggered Alert",
            default=False,
            description=(
                "Whether or not to send an alert when the Digital Input is "
                "untriggered"
            )
        )
        self.alert_msg = config.String(
            "Alert Message",
            description="The message to send when the Digital Input is triggered"
        )
        self.untriggered_msg = config.String(
            "Alert Complete Message",
            description="The message to send when the Digital Input is untriggered"
        )
        self.voltage_state_enum = config.Enum(
            "Voltage State",
            choices=VoltageState,
            default=VoltageState.V24,
            description="The voltage state of the Digital Input"
        )
        self.show_triggered_count = config.Boolean(
            "Show Triggered Count",
            description="Whether or not to show the triggered count"
        )
        self.show_triggered_duration = config.Boolean(
            "Show Triggered Duration",
            default=True,
            description="Whether or not to show the triggered duration"
        )
        self.show_last_triggered_duration = config.Boolean(
            "Show Last Triggered Duration",
            default=True,
            description="Whether or not to show the last triggered duration"
        )
        self.position = config.Integer(
            "Position",
            description="The position of the application in the UI.",
            default=50,
        )
        
    def get_di_name(self):
        return self.di_name.value
    
    def get_alert_msg(self):
        return self.alert_msg.value
    
    def get_show_triggered_count(self):
        return self.show_triggered_count.value

    def get_show_last_triggered_duration(self):
        return self.show_last_triggered_duration.value
    
    def get_untriggered_msg(self):
        return self.untriggered_msg.value
    
    def get_di_channel(self):
        return self.di_channel.value
    
    def get_is_ai(self):
        return self.di_state_enum.value in [
            DiState.AI_RISING.value,
            DiState.AI_FALLING.value
        ]
    
    def get_triggered_bool(self):
        return self.di_state_enum.value in [
            DiState.AI_RISING.value,
            DiState.HIGH.value
        ]
    
    def get_triggered_state(self):
        match self.di_state_enum.value:
            case DiState.HIGH.value:
                return DiState.HIGH.value
            case DiState.LOW.value:
                return DiState.LOW.value
            case DiState.AI_RISING.value:
                if self.voltage_state_enum.value == VoltageState.V12.value:
                    return DiState.AI_RISING.value + "8"
                else:
                    return DiState.AI_RISING.value + "18"
            case DiState.AI_FALLING.value:
                if self.voltage_state_enum.value == VoltageState.V12.value:
                    return DiState.AI_FALLING.value + "8"
                else:
                    return DiState.AI_FALLING.value + "18"
        return self.di_state_enum.value
    
    def get_untriggered_state(self):
        match self.di_state_enum.value:
            case DiState.HIGH.value:
                return DiState.LOW.value
            case DiState.LOW.value:
                return DiState.HIGH.value
            case DiState.AI_RISING.value:
                if self.voltage_state_enum.value == VoltageState.V12.value:
                    return DiState.AI_FALLING.value + "8"
                else:
                    return DiState.AI_FALLING.value + "18"
            case DiState.AI_FALLING.value:
                if self.voltage_state_enum.value == VoltageState.V12.value:
                    return DiState.AI_RISING.value + "8"
                else:
                    return DiState.AI_RISING.value + "18"

    def get_position(self):
        return self.position.value


def export():
    DiMonitorConfig().export(
        Path(__file__).parents[2] / "doover_config.json",
        "di_monitor"
    )

if __name__ == "__main__":
    export()
