from pydoover import ui

from .app_config import DiMonitorConfig

class DiMonitorUI:
    def __init__(self, config: DiMonitorConfig):
        self.config = config
        
        self.di_state = ui.BooleanVariable("di_state", self.config.get_di_name())
        self.last_triggered_duration = ui.TextVariable("last_triggered_duration", "Last Triggered Duration")
        self.triggered_duration = ui.TextVariable("triggered_duration", "Triggered Duration")
        self.triggered_count = ui.NumericVariable("triggered_count", "Triggered Count")
        
    def fetch(self):
        result = [self.di_state, self.last_triggered_duration]
        
        if self.config.get_show_triggered_count():
            result.append(self.triggered_count)
            
        if self.config.show_triggered_duration.value:
            result.append(self.triggered_duration)
        
        return result

    def update(self, di_state=None, last_triggered_duration=None, triggered_duration=None, triggered_count=None):
        if di_state is not None: 
            self.di_state.update(di_state)
            
        if last_triggered_duration is not None:
            self.last_triggered_duration.update(last_triggered_duration)

        if triggered_duration is not None:
            self.triggered_duration.update(triggered_duration)
            
        if triggered_count is not None:
            self.triggered_count.update(triggered_count)

    def update_triggered_count(self, triggered_count):
        if self.config.get_show_triggered_count():
            self.triggered_count.update(triggered_count)