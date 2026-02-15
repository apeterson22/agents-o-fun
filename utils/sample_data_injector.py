import threading
import time
import schedule
import logging
from agents.trading_agent import run_trading_agent
from agents.marketing_agent import run_marketing_agent

log = logging.getLogger(__name__)

class SampleDataInjector:
    def __init__(self):
        self.running = False
        self.thread = None
        self.scheduler_config = {
            "interval_minutes": 5,
            "enabled": True
        }

    def inject_once(self):
        log.info("Injecting one-time sample data.")
        run_trading_agent()
        run_marketing_agent()

    def _scheduler_loop(self):
        log.info("Starting background data injection scheduler...")
        schedule.every(self.scheduler_config["interval_minutes"]).minutes.do(self.inject_once)
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def start_scheduler(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()

    def stop_scheduler(self):
        self.running = False
        log.info("Stopped data injection scheduler.")

    def update_config(self, interval_minutes=None, enabled=None):
        if interval_minutes is not None:
            self.scheduler_config["interval_minutes"] = interval_minutes
        if enabled is not None:
            self.scheduler_config["enabled"] = enabled
        if self.scheduler_config["enabled"]:
            self.start_scheduler()
        else:
            self.stop_scheduler()

injector = SampleDataInjector()
