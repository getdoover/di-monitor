import logging
import time
import asyncio

from pydoover import ui

from pydoover.docker import Application
from .app_config import DiMonitorConfig
from .app_ui import DiMonitorUI
from .utils import seconds_to_hms

log = logging.getLogger()

class DiMonitorApplication(Application):
    config: DiMonitorConfig  # not necessary, but helps your IDE provide autocomplete!
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: DiMonitorUI = None
        
        self.loop_target_period = 5

    async def setup(self):
        self.ui = DiMonitorUI(self.config)
        
        self.triggered_count = self.get_tag("triggered_count", default=0)
        
        self.trigger_alarm = await self.platform_iface.recv_di_pulses(
            self.config.get_di_channel(),
            self.on_triggered_pulse,
            self.config.get_triggered_state(),
        )
        
        self.untrigger_alarm = await self.platform_iface.recv_di_pulses(
            self.config.get_di_channel(),
            self.on_untriggered_pulse,
            self.config.get_untriggered_state(),
        )
        
        self.ui_manager.add_children(*self.ui.fetch())
        print("setup complete")
        logging.info(f"DI {self.config.get_di_name()} is configured to monitor channel {self.config.get_di_channel()} in state {self.config.get_triggered_state()}")
        # self.ui_manager.sync_ui()
        
    def on_triggered_pulse(self, di, val, dt_sec, counter, edge):
        log.info(f"DI {di} triggered pulse: {val}, {dt_sec}, {counter}, {edge}")
        self.triggered_count += 1
        self.set_tag("triggered_count", self.triggered_count)
        self.publish_to_channel("significantEvent",self.config.get_alert_msg())
        self.ui.update(
            di_state=val,
            last_triggered_duration=seconds_to_hms(-1)
        )
        self.ui.update_triggered_count(self.triggered_count)
        
    def on_untriggered_pulse(self, di, val, dt_sec, counter, edge):
        log.info(f"DI {di} untriggered pulse: {val}, {dt_sec}, {counter}, {edge}")
        hms = seconds_to_hms(dt_sec)
        self.publish_to_channel("significantEvent",self.config.get_untriggered_msg())
        self.ui.update(
            di_state=val,
            last_triggered_duration=hms
        )

    async def main_loop(self):
        logging.info("Main loop running...")
        print("Main loop running...")
        asyncio.sleep(5)