import logging
import time

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
        
        self.loop_target_period = 4
        

    async def setup(self):
        print("---- RUNNING SETUP ----")
        self.ui = DiMonitorUI(self.config)
        
        self.loop_target_period = 1
        self.last_triggered_time = None
        
        self.triggered_duration = self.get_tag("triggered_duration", default=0)
        self.triggered_count = self.get_tag("triggered_count", default=0)
        
        self.ui_manager.add_children(*self.ui.fetch())
        
        self.ui.update(
            # init Ui
            di_state=await self.get_input_state(),
            triggered_duration=seconds_to_hms(self.triggered_duration),
            triggered_count=self.triggered_count,
        )
        # self.ui_manager.sync_ui()
        
    async def on_triggered_pulse(self, di=None, val=None, dt_sec=None, counter=None, edge=None):
        log.info("Input Activated")
        self.last_triggered_time = time.monotonic()
        self.triggered_count += 1
        await self.set_tag("triggered_count", self.triggered_count)
        if self.config.send_triggered_alert.value:
            await self.publish_to_channel("significantEvent",self.config.get_alert_msg())
        self.ui.update(
            di_state=True,
            last_triggered_duration=seconds_to_hms(0)
        )
        self.ui.update_triggered_count(self.triggered_count)
        
    async def on_untriggered_pulse(self, di=None, val=None, dt_sec=None, counter=None, edge=None):
        log.info("Input Deactivated")
        await self.triggered_duration_complete()
        
        if self.config.send_untriggered_alert.value:
            await self.publish_to_channel("significantEvent",self.config.get_untriggered_msg())
            
        self.ui.update(
            di_state=False,
        )
        
    async def triggered_duration_complete(self):
        if self.last_triggered_time is not None:
            dt_sec = time.monotonic() - self.last_triggered_time
            self.triggered_duration += dt_sec
            await self.set_tag("triggered_duration", self.triggered_duration)
            self.ui.update(triggered_duration=seconds_to_hms(self.triggered_duration))
            self.last_triggered_time = None

    async def manually_untrigger(self):
        log.info(f"Manually untriggering DI {self.config.get_di_name()}")
        await self.on_untriggered_pulse()
        
    async def manually_trigger(self):
        log.info(f"Manually triggering DI {self.config.get_di_name()}")
        await self.on_triggered_pulse()
        
    async def get_input_state(self):
        if self.config.get_is_ai():
            di_val = await self.get_ai(self.config.get_di_channel())
            di_val = di_val > 8
        else:
            di_val = await self.get_di(self.config.get_di_channel())
        return di_val

    async def main_loop(self):
        di_val = await self.get_input_state()
        
        if di_val != self.config.get_triggered_bool():
            if self.last_triggered_time is not None:
                # manually untrigger event incase the pulse counter misses a pulse
                await self.manually_untrigger()
        else:
            if self.last_triggered_time is not None:
                delta_t = time.monotonic() - self.last_triggered_time
                self.ui.update(
                    last_triggered_duration=seconds_to_hms(delta_t),
                    triggered_duration=seconds_to_hms(self.triggered_duration+delta_t)
                    )
            else:
                # manually trigger event incase the pulse counter misses a pulse
                await self.manually_trigger()
                
