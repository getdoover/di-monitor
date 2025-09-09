from pathlib import Path

from pydoover import config

from enum import Enum

class DiState(Enum):
    HIGH = "rising"
    LOW = "falling"
    AI_RISING = "ai_rising"
    AI_FALLING = "ai_falling"

class DiMonitorConfig(config.Schema):
    def __init__(self):
        self.di_name = config.String("DI Name")
        self.di_channel = config.Integer("DI Channel", minimum=0)
        self.di_state_enum = config.Enum("DI Triggered State", choices=DiState, default=DiState.HIGH)
        self.alert_msg = config.String("Alert Message")
        self.untriggered_msg = config.String("Alert Complete Message")
        self.show_triggered_count = config.Boolean("Show Triggered Count")
        
    def get_di_name(self):
        return self.di_name.value
    
    def get_alert_msg(self):
        return self.alert_msg.value
    
    def get_show_triggered_count(self):
        return self.show_triggered_count.value
    
    def get_untriggered_msg(self):
        return self.untriggered_msg.value
    
    def get_di_channel(self):
        return self.di_channel.value
    
    def get_triggered_state(self):
        return self.di_state_enum.value
    
    def get_untriggered_state(self):
        match self.di_state_enum.value:
            case DiState.HIGH.value:
                return DiState.LOW.value
            case DiState.LOW.value:
                return DiState.HIGH.value
            case DiState.AI_RISING.value:
                return DiState.AI_FALLING.value
            case DiState.AI_FALLING.value:
                return DiState.AI_RISING.value
    
    

def export():
    DiMonitorConfig().export(Path(__file__).parents[2] / "doover_config.json", "di_monitor")

if __name__ == "__main__":
    export()
